from log import log
from telethon import functions


async def subscribe_channel(user_client, channel):
    log(f"Subscribing to channel: {channel.title} {channel.id}")
    await user_client(functions.channels.JoinChannelRequest(channel))


async def unsubscribe_channel(user_client, channel):
    log(f"Unsubscribing from channel: {channel.title} {channel.id}")
    await user_client(functions.channels.LeaveChannelRequest(channel))
