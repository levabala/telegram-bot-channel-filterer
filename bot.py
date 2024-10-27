import sqlite3
import os
import re
import asyncio
from telethon import TelegramClient
from telethon import functions, events

api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

admin_username = os.environ.get("ADMIN_USERNAME")

channels_usernames_to_watch = []
channels_watched = []

channel_username_to_message_filter = {}

forward_to_username = "levabalasfeed"

assert api_id is not None and len(api_id) > 0, "API_ID must be set"
assert api_hash is not None and len(api_hash) > 0, "API_HASH must be set"
assert bot_token is not None and len(bot_token) > 0, "BOT_TOKEN must be set"
assert (
    admin_username is not None and len(admin_username) > 0
), "ADMIN_USERNAME must be set"

user_client = TelegramClient("session_name", api_id, api_hash)
bot_client = TelegramClient("bot", api_id, api_hash)


async def user_message_handler(event):
    print(f"New message in channel: {event.message.message}")

    channel = await user_client.get_entity(event.message.peer_id)
    filter_regex = channel_username_to_message_filter.get(channel.username)

    if filter_regex and re.search(
        filter_regex,
        event.message.message,
    ):
        print("forwarding...")
        channel_destination = await user_client.get_entity(
            "@" + forward_to_username
        )
        print("forwarding to", channel_destination.username)

        await user_client.forward_messages(
            channel_destination, event.message.id, event.message.peer_id
        )


async def bot_message_handler(event):
    sender = await event.get_sender()
    message = event.message.message
    print(f"New message from {sender.username}: {message}")

    if sender.username != admin_username:
        await event.reply("hui")
        return

    if message.startswith("/addchannel"):
        try:
            channel_username = message.split(" ")[1]
        except IndexError:
            await event.reply("Channel username not specified")

        print(f"Adding channel {channel_username}")
        try:
            channel_entity = await user_client.get_entity(
                "@" + channel_username
            )
        except Exception as e:
            print(f"Error adding channel {channel_username}", e)
            await event.reply("Channel not found")
            return

        await subscribe_channel(channel_entity)
        listen_to_channel(channel_entity)
        add_channel_to_watch(channel_username)

        await event.reply(f"Channel {channel_username} added")
    elif message.startswith("/deletechannel"):
        channel_username = message.split(" ")[1]
        print(f"Deleting channel {channel_username}")
        try:
            channel_entity = await user_client.get_entity(
                "@" + channel_username
            )
        except Exception:
            print(f"Error deleting channel {channel_username}")
            await event.reply("Channel not found")
            return

        await unsubscribe_channel(channel_entity)
        stop_listening_to_channel(channel_entity)

        await event.reply(f"Channel {channel_username} deleted")
    elif message.startswith("/listchannels"):
        list_str = "\n".join(
            [
                f"{channel.title} - {channel.username}"
                for channel in channels_watched
            ]
        )
        await event.reply(list_str)
    elif message.startswith("/setchannelfilter"):
        try:
            channel_username = message.split(" ")[1]
            filter_regex = " ".join(message.split(" ")[2:])
        except IndexError:
            await event.reply(
                "Channel username and filter regex not specified"
            )
            return

        set_channel_message_filter(channel_username, filter_regex)
        await event.reply(
            f"Filter `{filter_regex}` for channel {channel_username} set"
        )
    elif message.startswith("/listchannelfilters"):
        list_str = "\n".join(
            [
                f"{channel_username}: `{filter_regex}`"
                for channel_username, filter_regex in channel_username_to_message_filter.items()
            ]
        )
        await event.reply(list_str)
    else:
        await event.reply("Unknown command")


async def subscribe_channel(channel):
    print(f"Subscribing to channel: {channel.title} {channel.id}")
    await user_client(functions.channels.JoinChannelRequest(channel))


async def unsubscribe_channel(channel):
    print(f"Unsubscribing from channel: {channel.title} {channel.id}")
    await user_client(functions.channels.LeaveChannelRequest(channel))


def listen_to_channel(channel):
    print(f"Listening to channel: {channel.title} {channel.id}")
    user_client.add_event_handler(
        user_message_handler, events.NewMessage(chats=channel.id)
    )
    channels_watched.append(channel)


def stop_listening_to_channel(channel):
    print(f"Stopping listening to channel: {channel.title} {channel.id}")
    user_client.remove_event_handler(
        user_message_handler, events.NewMessage(chats=channel.id)
    )
    channels_watched.remove(channel)


def add_channel_to_watch(channel_username):
    print(f"Adding channel {channel_username} to watch")
    channels_usernames_to_watch.append(channel_username)

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
    print(f"Setting filter {filter_regex} for channel {channel_username}")
    channel_username_to_message_filter[channel_username] = filter_regex

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

    channels_usernames_to_watch
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

    global channels_usernames_to_watch
    channels_usernames_to_watch = [row[0] for row in resUsernamesToWatch]

    resFilters = cur.execute(
        "SELECT username, filter FROM channel_to_message_filter"
    ).fetchall()

    global channel_username_to_message_filter
    channel_username_to_message_filter = {row[0]: row[1] for row in resFilters}

    con.close()
    print("Done reading db to local state")

    print(f"Channels to watch: {channels_usernames_to_watch}")
    print(f"Channel filters: {channel_username_to_message_filter}")


async def main():
    dialogs = await user_client.get_dialogs()

    channels = [dialog.entity for dialog in dialogs if dialog.is_channel]
    for channel in channels:
        print(
            f"Channel: {channel.title} - "
            f"Username: {channel.username} - "
            f"ID: {channel.id}"
        )

    channels_usernames_subscribed = [channel.username for channel in channels]

    print("channels usernames subscribed: ", channels_usernames_subscribed)

    channels_to_subscribe_usernames = [
        channel_username
        for channel_username in channels_usernames_to_watch
        if channel_username not in channels_usernames_subscribed
    ]

    print("to subscribe wanted: ", channels_usernames_to_watch)
    print("to subscribe now: ", channels_to_subscribe_usernames)

    channels_to_subscribe_inputs = [
        await user_client.get_entity("@" + id)
        for id in channels_to_subscribe_usernames
    ]

    print("inputs: ", channels_to_subscribe_inputs)

    for channel in channels_to_subscribe_inputs:
        await subscribe_channel(channel)

    channels_to_listen = [
        channel
        for channel in channels
        if channel.username in channels_usernames_to_watch
    ] + channels_to_subscribe_inputs

    print("channels to listen: ", channels_to_listen)

    for channel in channels_to_listen:
        listen_to_channel(channel)

    print("setup done")


async def run_both_clients():
    await user_client.start()
    await bot_client.start(bot_token=bot_token)

    bot_client.add_event_handler(bot_message_handler, events.NewMessage)

    try:
        setup_db()
        read_db_to_local_state()

        await asyncio.gather(
            main(),
            user_client.run_until_disconnected(),
            # bot_client.run_until_disconnected(),
        )
    finally:
        await user_client.disconnect()
        await bot_client.disconnect()


asyncio.run(run_both_clients())
