from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    balance = Column(Float, default=100.0)  # 初始100遊戲幣
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GameRoom(Base):
    __tablename__ = "game_rooms"
    
    id = Column(Integer, primary_key=True)
    room_id = Column(String, unique=True, nullable=False)
    game_type = Column(String, default="dice")  # dice, mines, blackjack, etc.
    creator_id = Column(Integer, nullable=False)
    players = Column(String)  # JSON string of player IDs
    bet_amount = Column(Float, default=10.0)
    status = Column(String, default="waiting")  # waiting, in_progress, completed
    result = Column(String)  # JSON string of game result
    created_at = Column(DateTime, default=datetime.utcnow)

class NFT(Base):
    __tablename__ = "nfts"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    rarity = Column(String, default="common")
    image_url = Column(String)
    token_id = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)