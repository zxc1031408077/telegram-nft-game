from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, ContextTypes

from .bot import TelegramBot
from .database import init_db, engine
from .config import Config
import logging

# 設置日誌
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()
telegram_bot = None

@app.on_event("startup")
async def startup_event():
    # 初始化數據庫
    await init_db()
    
    # 初始化Telegram機器人
    global telegram_bot
    telegram_bot = TelegramBot(Config.TELEGRAM_BOT_TOKEN)
    
    # 設置數據庫引擎到應用程序
    telegram_bot.application.db_engine = engine
    
    # 設置webhook
    await telegram_bot.application.bot.set_webhook(f"{Config.WEBHOOK_URL}/webhook")
    logger.info("機器人啟動完成")

@app.on_event("shutdown")
async def shutdown_event():
    if telegram_bot:
        await telegram_bot.application.shutdown()
    logger.info("機器人已關閉")

@app.post("/webhook")
async def webhook(request: Request):
    """接收Telegram更新"""
    global telegram_bot
    data = await request.json()
    update = Update.de_json(data, telegram_bot.application.bot)
    
    await telegram_bot.application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Telegram Game Bot is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}