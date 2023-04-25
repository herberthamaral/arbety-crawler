# kelly criterion
import sqlite3
import parameters as params

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


def calc_probability(black, red, white):
    """
    Calcula a probabilidade da próxima jogada ser preto, branco ou vermelho
    baseado na quantidade de cada um nas últimas N jogadas.
    """
    total = float(black + white + red)
    prob_black = params.BLACK_ROLL_CHANCE - (black/total - params.BLACK_ROLL_CHANCE)
    prob_red = params.RED_ROLL_CHANCE - (red/total - params.RED_ROLL_CHANCE)
    prob_white = params.WHITE_ROLL_CHANCE - (white/total - params.WHITE_ROLL_CHANCE)
    return prob_black, prob_red, prob_white


def formula(
    probability_of_win: float = params.TOTAL_NON_WHITE / params.TOTAL_ROLLS,
    proportion_of_win: float = params.PROPORTION_OF_WIN_NON_WHITE,
) -> float:
    probability_of_loss = 1 - probability_of_win
    return probability_of_win - probability_of_loss / proportion_of_win


def calc_bets_based_on_db_slice(db_slice):
    """
    Calcula a proporção de investimento de capital em cada cor baseado no
    histórico do banco
    """
    black = sum([1 for c in db_slice if c == "black"])
    red = sum([1 for c in db_slice if c == "red"])
    white = sum([1 for c in db_slice if c == "white"])
    p_black, p_red, p_white = calc_probability(black, red, white)
    invest_black = formula(p_black)
    invest_red = formula(p_red)
    invest_white = formula(p_white, params.PROPORTION_OF_WIN_WHITE)
    if invest_black < 0 and invest_red < 0:
        invest_white += (invest_black * -1)
        invest_white += (invest_red * -1)
        invest_black = 0
        invest_red = 0
    if invest_black < 0:
        invest_red += (invest_black * -1)
        invest_black = 0
    if invest_red < 0:
        invest_black += (invest_white * -1)
        invest_red = 0
    if invest_white < 0:
        invest_white = 0
    return invest_black, invest_red, invest_white


def simulate_based_on_db(db):
    slice_start = 0
    slice_finish = params.WINDOW_SIZE
    money = params.START_MONEY
    len_db = len(db)
    wins = 0
    total_wins = 0
    total_bets = 0
    while slice_finish < len_db - 1 and money > params.STOP_LOSS:
        db_slice = db[slice_start: slice_finish]
        actual_roll = db[slice_finish + 1]
        bb, br, bw = calc_bets_based_on_db_slice(db_slice)
        gain, loss = 0, 0
        money_to_bet = max(min(money, params.MAX_BET), params.STOP_LOSS)
        if actual_roll == "black":
            gain = bb * money_to_bet
            loss = br * money_to_bet + bw * money_to_bet
        if actual_roll == "red":
            gain = br * money_to_bet
            loss = bb * money_to_bet + bw * money_to_bet
        if actual_roll == "white":
            gain = bw * money_to_bet * (params.PROPORTION_OF_WIN_WHITE - 1)
            loss = bb * money_to_bet + br * money_to_bet
        money += gain
        money -= loss
        print(gain > loss, gain, loss, money)
        print(" -> actual roll: ", actual_roll , " | black:", bb * money_to_bet, "red: ", br * money_to_bet, "white: ", bw * money_to_bet)
        wins += int(gain > loss)
        total_wins += int(gain > loss)
        if slice_start % 30 == 0:
            print(f"wins: {wins}/30 (total: {total_wins}/{total_bets}):")
            wins = 0
        slice_start += 1
        slice_finish += 1
        total_bets += 1
    return money, total_wins, total_bets, (float(total_wins)/total_bets if total_bets > 0 else 0)

def main():
    db = read_db()
    print(f"Simulando com {len(db)} entradas")
    print(simulate_based_on_db(db))

if __name__ == "__main__":
    main()
