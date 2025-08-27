from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import logging

from app.database import SessionLocal, engine, Base
from app import models
from app.api import endpoints, websocket
from app.telegram.bot import TelegramBot
from app.utils.helpers import get_settings

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建資料庫表
Base.metadata.create_all(bind=engine)

# 獲取配置
settings = get_settings()

app = FastAPI(
    title="Telegram NFT Game API",
    description="A Telegram-based gaming platform with NFT rewards",
    version="1.0.0"
)

# 中間件設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(endpoints.router, prefix="/api/v1", tags=["api"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Telegram 機器人實例
telegram_bot = None

@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    global telegram_bot
    if settings.telegram_bot_token:
        try:
            telegram_bot = TelegramBot(settings.telegram_bot_token)
            # 在後台啟動 Telegram 機器人
            import threading
            thread = threading.Thread(target=telegram_bot.run, daemon=True)
            thread.start()
            logger.info("Telegram bot started successfully")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    if telegram_bot:
        telegram_bot.stop()
        logger.info("Telegram bot stopped")

@app.get("/")
async def root():
    """根路由"""
    return {"message": "Telegram NFT Game API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "telegram-nft-game"}