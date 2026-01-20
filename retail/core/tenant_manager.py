from typing import Dict, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
from .config import settings
import json

class TenantManager:
    def __init__(self):
        self._engines: Dict[str, AsyncEngine] = {}
        # Central engine for fetching tenant info
        self.central_engine = create_async_engine(
            settings.CENTRAL_DATABASE_URL,
            pool_pre_ping=True
        )

    async def get_tenant_config(self, tenant_id: str) -> Optional[dict]:
        """Fetch tenant database configuration from central DB"""
        async with self.central_engine.connect() as conn:
            query = text("SELECT connection_type, connection_config FROM public.firmalar WHERE firma_id = :tid")
            result = await conn.execute(query, {"tid": tenant_id})
            row = result.fetchone()
            if row:
                return {
                    "type": row[0],
                    "config": row[1] if isinstance(row[1], dict) else json.loads(row[1])
                }
        return None

    def _build_url(self, config_data: dict) -> str:
        """Build SQLAlchemy connection URL from config dict"""
        db_type = config_data["type"].lower()
        cfg = config_data["config"]
        
        if db_type == "postgresql":
            # postgresql+asyncpg://user:pass@host:port/dbname
            user = cfg.get("username", cfg.get("user", "postgres"))
            password = cfg.get("password", "")
            host = cfg.get("server", cfg.get("host", "localhost"))
            port = cfg.get("port", 5432)
            database = cfg.get("database", "")
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        
        elif db_type == "mssql":
            # mssql+aioodbc://user:pass@host:port/dbname?driver=ODBC+Driver+17+for+SQL+Server
            user = cfg.get("username", cfg.get("user", "sa"))
            password = cfg.get("password", "")
            server = cfg.get("server", cfg.get("host", "."))
            database = cfg.get("database", "")
            # Note: For MSSQL async, we usually use aioodbc or similar. 
            # The current environment has sqlalchemy, but we need to ensure drivers are there.
            # Using a generic DSN-less connection string format for aioodbc if possible.
            return f"mssql+aioodbc://{user}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
            
        return ""

    async def get_engine(self, tenant_id: str) -> AsyncEngine:
        """Get or create a cached engine for a specific tenant"""
        if tenant_id in self._engines:
            return self._engines[tenant_id]

        config_data = await self.get_tenant_config(tenant_id)
        if not config_data:
            raise ValueError(f"Tenant {tenant_id} not found in central database")

        url = self._build_url(config_data)
        if not url:
            raise ValueError(f"Could not build connection URL for tenant {tenant_id}")

        engine = create_async_engine(
            url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        self._engines[tenant_id] = engine
        return engine

# Global tenant manager instance
tenant_manager = TenantManager()
