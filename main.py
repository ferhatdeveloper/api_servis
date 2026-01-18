from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
from app.api.v1.api import api_router

from app.core.logging import configure_logging
from app.core.middleware import LoggingMiddleware

from contextlib import asynccontextmanager
from app.core.config import settings
from app.services.scheduler_service import scheduler_service

# Configure Loguru
# Configure Loguru
configure_logging()

# GLOBAL LOCK: Prevent multiple instances (User vs Service or User A vs User B)
try:
    from tendo import singleton
    me = singleton.SingleInstance() # Will sys.exit(-1) if another instance is running
except Exception as e:
    logger.warning(f"Could not acquire singleton lock: {e}")
except SystemExit:
    logger.error("Another instance is already running! Exiting.")
    sys.exit(-1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up EXFIN API...")
    scheduler_service.start()
    yield
    # Shutdown
    logger.info("Shutting down EXFIN API...")
    scheduler_service.shutdown()

app = FastAPI(
    title="EXFIN OPS API",
    description="Integrated API for Operations Management & Logo ERP Integration",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "app": "EXFIN OPS API",
        "version": "2.1.0",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    
    ssl_config = {}
    if settings.SSL_CERT_FILE and settings.SSL_KEY_FILE:
        import os
        if os.path.exists(settings.SSL_CERT_FILE) and os.path.exists(settings.SSL_KEY_FILE):
             ssl_config = {
                 "ssl_keyfile": settings.SSL_KEY_FILE,
                 "ssl_certfile": settings.SSL_CERT_FILE
             }
             logger.info(f"SSL Enabled. Cert: {settings.SSL_CERT_FILE}")

    uvicorn.run("main:app", host="0.0.0.0", port=settings.API_PORT, reload=False, **ssl_config)
