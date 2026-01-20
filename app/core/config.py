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

    def load_db_config(self):
        db_path = os.path.join(os.getcwd(), "exfin.db")
        if os.path.exists(db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                
                # 1. Global Settings
                rows = c.execute("SELECT key, value FROM settings").fetchall()
                s_dict = {r[0]: r[1] for r in rows}
                
                if s_dict:
                    self.DEFAULT_DB = s_dict.get("Default", self.DEFAULT_DB)
                    self.DEVELOPER_MODE = s_dict.get("DeveloperMode", "True").lower() == "true"
                    self.USE_HTTPS = s_dict.get("UseHTTPS", "False").lower() == "true"
                    self.API_PORT = int(s_dict.get("Api_Port", self.API_PORT))
                    self.STREAMLIT_PORT = int(s_dict.get("Streamlit_Port", self.STREAMLIT_PORT))
                    self.DEBUG = self.DEVELOPER_MODE

                # 2. Database Connections (for legacy compat)
                conn.row_factory = sqlite3.Row
                c_rows = conn.execute("SELECT * FROM api_connections").fetchall()
                self.DB_CONFIGS = [dict(r) for r in c_rows]
                
                conn.close()
                return True
            except Exception as e:
                print(f"Error loading exfin.db config: {e}")
        
        # Fallback to JSON if DB setup failed
        config_path = os.path.join(os.getcwd(), "db_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        globals = data[0]
                        self.DEFAULT_DB = globals.get("Default", self.DEFAULT_DB)
                        self.DEVELOPER_MODE = globals.get("DeveloperMode", self.DEVELOPER_MODE)
                        self.USE_HTTPS = globals.get("UseHTTPS", self.USE_HTTPS)
                        self.API_PORT = int(globals.get("Api_Port", self.API_PORT))
                        self.DEBUG = self.DEVELOPER_MODE
                        self.DB_CONFIGS = data[1:]
                return True
            except: pass
        return False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
settings.load_db_config()
