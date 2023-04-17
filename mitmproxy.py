from mitmproxy import http
import redis
import datetime
import logging
import json
import sqlite3


class WebSocketDataCapture:

    def __init__(self):
        self.db = self._setup_db()
        self.redis = self._setup_redis()

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
        CREATE TABLE IF NOT EXISTS bets(id PRIMARY KEY, started_at, color, roll)
        '''
        cur.execute(create_table)
        return db

    def _setup_redis(self):
        r = redis.Redis(host="localhost", port=6379, db=0)
        return r

    def _add_bet(self, id, started_at, color, roll) -> bool:
        data = (id, started_at, color, roll)
        cur = self.db.cursor()
        cur.execute("INSERT OR IGNORE INTO bets(id, started_at, color, roll) VALUES (?,?,?,?)", data)
        self.db.commit()
        return cur.rowcount > 0

    def _process_message_if_necessary(self, pretty_url: str, message: str) -> None:
        if "arbety.eway.dev" not in pretty_url:
            return
        if message.startswith("42"):  # socket.io protocol
            stripped_message = message[2:]
            try:
                parsed_message = json.loads(stripped_message)
            except json.JSONDecodeError:
                return
            if len(parsed_message) > 0:
                if parsed_message[0] == "double":
                    self._process_double_message(parsed_message)
                if parsed_message[0] == "double.history":
                    self._process_double_history_message(parsed_message)

    def _process_double_message(self, parsed_message):
        if "color" not in parsed_message[1]:
            return
        roll = parsed_message[1]["roll"]
        if roll is None:
            return
        id = parsed_message[1]["id"]
        color = parsed_message[1]["color"]
        started_at = int(int(parsed_message[1]["startedAt"])/1000.0)
        logging.info("Color: %s, Roll: %s, Started at: %s" % (color, roll, started_at))
        new_entry = self._add_bet(id, started_at, color, roll)
        if new_entry:
            self._notify_new_entry(id, started_at, color, roll)

    def _process_double_history_message(self, parsed_message):
        logging.info("Processing history...")
        entries_processed = 0
        for entry in parsed_message[1]:
            id = entry["id"]
            started_at = int(datetime.datetime.fromisoformat(entry["startedAt"]).timestamp())
            color = entry["color"]
            roll = entry["roll"]
            new_entry = self._add_bet(id, started_at, color, roll)
            if new_entry:
                self._notify_new_entry(id, started_at, color, roll)
                entries_processed += 1
        logging.info("Entries processed: %s", entries_processed)

    def _notify_new_entry(self, id, started_at, color, roll) -> None:
        new_entry = (id, started_at, color, roll)
        self.redis.rpush("arbety.bets", json.dumps(new_entry))

addons = [WebSocketDataCapture()]
