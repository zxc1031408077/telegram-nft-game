from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas, models
from app.game_logic import get_game_class
from app.nft.blockchain import NFTManager

router = APIRouter()

# 用戶相關端點
@router.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """創建新用戶"""
    db_user = crud.get_user_by_telegram_id(db, user.telegram_id)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this Telegram ID already exists"
        )
    return crud.create_user(db=db, user=user)

@router.get("/users", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """獲取用戶列表"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """獲取特定用戶"""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """更新用戶信息"""
    db_user = crud.update_user(db, user_id, user_update)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.post("/users/{user_id}/purchase-coins")
def purchase_coins(user_id: int, purchase: schemas.CoinPurchase, db: Session = Depends(get_db)):
    """購買遊戲幣"""
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 這裡應該整合支付網關處理 USDT 支付
    # 簡化版本直接增加遊戲幣
    new_balance = user.game_coin + purchase.amount
    updated_user = crud.update_user_coins(db, user_id, new_balance)
    
    # 記錄交易
    transaction = schemas.TransactionCreate(
        user_id=user_id,
        amount=purchase.amount,
        type="purchase",
        description=f"Purchased {purchase.amount} coins via {purchase.payment_method}"
    )
    crud.create_transaction(db, transaction)
    
    return {"message": "Coins purchased successfully", "new_balance": updated_user.game_coin}

# 房間相關端點
@router.get("/rooms", response_model=List[schemas.Room])
def read_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """獲取房間列表"""
    rooms = crud.get_rooms(db, skip=skip, limit=limit)
    return rooms

@router.get("/rooms/available", response_model=List[schemas.Room])
def read_available_rooms(game_type: str = None, db: Session = Depends(get_db)):
    """獲取可用房間列表"""
    rooms = crud.get_available_rooms(db, game_type)
    return rooms

@router.post("/rooms", response_model=schemas.Room, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    """創建新房間"""
    try:
        return crud.create_room(db=db, room=room)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/rooms/{room_id}/join")
def join_room(room_id: int, room_player: schemas.RoomPlayerCreate, db: Session = Depends(get_db)):
    """加入房間"""
    try:
        result = crud.add_player_to_room(db, room_player)
        return {"message": "Joined room successfully", "room_player": result}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# NFT相關端點
@router.post("/nft/mint")
def mint_nft(nft_request: schemas.NFTMintRequest, db: Session = Depends(get_db)):
    """鑄造NFT"""
    user = crud.get_user(db, user_id=nft_request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.game_coin < nft_request.cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient coins"
        )
    
    # 初始化NFT管理器
    nft_manager = NFTManager()
    
    # 鑄造NFT
    token_id = nft_manager.mint_nft(
        to_address=user.wallet_address or "0x0",  # 需要用戶設置錢包地址
        token_uri=nft_request.token_uri,
        metadata=nft_request.metadata
    )
    
    if not token_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mint NFT"
        )
    
    # 扣除遊戲幣
    new_balance = user.game_coin - nft_request.cost
    crud.update_user_coins(db, nft_request.user_id, new_balance)
    
    # 記錄交易
    transaction = schemas.TransactionCreate(
        user_id=nft_request.user_id,
        amount=-nft_request.cost,
        type="nft_mint",
        description=f"Minted NFT: {nft_request.name}"
    )
    crud.create_transaction(db, transaction)
    
    # 保存NFT記錄
    nft = crud.create_nft(
        db, 
        schemas.NFTCreate(
            token_id=token_id,
            owner_id=nft_request.user_id,
            name=nft_request.name,
            description=nft_request.description,
            image_url=nft_request.image_url,
            attributes=nft_request.metadata
        )
    )
    
    return {"message": "NFT minted successfully", "nft_id": token_id, "nft": nft}

@router.get("/users/{user_id}/nfts", response_model=List[schemas.NFT])
def get_user_nfts(user_id: int, db: Session = Depends(get_db)):
    """獲取用戶的NFT列表"""
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    nfts = crud.get_nfts_by_owner(db, user_id)
    return nfts

# 遊戲相關端點
@router.post("/games/{game_type}/play")
def play_game(game_type: str, players: List[int], entry_fee: float, db: Session = Depends(get_db)):
    """執行遊戲"""
    game_class = get_game_class(game_type)
    if not game_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid game type"
        )
    
    # 獲取玩家信息
    db_players = []
    for player_id in players:
        player = crud.get_user(db, player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player with ID {player_id} not found"
            )
        db_players.append(player)
    
    # 創建遊戲實例
    game = game_class(db_players, entry_fee)
    
    # 執行遊戲
    result = game.play()
    
    # 處理遊戲結果
    if result["has_winner"]:
        if "winner_id" in result:
            # 單一贏家
            winner_id = result["winner_id"]
            prize = result["prize"]
            
            # 發放獎勵
            winner = crud.get_user(db, winner_id)
            if winner:
                new_balance = winner.game_coin + prize
                crud.update_user_coins(db, winner_id, new_balance)
                
                # 記錄交易
                transaction = schemas.TransactionCreate(
                    user_id=winner_id,
                    amount=prize,
                    type="game_win",
                    description=f"Won {prize} coins in {game_type} game"
                )
                crud.create_transaction(db, transaction)
        
        elif "winners" in result:
            # 多個贏家
            winners = result["winners"]
            prize_per_winner = result["prize_per_winner"]
            
            for winner_id in winners:
                # 發放獎勵
                winner = crud.get_user(db, winner_id)
                if winner:
                    new_balance = winner.game_coin + prize_per_winner
                    crud.update_user_coins(db, winner_id, new_balance)
                    
                    # 記錄交易
                    transaction = schemas.TransactionCreate(
                        user_id=winner_id,
                        amount=prize_per_winner,
                        type="game_win",
                        description=f"Won {prize_per_winner} coins in {game_type} game"
                    )
                    crud.create_transaction(db, transaction)
    else:
        # 沒有贏家，退還部分入場費
        refund = result["refund"]
        for player in db_players:
            new_balance = player.game_coin + refund
            crud.update_user_coins(db, player.id, new_balance)
            
            # 記錄交易
            transaction = schemas.TransactionCreate(
                user_id=player.id,
                amount=refund,
                type="game_refund",
                description=f"Refund of {refund} coins from {game_type} game"
            )
            crud.create_transaction(db, transaction)
    
    return result