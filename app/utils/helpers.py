from pydantic import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # 數據庫配置
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./telegram_game.db")
    
    # Telegram 配置
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # 區塊鏈配置
    blockchain_network: str = os.getenv("BLOCKCHAIN_NETWORK", "polygon")
    nft_contract_address: str = os.getenv("NFT_CONTRACT_ADDRESS", "")
    wallet_private_key: str = os.getenv("WALLET_PRIVATE_KEY", "")
    polygon_rpc_url: str = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    ethereum_rpc_url: str = os.getenv("ETHEREUM_RPC_URL", "")
    bsc_rpc_url: str = os.getenv("BSC_RPC_URL", "")
    
    # CORS 配置
    cors_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()