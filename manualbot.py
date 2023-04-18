import sys
import sqlite3
import redis
import json
from kelly_criterion import calc_bets_based_on_db_slice, read_db


db = redis.Redis(host="localhost", port=6379, db=0)
db.delete("arbety.bets")  # exclui bets antigos
bets_db = read_db()
db_slice = bets_db[len(bets_db)-30:]   # apenas os últimos 30 bets. assume continuidade
# TODO: verificar se os últimos 30 estão contíguos

# Parâmetros:
money = 100
max_bet = 500

while money > 10:
    bb, br, bw = calc_bets_based_on_db_slice(db_slice)
    money_to_bet = min(money, max_bet)
    print("Quanto apostar: black:", int(bb * money_to_bet), " red: ", int(br * money_to_bet))
    # aguarda próximo bet
    _, raw_bet = db.blpop("arbety.bets")
    bet = json.loads(raw_bet.decode("utf-8"))
    print("Deu:", bet[2])
    gain, loss = 0, 0
    actual_roll = bet[2]
    if actual_roll == "black":
        gain = int(bb * money_to_bet) * 2  # TODO: nem sempre será x2. Pegar dados para saber quanto ganhamos
        loss = int(br * money_to_bet) + int(bw * money_to_bet)
    if actual_roll == "red":
        gain = int(br * money_to_bet) * 2
        loss = int(bb * money_to_bet) + int(bw * money_to_bet)
    if actual_roll == "white":
        gain = 0  # Não apostamos em brancas (ainda)
        loss = int(bb * money) + int(br * money)
    money += gain
    money -= loss
    print("Ganhamos ", gain, ". Perdemos ", loss, ". Saldo: ", money)
    db_slice.append(bet[2])
    db_slice = db_slice[1:]
    print("-"*30)
