import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

ECHO_SQL = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800")) 
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=ECHO_SQL,
    pool_pre_ping=True,
    pool_recycle=POOL_RECYCLE,
    pool_timeout=POOL_TIMEOUT,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        logger.error("DB connection error: %s", type(e).__name__)
        raise HTTPException(status_code=503, detail="データベース接続エラー")
    finally:
        db.close()