from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from app.utils.helpers import get_settings

settings = get_settings()

# 創建數據庫引擎
if settings.database_url and settings.database_url.startswith("postgresql"):
    engine = create_engine(settings.database_url)
else:
    # 默認使用 SQLite
    SQLALCHEMY_DATABASE_URL = "sqlite:///./telegram_game.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

# 創建會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 創建基類
Base = declarative_base()

# 依賴項
def get_db():
    """獲取數據庫會話"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()