from mitmproxy import http
import logging
import json
import sqlite3


class WebSocketDataCapture:

    def __init__(self):
        self.db = self._setup_db()

    def response(self, flow) -> None:
        self._process_message_if_necessary(
            flow.request.pretty_url,
            flow.response.text,
        )

    def websocket_message(self, flow) -> None:
        message = flow.websocket.messages[-1]
        if not message.is_text:
            return
        text = message.text
        self._process_message_if_necessary(
            flow.request.pretty_url,
            text,
        )

    def _setup_db(self) -> sqlite3.Connection:
        db = sqlite3.connect("bets.db")
        cur = db.cursor()
        create_table = '''
        CREATE TABLE IF NOT EXISTS bets(started_at PRIMARY KEY, color, roll)
        '''
        cur.execute(create_table)
        return db

    def _add_bet(self, started_at, color, roll) -> bool:
        data = (started_at, color, roll)
        cur = self.db.cursor()
        cur.execute("INSERT OR IGNORE INTO bets(started_at, color, roll) VALUES (?,?,?)", data)
        self.db.commit()
        return cur.rowcount > 0

    def _process_message_if_necessary(self, pretty_url: str, message: str) -> None:
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
                new_entry = self._add_bet(started_at, color, roll)
                if new_entry:
                    self._notify_new_entry(started_at, color, roll)

    def _notify_new_entry(self, started_at, color, roll) -> None:
        pass

addons = [WebSocketDataCapture()]
