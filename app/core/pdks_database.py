"""
PDKS specific database management using SQLAlchemy.
Adapts EXFIN_OPS settings to provide session and engine for PDKS models.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.core.config import settings

# Find PostgreSQL config
pg_config = next(
    (c for c in settings.DB_CONFIGS if c.get("Type") == "PostgreSQL"),
    None
)

if not pg_config:
    # Fallback to env variables if config not found in DB_CONFIGS
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{pg_config['Username']}:{pg_config['Password']}@{pg_config['Server']}:{pg_config.get('Port', 5432)}/{pg_config['Database']}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
