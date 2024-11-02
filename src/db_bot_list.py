from log import log
from collections import namedtuple
import sqlite3

BotConfig = namedtuple("BotConfig", "name db_name")


class DBBotList:
    def __init__(self, db_name):
        self.db_name = db_name

    def get_db_connection(self):
        con = sqlite3.connect(self.db_name)

        return con

    def setup_db(self):
        log("Setting up db bot list")
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS bots (name TEXT PRIMARY KEY, db_name TEXT)"
        )

        con.close()
        log("Done setting up db bot list")

    def get_bots_list(self):
        con = self.get_db_connection()
        cur = con.cursor()

        bots = cur.execute("SELECT name, db_name FROM bots")

        return [BotConfig(name, db_name) for name, db_name in bots]

    def add_bot(self, bot_config):
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "INSERT INTO bots (name, db_name) VALUES (?, ?)",
            (bot_config.name, bot_config.db_name),
        )
        con.commit()
        con.close()

        log(f"Added bot {bot_config.name} to db bot list")
