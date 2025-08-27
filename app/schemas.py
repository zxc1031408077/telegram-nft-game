from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    game_coin: float = 0.0

class UserUpdate(BaseModel):
    game_coin: Optional[float] = None
    wallet_address: Optional[str] = None

class User(UserBase):
    id: int
    game_coin: float
    wallet_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RoomBase(BaseModel):
    name: str
    game_type: str
    entry_fee: float = Field(..., ge=10.0, description="Minimum entry fee is 10 coins")
    max_players: int = Field(..., ge=2, le=10, description="Max players between 2 and 10")

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    current_players: int
    is_active: bool
    first_bet_amount: Optional[float] = None
    created_at: datetime

    class Config:
        orm_mode = True

class RoomPlayerBase(BaseModel):
    room_id: int
    user_id: int
    bet_amount: float = 0.0
    is_ready: bool = False

class RoomPlayerCreate(RoomPlayerBase):
    pass

class RoomPlayer(RoomPlayerBase):
    id: int
    joined_at: datetime

    class Config:
        orm_mode = True

class NFTAttributes(BaseModel):
    rarity: str
    game_type: str
    win_streak: Optional[int] = None
    special_trait: Optional[str] = None

class NFTBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    attributes: Dict[str, Any]

class NFTCreate(NFTBase):
    token_id: str
    owner_id: int

class NFT(NFTBase):
    id: int
    token_id: str
    owner_id: int
    transaction_hash: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class CoinPurchase(BaseModel):
    amount: float = Field(..., gt=0, description="Purchase amount must be greater than 0")
    payment_method: str = "usdt"

class NFTMintRequest(BaseModel):
    user_id: int
    cost: float = Field(..., gt=0, description="Mint cost must be greater than 0")
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    token_uri: str
    metadata: Dict[str, Any]

class TransactionBase(BaseModel):
    user_id: int
    amount: float
    type: str
    description: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class GameResult(BaseModel):
    has_winner: bool
    winner_id: Optional[int] = None
    prize: Optional[float] = None
    refund: Optional[float] = None
    winners: Optional[List[int]] = None
    prize_per_winner: Optional[float] = None