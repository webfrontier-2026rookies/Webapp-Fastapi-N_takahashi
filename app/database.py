import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
if SQLALCHEMY_DATABASE_URL is None:
    # 実際に入っている環境変数をすべて表示して止める（これで何が読み込まれているか分かる）
    print("DEBUG: OS環境変数一覧:", os.environ)
    raise ValueError("DATABASE_URL が None です！.env と docker-compose.yml を確認してください。")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()