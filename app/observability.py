from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"
ACCESS_LOGGER_NAME = "cloud_infra_lab.access"


def new_request_id() -> str:
    return uuid.uuid4().hex


def build_access_log(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> dict[str, object]:
    return {
        "event": "http_request",
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 4),
    }


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self.logger = logger or logging.getLogger(ACCESS_LOGGER_NAME)

    async def dispatch(self, request: Request, call_next: Callable[[Request], object]) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            log_event = build_access_log(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            self.logger.info(json.dumps(log_event, sort_keys=True))
            if "response" in locals():
                response.headers[REQUEST_ID_HEADER] = request_id
