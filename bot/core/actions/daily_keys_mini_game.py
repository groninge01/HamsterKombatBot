import base64
import hashlib
import random
from datetime import datetime
from random import randint

from bot.core.entities import DailyMiniGame


def get_keys_mini_game_cipher(mini_game: DailyMiniGame, user_id: str, max_points: int) -> str:
    number = int(datetime.fromisoformat(mini_game.start_date.replace("Z", "+00:00")).timestamp())
    number_len = len(str(number))
    index = (number % (number_len - 2)) + 1
    res = ""
    score_per_game = {
        "Candles": 0,
        "Tiles": random.randint(int(max_points * 0.1), max_points) if max_points > 300 else max_points,
    }

    for i in range(1, number_len + 1):
        if i == index:
            res += "0"
        else:
            res += str(randint(0, 9))

    score_cipher = 2 * (number + score_per_game[mini_game.id])

    data_string = "|".join(
        [
            res,
            user_id,
            mini_game.id,
            str(score_cipher),
            base64.b64encode(hashlib.sha256(f"415t1ng{score_cipher}0ra1cum5h0t".encode()).digest()).decode()
        ]
    ).encode()

    return base64.b64encode(data_string).decode()
