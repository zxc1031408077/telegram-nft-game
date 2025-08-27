from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import asyncio

from app.database import get_db
from app import crud
from app.game_logic import get_game_class

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
        self.game_rooms: dict = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][user_id] = websocket

    def disconnect(self, room_id: str, user_id: int):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            del self.active_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(self, message: dict, room_id: str, user_id: int):
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            await self.active_connections[room_id][user_id].send_json(message)

    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].values():
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/room/{room_id}/user/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket, room_id, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "join_room":
                # 處理玩家加入房間
                room = crud.get_room(db, int(room_id))
                user = crud.get_user(db, int(user_id))
                
                if room and user:
                    # 通知其他玩家
                    await manager.broadcast({
                        "action": "player_joined",
                        "user_id": user_id,
                        "username": user.username,
                        "current_players": room.current_players
                    }, room_id)
            
            elif action == "place_bet":
                # 處理玩家下注
                bet_amount = data.get("amount")
                bet_choice = data.get("choice")
                
                # 檢查是否是首位下注者
                room = crud.get_room(db, int(room_id))
                if room and room.first_bet_amount is None:
                    # 設置首位下注金額
                    crud.update_room_bet(db, int(room_id), bet_amount)
                
                # 通知其他玩家
                await manager.broadcast({
                    "action": "bet_placed",
                    "user_id": user_id,
                    "amount": bet_amount,
                    "choice": bet_choice
                }, room_id)
            
            elif action == "start_game":
                # 開始遊戲
                room = crud.get_room(db, int(room_id))
                if room:
                    # 獲取所有玩家
                    players = [rp.player for rp in room.players]
                    
                    # 創建遊戲實例
                    game_class = get_game_class(room.game_type)
                    if game_class:
                        game = game_class(players, room.entry_fee)
                        
                        # 執行遊戲
                        result = game.play()
                        
                        # 廣播遊戲結果
                        await manager.broadcast({
                            "action": "game_result",
                            "result": result
                        }, room_id)
            
            elif action == "chat_message":
                # 處理聊天消息
                message = data.get("message")
                await manager.broadcast({
                    "action": "chat_message",
                    "user_id": user_id,
                    "message": message
                }, room_id)
    
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        await manager.broadcast({
            "action": "player_left",
            "user_id": user_id
        }, room_id)