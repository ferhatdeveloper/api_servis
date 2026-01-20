from contextvars import ContextVar
from typing import Optional

tenant_id_context: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)

def set_tenant_id(tenant_id: str):
    tenant_id_context.set(tenant_id)

def get_current_tenant_id() -> Optional[str]:
    return tenant_id_context.get()
