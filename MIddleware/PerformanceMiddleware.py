import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from Utils.LogUtil import log


class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        log.info(f"[{request.method}] {request.url.path} - 耗时: {process_time:.4f}s")
        return response
