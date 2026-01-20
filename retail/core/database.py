"""
RetailOS - Database Connection (Multi-Dialect Support)
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from .config import settings
from .tenant_manager import tenant_manager
from .context import get_current_tenant_id

# Default engine (Central DB)
engine = create_async_engine(
    settings.CENTRAL_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

# Base class for models
Base = declarative_base()

# Dependency
async def get_db():
    """Tenant-aware database session dependency"""
    tenant_id = get_current_tenant_id() or settings.DEFAULT_TENANT_ID
    try:
        tenant_engine = await tenant_manager.get_engine(tenant_id)
        async_session = async_sessionmaker(
            tenant_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()
    except Exception as e:
        print(f"Error getting DB for tenant {tenant_id}: {e}")
        raise
