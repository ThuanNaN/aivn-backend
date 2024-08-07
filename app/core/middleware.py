import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.utils.logger import Logger
logger = Logger("core/middleware", log_file="middleware.log", stream_handler=False)

class LogProcessAndTime(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"{request.client.host}:{request.client.port} - \"{request.method} {request.url.path} HTTP/{request.scope['http_version']}\" {response.status_code} {process_time*100:.2f} ms")
        return response