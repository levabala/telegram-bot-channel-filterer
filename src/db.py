from log import log
import sqlite3


class DB:
    def __init__(self, db_name):
        self.db_name = db_name + ".db"

    def add_channel_to_watch(self, channel_username):
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "INSERT INTO channels_usernames_to_watch (username) VALUES (?)",
            (channel_username,),
        )
        con.commit()
        con.close()

        log(f"Added channel {channel_username} to watch")

    def remove_channel_to_watch(self, channel_username):
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "DELETE FROM channels_usernames_to_watch WHERE username = ?",
            (channel_username,),
        )
        con.commit()
        con.close()

        log(f"Removed channel {channel_username} to watch")

    def set_channel_message_filter(self, channel_username, filter_regex):
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "INSERT OR REPLACE INTO channel_to_message_filter (username, filter) VALUES (?, ?)",
            (channel_username, filter_regex),
        )
        con.commit()
        con.close()

        log(f"Set filter {filter_regex} for channel {channel_username}")

    def add_channel_forward_target(self, channel_username):
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "INSERT OR REPLACE INTO forward_target_usernames (username) VALUES (?)",
            (channel_username,),
        )
        con.commit()
        con.close()

        log(f"Added channel {channel_username} to forward to")

    def remove_channel_forward_target(self, channel_username):
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "DELETE FROM forward_target_usernames WHERE username = ?",
            (channel_username,),
        )
        con.commit()
        con.close()

        log(f"Removed channel {channel_username} to forward to")

    def update_channel_reactions_threshold(
        self, channel_username, threshold
    ):
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "INSERT OR REPLACE INTO channel_to_reactions_threshold (username, threshold) VALUES (?, ?)",
            (channel_username, threshold),
        )
        con.commit()
        con.close()

        log(
            f"Updated reactions threshold {threshold} for channel {channel_username}"
        )

    def get_db_connection(self):
        con = sqlite3.connect(self.db_name)

        return con

    def setup_db(self):
        log("Setting up db")
        con = self.get_db_connection()
        cur = con.cursor()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS channels_usernames_to_watch (username TEXT PRIMARY KEY)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS channel_to_message_filter (username TEXT PRIMARY KEY, filter TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS forward_target_usernames (username TEXT PRIMARY KEY)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS channel_to_reactions_threshold (username TEXT PRIMARY KEY, threshold INTEGER)"
        )

        con.close()
        log("Done setting up db")

    def read_db(self):
        log("Reading db to local state")
        con = self.get_db_connection()
        cur = con.cursor()

        resUsernamesToWatch = cur.execute(
            "SELECT username FROM channels_usernames_to_watch"
        ).fetchall()

        channels_usernames_to_watch = [row[0] for row in resUsernamesToWatch]

        resFilters = cur.execute(
            "SELECT username, filter FROM channel_to_message_filter"
        ).fetchall()

        channel_username_to_message_filter = {
            row[0]: row[1] for row in resFilters
        }

        resForwardTargets = cur.execute(
            "SELECT username FROM forward_target_usernames"
        ).fetchall()

        forward_channel_target_usernames = [
            row[0] for row in resForwardTargets
        ]

        resReactionsThresholds = cur.execute(
            "SELECT username, threshold FROM channel_to_reactions_threshold"
        ).fetchall()

        channel_username_to_reactions_threshold = {
            row[0]: row[1] for row in resReactionsThresholds
        }

        con.close()
        log("Done reading db to local state")

        return (
            channels_usernames_to_watch,
            channel_username_to_message_filter,
            forward_channel_target_usernames,
            channel_username_to_reactions_threshold,
        )
