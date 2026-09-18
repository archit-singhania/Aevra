from __future__ import annotations

import time
import uuid
from asyncio import to_thread
from collections import Counter, deque
from threading import Lock
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from aevra_api.config import get_settings


class RequestMetrics:
    def __init__(self) -> None:
        self.requests: Counter[str] = Counter()
        self.failures: Counter[str] = Counter()

    def record(self, method: str, path: str, status_code: int) -> None:
        key = f"{method} {path}"
        self.requests[key] += 1
        if status_code >= 500:
            self.failures[key] += 1


metrics = RequestMetrics()


class AuthRateLimiter:
    """Small in-process guard for login bursts.

    Redis remains the cross-instance production limiter; this protects a single
    API process and keeps local/staging deployments safe before Redis workers
    are enabled.
    """

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= now - window_seconds:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True


auth_rate_limiter = AuthRateLimiter()


class DistributedRateLimiter:
    """Redis-backed fixed-window limiter with a safe local fallback."""

    def __init__(self) -> None:
        self._clients: dict[str, Any] = {}
        self._lock = Lock()

    def _client(self, redis_url: str) -> Any:
        with self._lock:
            if redis_url not in self._clients:
                try:
                    from redis import Redis  # type: ignore[import-not-found]

                    self._clients[redis_url] = Redis.from_url(redis_url, decode_responses=True)
                except Exception:
                    self._clients[redis_url] = False
            return self._clients[redis_url]

    def _allow_sync(self, key: str, limit: int, window_seconds: int, redis_url: str) -> bool:
        client = self._client(redis_url)
        if client is not False:
            try:
                bucket = int(time.time() // window_seconds)
                redis_key = f"{key}:{bucket}"
                count = client.incr(redis_key)
                if count == 1:
                    client.expire(redis_key, window_seconds + 1)
                return count <= limit
            except Exception:
                pass
        return auth_rate_limiter.allowed(key, limit, window_seconds)

    async def allowed(self, key: str, limit: int, window_seconds: int, redis_url: str) -> bool:
        return await to_thread(self._allow_sync, key, limit, window_seconds, redis_url)


distributed_rate_limiter = DistributedRateLimiter()


def configured_origins(value: str) -> set[str]:
    return {origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()}


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        is_write = request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
        origin = request.headers.get("origin")
        allowed_origins = configured_origins(settings.allowed_origins)
        if is_write and origin and allowed_origins and origin.rstrip("/") not in allowed_origins:
            return Response(
                status_code=403,
                content='{"error":{"code":"invalid_origin","message":"Origin is not allowed."}}',
                media_type="application/json",
            )
        if settings.env.lower() in {"staging", "production"} and request.url.path in {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        }:
            client = request.client.host if request.client else "unknown"
            limiter_key = f"{settings.redis_rate_limit_prefix}:{client}:{request.url.path}"
            allowed = (
                await distributed_rate_limiter.allowed(
                    limiter_key,
                    settings.auth_rate_limit_attempts,
                    settings.auth_rate_limit_window_seconds,
                    settings.redis_url,
                )
                if settings.enable_redis_rate_limit
                else auth_rate_limiter.allowed(
                    limiter_key,
                    settings.auth_rate_limit_attempts,
                    settings.auth_rate_limit_window_seconds,
                )
            )
            if not allowed:
                return Response(
                    status_code=429,
                    content=(
                        '{"error":{"code":"rate_limited","message":"Too many '
                        'authentication attempts. Try again shortly."}}'
                    ),
                    media_type="application/json",
                    headers={"Retry-After": str(settings.auth_rate_limit_window_seconds)},
                )
        if (
            settings.env.lower() in {"staging", "production"}
            and is_write
            and request.url.path not in {"/api/v1/auth/login", "/api/v1/auth/register"}
        ):
            client = request.client.host if request.client else "unknown"
            limiter_key = f"{settings.redis_rate_limit_prefix}:api:{client}"
            allowed = (
                await distributed_rate_limiter.allowed(
                    limiter_key,
                    settings.api_rate_limit_attempts,
                    settings.api_rate_limit_window_seconds,
                    settings.redis_url,
                )
                if settings.enable_redis_rate_limit
                else auth_rate_limiter.allowed(
                    limiter_key,
                    settings.api_rate_limit_attempts,
                    settings.api_rate_limit_window_seconds,
                )
            )
            if not allowed:
                return Response(
                    status_code=429,
                    content=(
                        '{"error":{"code":"rate_limited","message":"Too many '
                        'API requests. Try again shortly."}}'
                    ),
                    media_type="application/json",
                    headers={"Retry-After": str(settings.api_rate_limit_window_seconds)},
                )
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        metrics.record(request.method, request.url.path, response.status_code)
        response.headers["X-Request-ID"] = request_id
        response.headers["Server-Timing"] = f"app;dur={(time.perf_counter() - started) * 1000:.2f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), payment=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"
        if request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
