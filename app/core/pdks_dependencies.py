"""
FastAPI bağımlılıkları
"""
from fastapi import Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.pdks_core_database import database_manager
from app.core.pdks_config import config_manager


def get_db(db_name: Optional[str] = None) -> Session:
    """
    Veritabanı oturumu bağımlılığı - Varsayılan veya belirtilen veritabanı
    db_name=None ise varsayılan veritabanı kullanılır (Default: PostgreSQLDatabase)
    """
    session = database_manager.get_session(db_name)
    try:
        yield session
    finally:
        session.close()


def get_default_db() -> Session:
    """Varsayılan veritabanı oturumu"""
    return get_db()


def get_db_by_name(db_name: str) -> Session:
    """Belirli bir veritabanı için oturum"""
    return get_db(db_name)
