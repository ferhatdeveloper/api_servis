"""
RetailOS v1.0.0 - FastAPI Backend
Ana uygulama dosyası
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import uvicorn
import os

from retail.core.config import settings
from retail.core.database import engine, Base
from retail.api.v1 import api_router
from retail.middleware.tenant import TenantMiddleware

# Veritabanı tabloları oluştur
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Başlangıçta
    print(f"🚀 {settings.API_TITLE} starting on {settings.ENVIRONMENT} mode...")
    
    # Sadece development/staging ortamında tablo oluşturmayı otomatiğe bağla
    if settings.ENVIRONMENT != "production":
        async with engine.begin() as conn:
            # Note: Production'da alembic kullanılması önerilir.
            # await conn.run_sync(Base.metadata.create_all) 
            pass
    
    print("✅ Database initialization checked")
    yield
    # Kapatılırken
    print(f"👋 {settings.API_TITLE} shutting down...")

# FastAPI uygulaması
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Middleware ayarlarÄ±
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-tenant Middleware
app.add_middleware(TenantMiddleware)

# API router'ı ekle
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")

# Health check endpoint (Generic)
@app.get("/health")
async def health_check():
    """
    Health check endpoint - Veritabanı bağlantısını test eder
    """
    try:
        # Veritabanı bağlantısını test et
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "version": settings.API_VERSION,
            "database": {
                "status": "connected",
                "type": settings.DATABASE_TYPE,
                "message": f"{settings.DATABASE_TYPE.upper()} connection successful"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": settings.API_VERSION,
                "database": {
                    "status": "error",
                    "type": settings.DATABASE_TYPE,
                    "message": f"Database connection failed: {str(e)}"
                }
            }
        )

# Root endpoint
@app.get("/")
async def root():
    return {
        "app": settings.API_TITLE,
        "version": settings.API_VERSION,
        "docs": "/api/docs",
        "health": "/health",
        "environment": settings.ENVIRONMENT
    }

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    # Log the exception here
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
