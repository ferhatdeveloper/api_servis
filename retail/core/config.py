"""
RetailOS - Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import json

class Settings(BaseSettings):
    """Uygulama ayarlarÄ±"""
    
    # API AyarlarÄ±
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_VERSION: str = "v1"
    API_TITLE: str = "ExRetailOS API"
    API_DESCRIPTION: str = "Professional Retail Management System for Iraq Market"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # Veritabanı
    DATABASE_TYPE: str = "postgresql"  # postgresql, mssql
    DATABASE_URL: str = ""
    MSSQL_URL: str = ""
    
    # Merkezi Veritabanı (Tenant Yönetimi için)
    CENTRAL_DATABASE_URL: str = ""
    DEFAULT_TENANT_ID: str = "default"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.CENTRAL_DATABASE_URL = self._load_central_db_url()

    def _load_central_db_url(self) -> str:
        """db_config.json dosyasından varsayılan (Merkez) DB URL'ini yükler"""
        try:
            # backend/db_config.json
            json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db_config.json")
            if not os.path.exists(json_path):
                # Root/db_config.json (alternative)
                json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "db_config.json")

            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    default_info = next((item for item in data if "Default" in item), None)
                    if default_info:
                        default_name = default_info["Default"]
                        db_info = next((item for item in data if item.get("Name") == default_name), None)
                        if db_info:
                            dtype = db_info.get("Type", "PostgreSQL").lower()
                            user = db_info.get("Username", "postgres")
                            password = db_info.get("Password", "")
                            server = db_info.get("Server", "localhost")
                            database = db_info.get("Database", "")
                            port = db_info.get("Port", 5432)
                            
                            if dtype == "postgresql":
                                return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{database}"
                            elif dtype == "mssql":
                                return f"mssql+aioodbc://{user}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        except Exception as e:
            print(f"Error loading db_config.json: {e}")
        
        # Fallback
        return "postgresql+asyncpg://postgres:Yq7xwQpt6c@localhost:5432/EXFIN_MERKEZ"
    
    # Windows Service Ayarları
    SERVICE_NAME: str = "X_Retailos"
    SERVICE_DISPLAY_NAME: str = "RetailOS Backend Service"
    SERVICE_DESCRIPTION: str = "FastAPI Multi-Tenant Backend Service"
    
    # JWT
    JWT_SECRET: str = "change-this-in-production-min-32-characters"
    SECRET_KEY: str = "change-this-in-production-min-32-characters"  # Legacy support
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 saat
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://exretailos.vercel.app",
    ]
    
    # Sayfalama
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # Dosya Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,xlsx,xls,csv"
    
    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = False
    CACHE_ENABLED: bool = False
    
    # Performance
    WORKERS: int = 4
    MAX_CONNECTIONS: int = 100
    REQUEST_TIMEOUT: int = 30
    
    # External Integrations
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER: str = ""
    
    LOGO_API_URL: str = ""
    LOGO_API_USERNAME: str = ""
    LOGO_API_PASSWORD: str = ""
    LOGO_COMPANY_CODE: str = ""
    
    NEBIM_API_URL: str = ""
    NEBIM_API_KEY: str = ""
    
    # Iraq Payment Gateways
    ZAIN_CASH_MERCHANT_ID: str = ""
    ZAIN_CASH_SECRET_KEY: str = ""
    FASTPAY_API_KEY: str = ""
    QICARD_MERCHANT_ID: str = ""
    
    # Cargo
    ARAMEX_IRAQ_API_KEY: str = ""
    DHL_IRAQ_API_KEY: str = ""
    
    # E-posta (optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_USERNAME: str = ""  # Alias
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@exretailos.com"
    
    # Monitoring
    SENTRY_DSN: str = ""
    LOG_FILE_PATH: str = "/var/log/exretailos/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# Global settings instance
settings = Settings()
