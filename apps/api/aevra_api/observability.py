from __future__ import annotations

import time
import uuid
from collections import Counter, deque
from threading import Lock

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


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        if settings.env.lower() in {"staging", "production"} and request.url.path in {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        }:
            client = request.client.host if request.client else "unknown"
            if not auth_rate_limiter.allowed(
                f"{client}:{request.url.path}",
                settings.auth_rate_limit_attempts,
                settings.auth_rate_limit_window_seconds,
            ):
                return Response(
                    status_code=429,
                    content=(
                        '{"error":{"code":"rate_limited","message":"Too many '
                        'authentication attempts. Try again shortly."}}'
                    ),
                    media_type="application/json",
                    headers={"Retry-After": str(settings.auth_rate_limit_window_seconds)},
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
        if request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
