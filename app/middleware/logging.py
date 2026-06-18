import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("devmind.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Attaches a unique X-Request-ID to every request/response.
    Logs method, path, status code, and processing time.
    In Phase 2, this request_id will be threaded through agent traces.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                },
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"

        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({elapsed_ms:.1f}ms) "
            f"[{request_id[:8]}]"
        )
        return response
