from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional

from app import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_telegram_id(db: Session, telegram_id: str):
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        game_coin=user.game_coin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_coins(db: Session, user_id: int, amount: float):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.game_coin = amount
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

def get_room(db: Session, room_id: int):
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Room).offset(skip).limit(limit).all()

def get_available_rooms(db: Session, game_type: Optional[str] = None):
    query = db.query(models.Room).filter(
        and_(
            models.Room.is_active == True,
            models.Room.current_players < models.Room.max_players
        )
    )
    if game_type:
        query = query.filter(models.Room.game_type == game_type)
    return query.all()

def get_room_count(db: Session):
    return db.query(models.Room).filter(models.Room.is_active == True).count()

def create_room(db: Session, room: schemas.RoomCreate):
    # 檢查房間數量限制
    room_count = get_room_count(db)
    if room_count >= 20:  # 最大房間數限制
        raise ValueError("Maximum room limit (20) reached")
    
    db_room = models.Room(
        name=room.name,
        game_type=room.game_type,
        entry_fee=room.entry_fee,
        max_players=room.max_players
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def update_room_bet(db: Session, room_id: int, bet_amount: float):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if room and room.first_bet_amount is None:
        room.first_bet_amount = bet_amount
        db.commit()
        db.refresh(room)
    return room

def add_player_to_room(db: Session, room_player: schemas.RoomPlayerCreate):
    # 檢查房間是否存在且有空間
    room = get_room(db, room_player.room_id)
    if not room or room.current_players >= room.max_players:
        raise ValueError("Room is full or does not exist")
    
    # 檢查用戶是否有足夠遊戲幣
    user = get_user(db, room_player.user_id)
    if not user or user.game_coin < room.entry_fee:
        raise ValueError("Insufficient coins")
    
    # 檢查用戶是否已在房間中
    existing_player = db.query(models.RoomPlayer).filter(
        and_(
            models.RoomPlayer.room_id == room_player.room_id,
            models.RoomPlayer.user_id == room_player.user_id
        )
    ).first()
    
    if existing_player:
        raise ValueError("User already in room")
    
    # 扣除入場費
    user.game_coin -= room.entry_fee
    
    # 創建房間玩家記錄
    db_room_player = models.RoomPlayer(
        room_id=room_player.room_id,
        user_id=room_player.user_id,
        bet_amount=room_player.bet_amount,
        is_ready=room_player.is_ready
    )
    db.add(db_room_player)
    
    # 更新房間玩家數量
    room.current_players += 1
    if room.current_players >= room.max_players:
        room.is_active = False
    
    db.commit()
    db.refresh(db_room_player)
    
    # 記錄交易
    transaction = models.Transaction(
        user_id=room_player.user_id,
        amount=-room.entry_fee,
        type="room_entry",
        description=f"Entry fee for room {room.id} ({room.game_type})"
    )
    db.add(transaction)
    db.commit()
    
    return db_room_player

def remove_player_from_room(db: Session, room_id: int, user_id: int):
    room_player = db.query(models.RoomPlayer).filter(
        and_(
            models.RoomPlayer.room_id == room_id,
            models.RoomPlayer.user_id == user_id
        )
    ).first()
    
    if room_player:
        room = get_room(db, room_id)
        if room:
            room.current_players -= 1
            if room.current_players < room.max_players:
                room.is_active = True
        
        db.delete(room_player)
        db.commit()
        return True
    
    return False

def get_nft(db: Session, nft_id: int):
    return db.query(models.NFT).filter(models.NFT.id == nft_id).first()

def get_nft_by_token_id(db: Session, token_id: str):
    return db.query(models.NFT).filter(models.NFT.token_id == token_id).first()

def get_nfts_by_owner(db: Session, owner_id: int):
    return db.query(models.NFT).filter(models.NFT.owner_id == owner_id).all()

def create_nft(db: Session, nft: schemas.NFTCreate):
    db_nft = models.NFT(
        token_id=nft.token_id,
        owner_id=nft.owner_id,
        name=nft.name,
        description=nft.description,
        image_url=nft.image_url,
        attributes=nft.attributes
    )
    db.add(db_nft)
    db.commit()
    db.refresh(db_nft)
    return db_nft

def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(
        user_id=transaction.user_id,
        amount=transaction.amount,
        type=transaction.type,
        description=transaction.description
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction