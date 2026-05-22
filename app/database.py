import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import OperationalError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

ECHO_SQL = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=ECHO_SQL,
    pool_pre_ping=True,
    pool_recycle=3600,
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