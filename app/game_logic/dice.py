import random
from typing import List, Dict, Any

class DiceGame:
    def __init__(self, players: List[Any], entry_fee: float):
        self.players = players
        self.entry_fee = entry_fee
        self.bets = {player.user_id: {"choice": None, "amount": entry_fee} for player in players}
        self.first_bet = None
    
    def place_bet(self, user_id: int, choice: str, amount: float):
        """玩家下注，必須跟隨首位玩家的下注金額"""
        if self.first_bet is None:
            self.first_bet = amount
            self.bets[user_id] = {"choice": choice, "amount": amount}
            return True
        
        if amount != self.first_bet:
            return False  # 下注金額必須與首位玩家相同
        
        self.bets[user_id] = {"choice": choice, "amount": amount}
        return True
    
    def play(self) -> Dict[str, Any]:
        """執行遊戲並返回結果"""
        # 45% 機率有贏家，55% 機率無贏家
        has_winner = random.random() < 0.45
        
        if not has_winner:
            return {
                "has_winner": False,
                "refund": self.entry_fee * 0.95  # 退還95%入場費
            }
        
        # 擲骰子
        dice_roll = random.randint(1, 6)
        result = "big" if dice_roll > 3 else "small"
        
        # 找出贏家
        winners = []
        for user_id, bet in self.bets.items():
            if bet["choice"] == result:
                winners.append(user_id)
        
        if not winners:
            # 沒有玩家猜中，所有玩家輸
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