from __future__ import annotations

import time
import uuid
from collections import Counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


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


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        metrics.record(request.method, request.url.path, response.status_code)
        response.headers["X-Request-ID"] = request_id
        response.headers["Server-Timing"] = f"app;dur={(time.perf_counter() - started) * 1000:.2f}"
        return response
