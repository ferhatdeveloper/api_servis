"""
Role-Based Access Control (RBAC) Middleware
Enforce permissions on API endpoints

@created: 2024-12-18
"""

from fastapi import Request, HTTPException, status, Depends
from functools import wraps
from typing import List, Optional, Callable
from retail.core.jwt import TokenManager


# Permission definitions
PERMISSIONS = {
    # Sales permissions
    "sales.view": "View sales",
    "sales.create": "Create sales",
    "sales.update": "Update sales",
    "sales.delete": "Delete sales",
    "sales.discount": "Apply discounts",
    "sales.void": "Void sales",
    
    # Product permissions
    "products.view": "View products",
    "products.create": "Create products",
    "products.update": "Update products",
    "products.delete": "Delete products",
    "products.price": "Manage prices",
    
    # Customer permissions
    "customers.view": "View customers",
    "customers.create": "Create customers",
    "customers.update": "Update customers",
    "customers.delete": "Delete customers",
    
    # Inventory permissions
    "inventory.view": "View inventory",
    "inventory.adjust": "Adjust inventory",
    "inventory.transfer": "Transfer inventory",
    
    # Financial permissions
    "finance.view": "View financial data",
    "finance.reports": "View financial reports",
    "finance.accounting": "Access accounting",
    "finance.approve": "Approve transactions",
    
    # User management
    "users.view": "View users",
    "users.create": "Create users",
    "users.update": "Update users",
    "users.delete": "Delete users",
    "users.roles": "Manage roles",
    
    # Settings
    "settings.view": "View settings",
    "settings.update": "Update settings",
    "settings.system": "System settings",
    
    # Reports
    "reports.view": "View reports",
    "reports.export": "Export reports",
    "reports.advanced": "Advanced reports",
}


# Role hierarchy
ROLE_HIERARCHY = {
    "super_admin": 100,
    "admin": 80,
    "manager": 60,
    "accountant": 50,
    "cashier": 30,
    "staff": 20,
    "viewer": 10
}


# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    "super_admin": list(PERMISSIONS.keys()),  # All permissions
    
    "admin": [
        "sales.*", "products.*", "customers.*", "inventory.*",
        "users.view", "users.create", "users.update",
        "finance.view", "finance.reports", "finance.accounting",
        "reports.*", "settings.view", "settings.update"
    ],
    
    "manager": [
        "sales.*", "products.view", "products.update", "products.price",
        "customers.*", "inventory.*",
        "finance.view", "finance.reports",
        "reports.view", "reports.export",
        "settings.view"
    ],
    
    "accountant": [
        "sales.view", "customers.view",
        "finance.*", "reports.*",
        "settings.view"
    ],
    
    "cashier": [
        "sales.view", "sales.create", "sales.update",
        "products.view", "customers.view", "customers.create",
        "inventory.view",
        "reports.view"
    ],
    
    "staff": [
        "sales.view", "products.view", "customers.view",
        "inventory.view"
    ],
    
    "viewer": [
        "sales.view", "products.view", "customers.view",
        "reports.view"
    ]
}


class PermissionChecker:
    """Check if user has required permissions"""
    
    @staticmethod
    def has_permission(user_permissions: List[str], required_permission: str) -> bool:
        """
        Check if user has specific permission
        
        Args:
            user_permissions: List of user's permissions
            required_permission: Required permission (e.g., "sales.create")
            
        Returns:
            True if user has permission
        """
        # Check exact match
        if required_permission in user_permissions:
            return True
        
        # Check wildcard permissions (e.g., "sales.*")
        permission_parts = required_permission.split(".")
        if len(permission_parts) == 2:
            wildcard = f"{permission_parts[0]}.*"
            if wildcard in user_permissions:
                return True
        
        # Check super wildcard
        if "*" in user_permissions:
            return True
        
        return False
    
    @staticmethod
    def has_any_permission(user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Check if user has any of the required permissions"""
        return any(
            PermissionChecker.has_permission(user_permissions, perm)
            for perm in required_permissions
        )
    
    @staticmethod
    def has_all_permissions(user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Check if user has all required permissions"""
        return all(
            PermissionChecker.has_permission(user_permissions, perm)
            for perm in required_permissions
        )
    
    @staticmethod
    def get_role_permissions(role: str) -> List[str]:
        """Get permissions for a role"""
        return DEFAULT_ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def is_higher_role(role1: str, role2: str) -> bool:
        """Check if role1 is higher than role2 in hierarchy"""
        level1 = ROLE_HIERARCHY.get(role1, 0)
        level2 = ROLE_HIERARCHY.get(role2, 0)
        return level1 > level2


def require_permission(permission: str):
    """
    Decorator to require specific permission for endpoint
    
    Usage:
        @app.get("/sales")
        @require_permission("sales.view")
        async def get_sales():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request: Request = kwargs.get("request")
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            # Extract and verify token
            token = auth_header.replace("Bearer ", "")
            try:
                user_data = TokenManager.verify_token(token)
            except HTTPException:
                raise
            
            # Get user permissions
            user_permissions = user_data.get("permissions", [])
            user_role = user_data.get("role", "")
            
            # Add role-based permissions
            role_permissions = PermissionChecker.get_role_permissions(user_role)
            all_permissions = list(set(user_permissions + role_permissions))
            
            # Check permission
            if not PermissionChecker.has_permission(all_permissions, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            # Add user data to kwargs
            kwargs["current_user"] = user_data
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(min_role: str):
    """
    Decorator to require minimum role level
    
    Usage:
        @app.post("/users")
        @require_role("manager")
        async def create_user():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            token = auth_header.replace("Bearer ", "")
            user_data = TokenManager.verify_token(token)
            user_role = user_data.get("role", "")
            
            # Check if user role is high enough
            user_level = ROLE_HIERARCHY.get(user_role, 0)
            required_level = ROLE_HIERARCHY.get(min_role, 0)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role. Required: {min_role}, Current: {user_role}"
                )
            
            kwargs["current_user"] = user_data
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Dependency for FastAPI
async def get_current_user_with_permission(
    permission: str,
    request: Request
) -> dict:
    """
    Dependency to get current user and check permission
    
    Usage:
        @app.get("/sales")
        async def get_sales(
            current_user: dict = Depends(
                lambda r: get_current_user_with_permission("sales.view", r)
            )
        ):
            ...
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.replace("Bearer ", "")
    user_data = TokenManager.verify_token(token)
    
    # Get permissions
    user_permissions = user_data.get("permissions", [])
    user_role = user_data.get("role", "")
    role_permissions = PermissionChecker.get_role_permissions(user_role)
    all_permissions = list(set(user_permissions + role_permissions))
    
    # Check permission
    if not PermissionChecker.has_permission(all_permissions, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: {permission}"
        )
    
    return user_data


# Example usage in endpoints:
"""
from fastapi import FastAPI, Depends, Request
from retail.middleware.rbac import require_permission, require_role, get_current_user_with_permission

app = FastAPI()

# Using decorator
@app.get("/sales")
@require_permission("sales.view")
async def get_sales(request: Request):
    return {"sales": []}

# Using decorator for role
@app.post("/users")
@require_role("admin")
async def create_user(request: Request):
    return {"user": "created"}

# Using dependency
@app.get("/products")
async def get_products(
    current_user: dict = Depends(
        lambda r: get_current_user_with_permission("products.view", r)
    )
):
    return {"products": [], "user": current_user}
"""
