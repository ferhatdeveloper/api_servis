import json
import os
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any

class Settings(BaseSettings):
    APP_NAME: str = "EXFIN OPS API"
    VERSION: str = "2.1.0"
    DEBUG: bool = True
    
    # Global Settings from JSON
    DEVELOPER_MODE: bool = True
    USE_HTTPS: bool = False
    API_PORT: int = 8000
    DEFAULT_DB: str = "PostgreSQLDatabase"
    
    # Database Configurations (Legacy JSON support)
    DB_CONFIGS: List[Dict[str, Any]] = []

    # PostgreSQL Env Params
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "EXFINOPS"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "admin"
    ALGORITHM: str = "HS256"
    
    # SSL Settings
    SSL_CERT_FILE: Optional[str] = None
    SSL_KEY_FILE: Optional[str] = None

    # Logo Env Params
    LOGO_DB_HOST: Optional[str] = None
    LOGO_DB_NAME: str = "LOGO"
    LOGO_DB_USER: Optional[str] = None
    LOGO_DB_PASSWORD: Optional[str] = None
    
    # Logo App Credentials (for Unity Objects)
    LOGO_APP_USER: str = "LOGO"
    LOGO_APP_PASS: str = "LOGO"

    # Third Party
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    
    # Evolution API Settings
    WHATSAPP_PROVIDER: str = "Evolution" # Evolution, Twilio, Meta
    EVOLUTION_API_URL: Optional[str] = "http://localhost:8080"
    EVOLUTION_API_TOKEN: Optional[str] = None
    EVOLUTION_API_INSTANCE: str = "Main"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []

    # Streamlit Integration
    STREAMLIT_PORT: int = 8501

    # API Settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "SUPER_SECRET_KEY_CHANGE_ME"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Fallback / Default Schema context
    LOGO_FIRMA_NO: str = "001"
    LOGO_PERIOD_NO: str = "01"
    LOGO_INTEGRATION_MODE: str = "DirectDB"

    # --- RetailOS Settings ---
    API_TITLE: str = "ExRetailOS API"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_TYPE: str = "postgresql"
    CENTRAL_DATABASE_URL: str = ""
    DEFAULT_TENANT_ID: str = "default"
    
    # JWT
    JWT_SECRET: str = "change-this-in-production-min-32-characters"
    
    # Uploads
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,xlsx,xls,csv"
    
    # Integrations
    OPENAI_API_KEY: str = ""
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER: str = ""
    NEBIM_API_URL: str = ""
    NEBIM_API_KEY: str = ""
    
    # Payments
    ZAIN_CASH_MERCHANT_ID: str = ""
    ZAIN_CASH_SECRET_KEY: str = ""
    FASTPAY_API_KEY: str = ""
    QICARD_MERCHANT_ID: str = ""
    
    # Cargo
    ARAMEX_IRAQ_API_KEY: str = ""
    DHL_IRAQ_API_KEY: str = ""
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@exretailos.com"

    # Push Notifications (OneSignal)
    ONESIGNAL_APP_ID: str = ""
    ONESIGNAL_API_KEY: str = ""

    def load_db_config(self):
        db_path = os.path.join(os.getcwd(), "api.db")
        
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                
                # 1. Global Settings
                try:
                    rows = c.execute("SELECT key, value FROM settings").fetchall()
                    s_dict = {r[0]: r[1] for r in rows}
                    
                    if s_dict:
                        self.DEFAULT_DB = s_dict.get("Default", self.DEFAULT_DB)
                        self.DEVELOPER_MODE = s_dict.get("DeveloperMode", str(self.DEVELOPER_MODE)).lower() == "true"
                        self.USE_HTTPS = s_dict.get("UseHTTPS", str(self.USE_HTTPS)).lower() == "true"
                        self.API_PORT = int(s_dict.get("Api_Port", self.API_PORT))
                        self.STREAMLIT_PORT = int(s_dict.get("Streamlit_Port", self.STREAMLIT_PORT))
                        
                        # Load other settings if present in DB
                        if "API_TITLE" in s_dict: self.API_TITLE = s_dict["API_TITLE"]
                        if "SECRET_KEY" in s_dict: self.SECRET_KEY = s_dict["SECRET_KEY"]
                        # Add more mappings as needed from settings table
                        
                        self.DEBUG = self.DEVELOPER_MODE
                except: pass

                # 2. Database Connections
                conn.row_factory = sqlite3.Row
                try:
                    c_rows = conn.execute("SELECT * FROM db_connections").fetchall()
                    # Convert rows to dicts, mapping columns back to what app expects if needed
                    # App expects: Name, Type, Server, Port, Database, Username, Password
                    self.DB_CONFIGS = []
                    for r in c_rows:
                        self.DB_CONFIGS.append({
                            "Name": r["name"],
                            "Type": r["type"],
                            "Server": r["host"],
                            "Port": r["port"],
                            "Database": r["database"],
                            "Username": r["username"],
                            "Password": r["password"]
                        })
                except: pass
                
                conn.close()
            except Exception as e:
                print(f"Error loading api.db config: {e}")

        # --- Generate CENTRAL_DATABASE_URL ---
        if not self.CENTRAL_DATABASE_URL and self.DB_CONFIGS:
            # Try to find 'Main DB' or use the first one
            target_db = next((c for c in self.DB_CONFIGS if c.get("Name") == "Main DB"), None)
            if not target_db and len(self.DB_CONFIGS) > 0:
                target_db = self.DB_CONFIGS[0]
            
            if target_db:
                user = target_db.get("Username", "postgres")
                password = target_db.get("Password") or self.DB_PASSWORD
                server = target_db.get("Server", "localhost")
                database = target_db.get("Database") or self.DB_NAME
                port = target_db.get("Port", 5432)
                type_ = target_db.get("Type", "PostgreSQL").lower()
                
                if "postgres" in type_:
                    self.CENTRAL_DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{database}"
                elif "mssql" in type_:
                    self.CENTRAL_DATABASE_URL = f"mssql+aioodbc://{user}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

        # Fallback if still empty
        if not self.CENTRAL_DATABASE_URL:
             self.CENTRAL_DATABASE_URL = f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        return True

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
settings.load_db_config()
