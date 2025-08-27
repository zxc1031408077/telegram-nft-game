import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./game.db")