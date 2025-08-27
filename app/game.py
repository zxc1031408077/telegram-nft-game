import random
import json
from typing import List, Dict, Any

class DiceGame:
    def __init__(self, players: List[int], bet_amount: float):
        self.players = players
        self.bet_amount = bet_amount
        self.total_pot = bet_amount * len(players)
        self.system_fee = 0.05  # 5%手續費
        
    def play(self) -> Dict[str, Any]:
        # 45%機率有勝利者，55%機率無勝利者
        has_winner = random.random() < 0.45
        
        if has_winner:
            # 隨機選擇一名勝利者
            winner_id = random.choice(self.players)
            prize = self.total_pot * (1 - self.system_fee)
            
            return {
                "has_winner": True,
                "winner_id": winner_id,
                "prize": prize,
                "system_fee": self.total_pot * self.system_fee,
                "players": self.players
            }
        else:
            # 退回本金，但扣除5%手續費
            refund_per_player = self.bet_amount * (1 - self.system_fee)
            system_fee_total = self.total_pot * self.system_fee
            
            return {
                "has_winner": False,
                "refund_per_player": refund_per_player,
                "system_fee": system_fee_total,
                "players": self.players
            }

class GameManager:
    def __init__(self):
        self.active_rooms = {}
    
    def create_room(self, room_id: str, creator_id: int, game_type: str, bet_amount: float = 10.0):
        self.active_rooms[room_id] = {
            "room_id": room_id,
            "game_type": game_type,
            "creator_id": creator_id,
            "players": [creator_id],
            "bet_amount": bet_amount,
            "status": "waiting"
        }
        return self.active_rooms[room_id]
    
    def join_room(self, room_id: str, player_id: int):
        if room_id in self.active_rooms:
            if player_id not in self.active_rooms[room_id]["players"]:
                self.active_rooms[room_id]["players"].append(player_id)
            return True
        return False
    
    def start_game(self, room_id: str):
        if room_id in self.active_rooms and len(self.active_rooms[room_id]["players"]) > 0:
            room = self.active_rooms[room_id]
            
            if room["game_type"] == "dice":
                game = DiceGame(room["players"], room["bet_amount"])
                result = game.play()
                room["result"] = result
                room["status"] = "completed"
                
                # 從活動房間中移除
                self.active_rooms.pop(room_id, None)
                
                return result
        return None

# 全局遊戲管理器
game_manager = GameManager()