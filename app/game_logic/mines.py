import random
from typing import List, Dict, Any

class MinesGame:
    def __init__(self, players: List[Any], entry_fee: float, rows: int = 5, cols: int = 5, mines: int = 5):
        self.players = players
        self.entry_fee = entry_fee
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.grid = self.generate_grid()
        self.player_selections = {player.user_id: [] for player in players}
        self.first_bet = None
    
    def generate_grid(self):
        """生成地雷網格"""
        grid = [['empty' for _ in range(self.cols)] for _ in range(self.rows)]
        
        # 隨機放置地雷
        mine_positions = set()
        while len(mine_positions) < self.mines:
            row = random.randint(0, self.rows-1)
            col = random.randint(0, self.cols-1)
            mine_positions.add((row, col))
            grid[row][col] = 'mine'
        
        return grid
    
    def place_bet(self, user_id: int, amount: float):
        """玩家下注，必須跟隨首位玩家的下注金額"""
        if self.first_bet is None:
            self.first_bet = amount
            return True
        
        if amount != self.first_bet:
            return False  # 下注金額必須與首位玩家相同
        
        return True
    
    def select_cell(self, user_id: int, row: int, col: int):
        """玩家選擇格子"""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False, "Invalid cell selection"
        
        if (row, col) in self.player_selections[user_id]:
            return False, "Cell already selected"
        
        self.player_selections[user_id].append((row, col))
        
        # 檢查是否踩到地雷
        if self.grid[row][col] == 'mine':
            return True, "mine"
        
        return True, "safe"
    
    def play(self) -> Dict[str, Any]:
        """執行遊戲並返回結果"""
        # 45% 機率有贏家，55% 機率無贏家
        has_winner = random.random() < 0.45
        
        if not has_winner:
            return {
                "has_winner": False,
                "refund": self.entry_fee * 0.95  # 退還95%入場費
            }
        
        # 計算每位玩家的得分（安全格子數量）
        player_scores = {}
        for user_id, selections in self.player_selections.items():
            safe_count = 0
            for row, col in selections:
                if self.grid[row][col] == 'empty':
                    safe_count += 1
            player_scores[user_id] = safe_count
        
        # 找出最高分
        max_score = max(player_scores.values()) if player_scores else 0
        
        # 找出所有最高分玩家
        winners = [user_id for user_id, score in player_scores.items() if score == max_score]
        
        if not winners:
            # 沒有贏家
            return {
                "has_winner": False,
                "refund": self.entry_fee * 0.95  # 退還95%入場費
            }
        
        # 只有一位贏家獲得全部獎池
        if len(winners) == 1:
            return {
                "has_winner": True,
                "winner_id": winners[0],
                "prize": self.entry_fee * len(self.players) * 0.95  # 扣除5%手續費
            }
        
        # 多位贏家平分獎池
        prize_per_winner = (self.entry_fee * len(self.players) * 0.95) / len(winners)
        return {
            "has_winner": True,
            "winners": winners,
            "prize_per_winner": prize_per_winner
        }