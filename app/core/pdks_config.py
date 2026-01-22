"""
PDKS Configuration Shim
Adapts main application 'settings' to the 'config_manager' interface expected by PDKS code.
"""
from typing import Dict, Any, List
from pydantic import BaseModel
from app.core.config import settings

class AppConfigProxy:
    """Proxies access to main settings"""
    @property
    def Default(self):
        return settings.DEFAULT_DB
        
    @property
    def DeveloperMode(self):
        return settings.DEVELOPER_MODE
        
    @property
    def RealtimeEnabled(self):
        # Assuming True if not defined in main settings, or add to main settings later
        return getattr(settings, "REALTIME_ENABLED", True)
        
    @property
    def Api_Port(self):
        return str(settings.API_PORT)
        
    def get_api_port(self) -> int:
        return settings.API_PORT

class DatabaseConfig(BaseModel):
    Name: str
    Type: str
    Server: str = None
    Database: str
    Username: str = None
    Password: str = None
    Port: int = None

class ConfigManagerProxy:
    """Proxies ConfigManager methods to DatabaseManager/Settings"""
    
    def __init__(self):
        self.app_config = AppConfigProxy()
        # Helper to construct database list from settings.DB_CONFIGS
        self._databases = {}
        for db in settings.DB_CONFIGS:
             name = db.get("Name")
             if name:
                 self._databases[name] = DatabaseConfig(**db)

    @property
    def databases(self):
        # Dynamic property to get latest from settings if they change
        dbs = {}
        for db in settings.DB_CONFIGS:
             name = db.get("Name")
             if name:
                 dbs[name] = DatabaseConfig(**db)
        return dbs

    def get_database_config(self, name: str = None):
        if name is None:
            name = self.app_config.Default
        
        # Check settings.DB_CONFIGS
        for db in settings.DB_CONFIGS:
            if db.get("Name") == name:
                return DatabaseConfig(**db)
        
        # Fallbacks for env var defined DBs
        if name == "PostgreSQLDatabase":
            return DatabaseConfig(
                Name="PostgreSQLDatabase",
                Type="PostgreSQL",
                Server=settings.DB_HOST,
                Port=settings.DB_PORT,
                Database=settings.DB_NAME,
                Username=settings.DB_USER,
                Password=settings.DB_PASSWORD
            )
        elif name == "LOGO_Database":
             return DatabaseConfig(
                Name="LOGO_Database",
                Type="MSSQL",
                Server=settings.LOGO_DB_HOST or ".",
                Database=settings.LOGO_DB_NAME,
                Username=settings.LOGO_DB_USER or "sa",
                Password=settings.LOGO_DB_PASSWORD or ""
            )
            
        raise ValueError(f"Database config not found: {name}")
        
    def get_connection_string(self, name: str = None) -> str:
        cfg = self.get_database_config(name)
        if cfg.Type == "MSSQL":
            port_str = f":{cfg.Port}" if cfg.Port else ""
            return f"mssql+pymssql://{cfg.Username}:{cfg.Password}@{cfg.Server}{port_str}/{cfg.Database}"
        elif cfg.Type == "PostgreSQL":
            port = cfg.Port or 5432
            return f"postgresql://{cfg.Username}:{cfg.Password}@{cfg.Server}:{port}/{cfg.Database}"
        elif cfg.Type == "MySQL":
            port = f":{cfg.Port}" if cfg.Port else ":3306"
            return f"mysql+pymysql://{cfg.Username}:{cfg.Password}@{cfg.Server}{port}/{cfg.Database}"
        return ""

config_manager = ConfigManagerProxy()
