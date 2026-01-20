"""RetailOS - Auth Schemas"""
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    discount_limit: float
    is_active: bool

    class Config:
        from_attributes = True
