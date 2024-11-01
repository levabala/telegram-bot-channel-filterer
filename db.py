import sqlite3


def add_channel_to_watch(channel_username):
    con = get_db_connection()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO channels_usernames_to_watch (username) VALUES (?)",
        (channel_username,),
    )
    con.commit()
    con.close()

    print(f"Added channel {channel_username} to watch")


def set_channel_message_filter(channel_username, filter_regex):
    con = get_db_connection()
    cur = con.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO channel_to_message_filter (username, filter) VALUES (?, ?)",
        (channel_username, filter_regex),
    )
    con.commit()
    con.close()

    print(f"Set filter {filter_regex} for channel {channel_username}")


def set_channel_forward_targets(channel_username, filter_regex):
    con = get_db_connection()
    cur = con.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO channel_to_message_filter (username, filter) VALUES (?, ?)",
        (channel_username, filter_regex),
    )
    con.commit()
    con.close()

    print(f"Set filter {filter_regex} for channel {channel_username}")


def get_db_connection():
    con = sqlite3.connect("channels.db")

    return con


def setup_db():
    print("Setting up db")
    con = get_db_connection()
    cur = con.cursor()

    cur.execute(
        "CREATE TABLE IF NOT EXISTS channels_usernames_to_watch (username TEXT PRIMARY KEY)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS channel_to_message_filter (username TEXT PRIMARY KEY, filter TEXT)"
    )

    con.close()
    print("Done setting up db")


def read_db_to_local_state():
    print("Reading db to local state")
    con = get_db_connection()
    cur = con.cursor()

    resUsernamesToWatch = cur.execute(
        "SELECT username FROM channels_usernames_to_watch"
    ).fetchall()

    channels_usernames_to_watch = [row[0] for row in resUsernamesToWatch]

    resFilters = cur.execute(
        "SELECT username, filter FROM channel_to_message_filter"
    ).fetchall()

    channel_username_to_message_filter = {row[0]: row[1] for row in resFilters}

    con.close()
    print("Done reading db to local state")

    print(f"Channels to watch: {channels_usernames_to_watch}")
    print(f"Channel filters: {channel_username_to_message_filter}")

    return channels_usernames_to_watch, channel_username_to_message_filter
