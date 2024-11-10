from log import log
import sqlite3
from collections import namedtuple

ReactionsRecord = namedtuple(
    "ReactionsRecord", "username message_id range_seconds count"
)


class DBReactions:
    def __init__(self, db_name):
        self.db_name = db_name

    def get_db_connection(self):
        con = sqlite3.connect(self.db_name)

        return con

    def setup_db(self):
        log("Setting up db reactions")
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reactions (
                username TEXT PRIMARY KEY,
                message_id INTEGER PRIMARY KEY,
                range_seconds INTEGER PRIMARY KEY,
                count INTEGER
            )"""
        )

        con.close()
        log("Done setting up db reactions")

    def add_reaction(self, reactionsRecord: ReactionsRecord):
        con = self.get_db_connection()
        cur = con.cursor()

        username, message_id, range_seconds, count = reactionsRecord

        cur.execute(
            "INSERT OR REPLACE INTO reactions (username, message_id, range_seconds, count) VALUES (?, ?, ?, ?)",
            (
                username,
                message_id,
                range_seconds,
                count,
            ),
        )
        con.commit()
        con.close()

        log(f"Added reaction {username} {message_id} {range_seconds} {count}")

    def get_reactions(self, username, range_seconds):
        con = self.get_db_connection()
        cur = con.cursor()

        res = cur.execute(
            "SELECT count FROM reactions WHERE username = ? AND range_seconds = ?",
            (username, range_seconds),
        ).fetchall()

        con.close()

        return [row[0] for row in res]
