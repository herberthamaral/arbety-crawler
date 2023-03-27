# kelly criterion
import sqlite3

def read_db():
    db = sqlite3.connect("bets.db")
    cur = db.cursor()
    cur.execute("SELECT color FROM bets ORDER BY started_at")
    return [r[0] for r in cur.fetchall()]

def get_max_streak(db_slice):
    maxes = {"red": 0, "black": 0, "white": 0}
    currents = {"red": 0, "black": 0, "white": 0}
    current = ''
    for s in db_slice:
        if current != s:
            currents[s] = 0
        currents[s] += 1
        maxes[s] = max(maxes[s], currents[s])
        current = s
    return maxes

def formula(probability_of_win: float = 17.0/36) -> float:
    probability_of_loss = 1 - probability_of_win
    proportion_of_win = 2

    return probability_of_win - probability_of_loss / proportion_of_win
