from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from retail.core.context import set_tenant_id
from retail.core.config import settings

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant ID from header
        tenant_id = request.headers.get("X-Tenant-ID", settings.DEFAULT_TENANT_ID)
        
        # Set tenant ID in context
        token = set_tenant_id(tenant_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # ContextVar is automatically reset in its own context, 
            # but if we used a thread-local we'd need cleanup.
            # With ContextVar it's safe.
            pass
