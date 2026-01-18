from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from loguru import logger
import time
import uuid

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Add correlation ID to context
        with logger.contextualize(request_id=request_id):
            # Log Request
            logger.info(f"Incoming Request: {request.method} {request.url.path} (Client: {request.client.host})")
            
            try:
                response = await call_next(request)
                
                process_time = (time.time() - start_time) * 1000
                logger.info(
                    f"Completed: {response.status_code} | Took: {process_time:.2f}ms"
                )
                
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = str(process_time)
                
                return response
            except Exception as e:
                process_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Request Failed: {e} | Took: {process_time:.2f}ms"
                )
                raise e # Let FastAPI exception handlers deal with it, but we logged it.
