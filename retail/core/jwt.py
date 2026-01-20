"""
JWT Token Management with Refresh Tokens
Enhanced security for ExRetailOS

@created: 2024-12-18
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import hashlib

# Configuration
SECRET_KEY = "your-secret-key-change-in-production-min-32-chars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory token blacklist (use Redis in production)
token_blacklist = set()
# In-memory refresh tokens (use database in production)
refresh_tokens_db: Dict[str, Dict[str, Any]] = {}


class TokenManager:
    """Manage JWT tokens with refresh token support"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Payload data (user_id, username, roles, etc.)
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        Create refresh token
        
        Args:
            user_id: User identifier
            
        Returns:
            Refresh token string
        """
        # Generate random token
        token = secrets.token_urlsafe(32)
        
        # Store in database with expiration
        refresh_tokens_db[token] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "revoked": False
        }
        
        return token
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Check if token is blacklisted
            if token in token_blacklist:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # Decode and verify token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verify token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}"
            )
    
    @staticmethod
    def verify_refresh_token(refresh_token: str) -> str:
        """
        Verify refresh token and return user_id
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            User ID
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        token_data = refresh_tokens_db.get(refresh_token)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        if token_data.get("revoked"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        if datetime.utcnow() > token_data.get("expires_at"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        
        return token_data.get("user_id")
    
    @staticmethod
    def revoke_token(token: str):
        """Add token to blacklist"""
        token_blacklist.add(token)
    
    @staticmethod
    def revoke_refresh_token(refresh_token: str):
        """Revoke refresh token"""
        if refresh_token in refresh_tokens_db:
            refresh_tokens_db[refresh_token]["revoked"] = True
    
    @staticmethod
    def revoke_all_user_tokens(user_id: str):
        """Revoke all refresh tokens for a user"""
        for token, data in refresh_tokens_db.items():
            if data.get("user_id") == user_id:
                data["revoked"] = True
    
    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired tokens from storage"""
        current_time = datetime.utcnow()
        expired = [
            token for token, data in refresh_tokens_db.items()
            if current_time > data.get("expires_at")
        ]
        for token in expired:
            del refresh_tokens_db[token]


class PasswordManager:
    """Manage password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def check_password_strength(password: str) -> Dict[str, Any]:
        """
        Check password strength
        
        Returns:
            {
                "valid": bool,
                "score": int (0-5),
                "feedback": list of strings
            }
        """
        feedback = []
        score = 0
        
        # Length check
        if len(password) < 8:
            feedback.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
        
        # Uppercase check
        if not any(c.isupper() for c in password):
            feedback.append("Password should contain uppercase letters")
        else:
            score += 1
        
        # Lowercase check
        if not any(c.islower() for c in password):
            feedback.append("Password should contain lowercase letters")
        else:
            score += 1
        
        # Digit check
        if not any(c.isdigit() for c in password):
            feedback.append("Password should contain numbers")
        else:
            score += 1
        
        # Special character check
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            feedback.append("Password should contain special characters")
        else:
            score += 1
        
        valid = len(feedback) == 0 and len(password) >= 8
        
        return {
            "valid": valid,
            "score": score,
            "feedback": feedback
        }
    
    @staticmethod
    def check_compromised_password(password: str) -> bool:
        """
        Check if password has been compromised (haveibeenpwned API)
        Uses k-anonymity model - only sends first 5 chars of SHA-1 hash
        
        Returns:
            True if password is compromised
        """
        import requests
        
        # Hash password
        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        try:
            # Query haveibeenpwned API
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                # Check if hash suffix exists in response
                hashes = (line.split(':') for line in response.text.splitlines())
                for hash_suffix, count in hashes:
                    if hash_suffix == suffix:
                        return True
            
            return False
            
        except Exception as e:
            # If API fails, don't block user
            print(f"Could not check compromised password: {e}")
            return False


def get_current_user(token: str) -> Dict[str, Any]:
    """
    Dependency to get current user from JWT token
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User data from token
    """
    payload = TokenManager.verify_token(token)
    return payload


# Example usage in FastAPI endpoint:
"""
from fastapi import Depends, Header

@app.get("/protected")
async def protected_route(
    authorization: str = Header(...)
):
    # Extract token from "Bearer {token}"
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token)
    return {"message": f"Hello {user.get('username')}"}
"""
