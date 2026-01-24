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
except singleton.SingleInstanceException:
    logger.warning("SingleInstanceException raised! A stale lock file might exist. Continuing cautiously...")

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

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/health")
async def health_check():
    return {"status": "ok", "msg": "Servis aktif ve çalışıyor."}






# Retail Middleware
from app.middleware.tenant import TenantMiddleware
app.add_middleware(TenantMiddleware)

if __name__ == "__main__":
    import uvicorn
    import os
    
    ssl_config = {}
    
    # Resolve paths relative to main.py if not absolute
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    cert_file = settings.SSL_CERT_FILE
    key_file = settings.SSL_KEY_FILE
    
    # If paths are just filenames, prepend base_dir/Certifica/
    if cert_file and not os.path.isabs(cert_file):
         cert_file = os.path.join(base_dir, "Certifica", os.path.basename(cert_file))
    if key_file and not os.path.isabs(key_file):
         key_file = os.path.join(base_dir, "Certifica", os.path.basename(key_file))

    if settings.USE_HTTPS and cert_file and key_file:
        if os.path.exists(cert_file) and os.path.exists(key_file):
             ssl_config = {
                 "ssl_keyfile": key_file,
                 "ssl_certfile": cert_file
             }
             logger.info(f"SSL Enabled. Cert: {cert_file}")
        else:
             logger.warning(f"SSL Files not found: {cert_file}, {key_file}. Falling back to HTTP.")
    elif settings.USE_HTTPS:
         logger.warning("HTTPS enabled but certificate paths not configured. Falling back to HTTP.")

    protocol = "https" if ssl_config else "http"
    logger.info(f"Starting server on {protocol}://0.0.0.0:{settings.API_PORT}")
    uvicorn.run("main:app", host="0.0.0.0", port=settings.API_PORT, reload=False, **ssl_config)
