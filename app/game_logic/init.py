from .mines import MinesGame
from .dice import DiceGame
from .blackjack import BlackjackGame
from .balloons import BalloonsGame
from .cards import CardsGame

GAME_TYPES = {
    "mines": MinesGame,
    "dice": DiceGame,
    "blackjack": BlackjackGame,
    "balloons": BalloonsGame,
    "cards": CardsGame
}

def get_game_class(game_type):
    return GAME_TYPES.get(game_type)