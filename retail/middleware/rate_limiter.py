"""
Rate Limiting Middleware
Prevent API abuse and DDoS attacks

@created: 2024-12-18
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio


class RateLimiter:
    """In-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.cleanup_task = None
    
    def is_rate_limited(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> tuple[bool, Optional[int]]:
        """
        Check if identifier is rate limited
        
        Args:
            identifier: IP address or user ID
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            (is_limited, retry_after_seconds)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Get or create request history
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= max_requests:
            # Calculate retry after time
            oldest_request = min(self.requests[identifier])
            retry_after = (oldest_request + timedelta(seconds=window_seconds) - now).total_seconds()
            return True, int(retry_after) + 1
        
        # Add current request
        self.requests[identifier].append(now)
        
        return False, None
    
    def cleanup(self):
        """Remove old entries to prevent memory leak"""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=1)
        
        # Remove identifiers with no recent requests
        to_remove = []
        for identifier, requests in self.requests.items():
            if not requests or max(requests) < cutoff:
                to_remove.append(identifier)
        
        for identifier in to_remove:
            del self.requests[identifier]
    
    async def start_cleanup_task(self):
        """Start periodic cleanup task"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            self.cleanup()


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting"""
    
    def __init__(self, app, config: Optional[Dict] = None):
        super().__init__(app)
        self.config = config or {}
        
        # Default limits
        self.default_limit = self.config.get("default_limit", 100)
        self.default_window = self.config.get("default_window", 60)
        
        # Endpoint-specific limits
        self.endpoint_limits = self.config.get("endpoint_limits", {
            "/api/auth/login": {"max_requests": 5, "window": 60},  # 5 per minute
            "/api/auth/register": {"max_requests": 3, "window": 300},  # 3 per 5 minutes
            "/api/auth/reset-password": {"max_requests": 3, "window": 300},
            "/api/sales": {"max_requests": 200, "window": 60},  # 200 per minute
            "/api/products": {"max_requests": 300, "window": 60},
        })
        
        # Whitelist IPs (bypass rate limiting)
        self.whitelist = self.config.get("whitelist", [
            "127.0.0.1",
            "::1",
            "localhost"
        ])
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Skip if whitelisted
        if client_ip in self.whitelist:
            return await call_next(request)
        
        # Get path
        path = request.url.path
        
        # Get rate limit for this endpoint
        limit_config = None
        for endpoint, config in self.endpoint_limits.items():
            if path.startswith(endpoint):
                limit_config = config
                break
        
        # Use default if no specific limit
        max_requests = limit_config.get("max_requests", self.default_limit) if limit_config else self.default_limit
        window = limit_config.get("window", self.default_window) if limit_config else self.default_window
        
        # Check rate limit
        is_limited, retry_after = rate_limiter.is_rate_limited(
            identifier=client_ip,
            max_requests=max_requests,
            window_seconds=window
        )
        
        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after)
                }
            )
        
        # Add rate limit headers
        response = await call_next(request)
        
        # Get remaining requests
        remaining = max_requests - len(rate_limiter.requests.get(client_ip, []))
        
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)
        
        return response


class UserRateLimiter:
    """Rate limiter based on user ID (after authentication)"""
    
    @staticmethod
    def check_user_rate_limit(
        user_id: str,
        action: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check rate limit for specific user action
        
        Args:
            user_id: User identifier
            action: Action type (e.g., 'create_sale', 'export_data')
            max_requests: Max requests allowed
            window_seconds: Time window
            
        Returns:
            True if action is allowed
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        identifier = f"{user_id}:{action}"
        is_limited, retry_after = rate_limiter.is_rate_limited(
            identifier=identifier,
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "action": action,
                    "retry_after": retry_after
                }
            )
        
        return True


# Usage in main.py:
"""
from fastapi import FastAPI
from retail.middleware.rate_limiter import RateLimitMiddleware, rate_limiter

app = FastAPI()

# Add middleware
app.add_middleware(
    RateLimitMiddleware,
    config={
        "default_limit": 100,
        "default_window": 60,
        "endpoint_limits": {
            "/api/auth/login": {"max_requests": 5, "window": 60},
            "/api/sales": {"max_requests": 200, "window": 60},
        },
        "whitelist": ["127.0.0.1", "10.0.0.0/8"]
    }
)

# Start cleanup task
@app.on_event("startup")
async def startup():
    asyncio.create_task(rate_limiter.start_cleanup_task())
"""
