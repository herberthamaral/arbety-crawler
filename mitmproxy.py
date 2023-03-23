from mitmproxy import http
import logging
import json
import sqlite3


def setup_db():
    db = sqlite3.connect("bets.db")
    cur = db.cursor()
    create_table = '''
    CREATE TABLE IF NOT EXISTS bets(started_at PRIMARY KEY, color, roll)
    '''
    cur.execute(create_table)
    return db

def add_bet(db, started_at, color, roll):
    data = (started_at, color, roll)
    cur = db.cursor()
    cur.execute("INSERT OR IGNORE INTO bets(started_at, color, roll) VALUES (?,?,?)", data)
    db.commit()

def process_message_if_necessary(db, pretty_url: str, message: str) -> None:
    if "arbety.eway.dev" not in pretty_url:
        return
    logging.info("Processing message")
    if message.startswith("42"):  # socket.io protocol
        stripped_message = message[2:]
        parsed_message = json.loads(stripped_message)
        if len(parsed_message) > 0 and parsed_message[0] == "double":
            if "color" not in parsed_message[1]:
                return
            roll = parsed_message[1]["roll"]
            if roll is None:
                return
            color = parsed_message[1]["color"]
            started_at = parsed_message[1]["startedAt"]
            logging.info("Color: %s, Roll: %s, Started at: %s" % (color, roll, started_at))
            add_bet(db, started_at, color, roll)


class WebSocketDataCapture:

    def __init__(self):
        self.db = setup_db()

    def response(self, flow):
        process_message_if_necessary(
            self.db,
            flow.request.pretty_url,
            flow.response.text,
        )

    def websocket_message(self, flow: http.HTTPFlow):
        message = flow.websocket.messages[-1]
        if not message.is_text:
            return
        text = message.text
        process_message_if_necessary(
            self.db, 
            flow.request.pretty_url,
            text,
        )

addons = [WebSocketDataCapture()]
