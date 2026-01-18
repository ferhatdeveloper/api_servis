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
configure_logging()

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
    uvicorn.run("main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
