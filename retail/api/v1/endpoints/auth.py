"""
RetailOS - Authentication Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from retail.core.database import get_db
from retail.core.security import (
    verify_password,
    create_access_token,
    get_current_active_user
)
from retail.core.config import settings
from retail.models.user import User
from retail.schemas.auth import Token, UserResponse

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """KullanÄ±cÄ± giriÅŸi"""
    # KullanÄ±cÄ±yÄ± bul
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # KullanÄ±cÄ± kontrolÃ¼
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Token oluÅŸtur
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """Mevcut kullanÄ±cÄ± bilgisi"""
    return current_user
