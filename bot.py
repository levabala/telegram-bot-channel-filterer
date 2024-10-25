import os
import re
from telethon import TelegramClient
from telethon import functions, events

api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")

channels_usernames_to_watch = ["svtvnews", "mytestchannel228228"]

message_filter = "Что случилось.*самое важное"

forward_to_username = "levabalasfeed"

assert api_id is not None and len(api_id) > 0, "API_ID must be set"
assert api_hash is not None and len(api_hash) > 0, "API_HASH must be set"

client = TelegramClient("session_name", api_id, api_hash)


async def handler(event):
    print(f"New message in channel: {event.message.message}")
    if re.search(message_filter, event.message.message):
        print("forwarding...", event.message)
        channel_destination = await client.get_entity(
            "@" + forward_to_username
        )
        await client.forward_messages(
            channel_destination, event.message.id, event.message.peer_id
        )


async def main():
    dialogs = await client.get_dialogs()

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

    print("to subscribe: ", channels_to_subscribe_usernames)

    channels_to_subscribe_inputs = [
        await client.get_entity("@" + id)
        for id in channels_to_subscribe_usernames
    ]

    print("inputs: ", channels_to_subscribe_inputs)

    for channel in channels_to_subscribe_inputs:
        print(f"Subscribing to channel: {channel.title} {channel.id}")
        await client(functions.channels.JoinChannelRequest(channel))

    channels_to_listen = [
        channel
        for channel in channels
        if channel.username in channels_usernames_to_watch
    ] + channels_to_subscribe_inputs

    for channel in channels_to_listen:
        client.add_event_handler(handler, events.NewMessage(chats=channel.id))

    await client.run_until_disconnected()


client.start()
client.loop.run_until_complete(main())
