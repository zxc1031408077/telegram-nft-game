from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    game_coin = Column(Float, default=0.0)
    wallet_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    nfts = relationship("NFT", back_populates="owner")
    room_players = relationship("RoomPlayer", back_populates="player")
    transactions = relationship("Transaction", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    game_type = Column(String, nullable=False)  # mines, dice, blackjack, balloons, cards
    entry_fee = Column(Float, default=10.0)
    max_players = Column(Integer, default=10)
    current_players = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    first_bet_amount = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    players = relationship("RoomPlayer", back_populates="room")

class RoomPlayer(Base):
    __tablename__ = "room_players"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    bet_amount = Column(Float, default=0.0)
    is_ready = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room", back_populates="players")
    player = relationship("User", back_populates="room_players")

class NFT(Base):
    __tablename__ = "nfts"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(String, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    attributes = Column(JSON)  # 存儲 NFT 屬性
    transaction_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="nfts")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    type = Column(String)  # purchase, game_win, game_loss, nft_mint, room_entry
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")