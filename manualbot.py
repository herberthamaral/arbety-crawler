import sys
import redis
import json
from kelly_criterion import calc_bets_based_on_db_slice


db = redis.Redis(host="localhost", port=6379, db=0)
bets = []
print("Carregando histórico de bets")
for _ in range(30):
    _, raw_bet = db.blpop("arbety.bets")
    bet = json.loads(raw_bet.decode("utf-8"))
    bets.append(bet)
    sys.stdout.write(".")
    sys.stdout.flush()
print()
# TODO: verificar se os últimos 30 estão em sequencia ou se tem gap
while True:
    money = 100
    db_slice = [b[3] for b in bets]
    bb, br, bw = calc_bets_based_on_db_slice(db_slice)
    print("Quanto apostar: black:", bb * money, " red: ", br * money)
    # aguarda próximo bet
    _, raw_bet = db.blpop("arbety.bets")
    bet = json.loads(raw_bet.decode("utf-8"))
    gain, loss = 0, 0
    actual_roll = bet["color"]
    if actual_roll == "black":
        gain = bb * money_to_bet * 2  # TODO: nem sempre será x2. Pegar dados para saber quanto ganhamos
        loss = br * money_to_bet + bw * money_to_bet
    if actual_roll == "red":
        gain = br * money_to_bet * 2
        loss = bb * money_to_bet + bw * money_to_bet
    if actual_roll == "white":
        gain = 0  # Não apostamos em brancas (ainda)
        loss = bb * money_to_bet + br * money_to_bet
    money += gain
    money -= loss
    print("Ganhamos ", gain, ". Perdemos ", loss, ". Saldo: ", money)
    bets.append([bet["id"], 0, bet["color"], bet["roll"]])
    bets = bets[1:]
