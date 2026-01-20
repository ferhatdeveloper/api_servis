from fastapi import Header, HTTPException, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from retail.core.database import get_db
from retail.core.config import settings

async def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> str:
    """Extract tenant_id from X-Tenant-ID header"""
    if not x_tenant_id:
        # Fallback to default or raise error if multi-tenancy is strict
        # return settings.DEFAULT_TENANT_ID
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is missing")
    return x_tenant_id

async def get_tenant_db(
    tenant_id: str = Depends(get_tenant_id)
) -> AsyncSession:
    """Get database session for the current tenant"""
    async for session in get_db(tenant_id):
        yield session
