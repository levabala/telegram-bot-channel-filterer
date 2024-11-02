from log import log
import consts
import channel_utils
import db_bot_list as db_bot_list_module


class Command:
    def __init__(self, name, description, handler):
        self.name = name
        self.description = description
        self.handler = handler


async def initBotCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    await event.reply("Initializing bot")

    if bot is not None:
        await event.reply("Bot already initialized")
        return

    bot_config = db_bot_list_module.BotConfig(
        bot_key, f"{consts.DB_DIRECTORY}/user_bot_{sender_username}.db"
    )
    dialogs = await user_client.get_dialogs()
    start_bot(bot_config, dialogs)

    await event.reply(f"Bot `{bot_config.name}` created")


initBotCommand = Command(
    "/initbot",
    "Initialize bot",
    initBotCommandHandler,
)


async def addChannelCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    try:
        channel_username = message.split(" ")[1]
    except IndexError:
        await event.reply("Channel username not specified")
        return

    if channel_username in bot.channels_usernames_to_watch:
        await event.reply(f"Channel {channel_username} is already watched")
        return

    log(f"Adding channel {channel_username}")
    try:
        channel_entity = await user_client.get_entity("@" + channel_username)
    except Exception as e:
        log(f"Error adding channel {channel_username}", e)
        await event.reply("Channel not found")
        return

    await channel_utils.subscribe_channel(user_client, channel_entity)
    bot.add_channel_to_watch(channel_entity)

    await event.reply(f"Channel {channel_username} added")


addChannelCommand = Command(
    "/addchannel",
    "Add channel to watch",
    addChannelCommandHandler,
)


async def deleteChannelCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    channel_username = message.split(" ")[1]
    log(f"Deleting channel {channel_username}")

    if channel_username not in bot.channels_usernames_to_watch:
        await event.reply(f"Channel {channel_username} is not watched")
        return

    try:
        channel_entity = await user_client.get_entity("@" + channel_username)
    except Exception:
        log(f"Error deleting channel {channel_username}")
        await event.reply("Channel not found")
        return

    await channel_utils.unsubscribe_channel(user_client, channel_entity)
    bot.remove_channel_to_watch(channel_entity)

    await event.reply(f"Channel {channel_username} deleted")


deleteChannelCommand = Command(
    "/deletechannel",
    "Delete channel to watch",
    deleteChannelCommandHandler,
)


async def listChannelsCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    if len(bot.channels_watched) == 0:
        await event.reply("No channels")
        return

    list_str = "\n".join(
        [
            f"{channel.title} - {channel.username}"
            for channel in bot.channels_watched
        ]
    )
    await event.reply(list_str)


listChannelsCommand = Command(
    "/listchannels",
    "List channels to watch",
    listChannelsCommandHandler,
)


async def setChannelMessageFilterCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    try:
        channel_username = message.split(" ")[1]
        filter_regex = " ".join(message.split(" ")[2:])
    except IndexError:
        await event.reply("Channel username and filter regex not specified")
        return

    if channel_username not in [c.username for c in bot.channels_watched]:
        await event.reply(f"Channel {channel_username} not watched")
        return

    bot.set_channel_message_filter(channel_username, filter_regex)
    await event.reply(
        f"Filter `{filter_regex}` for channel {channel_username} set"
    )


setChannelMessageFilterCommand = Command(
    "/setchannelfilter",
    "Set channel message filter",
    setChannelMessageFilterCommandHandler,
)


async def listChannelFiltersCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    if len(bot.channel_username_to_message_filter) == 0:
        await event.reply("No filters")
        return

    list_str = "\n".join(
        [
            f"{channel_username}: `{filter_regex}`"
            for channel_username, filter_regex in bot.channel_username_to_message_filter.items()
        ]
    )
    await event.reply(list_str)


listChannelFiltersCommand = Command(
    "/listchannelfilters",
    "List channel message filters",
    listChannelFiltersCommandHandler,
)


async def addChannelToForwardToCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    try:
        channel_username = message.split(" ")[1]
    except IndexError:
        await event.reply("Channel username not specified")
        return

    if channel_username in bot.forward_channel_target_usernames:
        await event.reply(
            f"Channel {channel_username} is already set up to forward to"
        )
        return

    log(f"Adding channel to forward to{channel_username}")
    try:
        channel_entity = await user_client.get_entity("@" + channel_username)
    except Exception as e:
        log(f"Error adding channel {channel_username}", e)
        await event.reply("Channel not found")
        return

    bot.add_channel_to_forward_to(channel_username)
    await event.reply(f"Channel {channel_username} added")


addChannelToForwardToCommand = Command(
    "/addchannelforwardto",
    "Add channel to forward to",
    addChannelToForwardToCommandHandler,
)


async def removeChannelToForwardToCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    try:
        channel_username = message.split(" ")[1]
    except IndexError:
        await event.reply("Channel username not specified")
        return

    if channel_username not in bot.forward_channel_target_usernames:
        await event.reply(
            f"Channel {channel_username} is not set up to forward to"
        )
        return

    log(f"Removing channel to forward to{channel_username}")
    try:
        channel_entity = await user_client.get_entity("@" + channel_username)
    except Exception:
        log(f"Error deleting channel {channel_username}")
        await event.reply("Channel not found")
        return

    bot.remove_channel_to_forward_to(channel_username)
    await event.reply(f"Channel {channel_username} deleted")


removeChannelToForwardToCommand = Command(
    "/removechannelforwardto",
    "Remove channel to forward to",
    removeChannelToForwardToCommandHandler,
)


async def listChannelsToForwardToCommandHandler(
    event, message, user_client, start_bot, sender_username, bot, bot_key
):
    if len(bot.forward_channel_target_usernames) == 0:
        await event.reply("No channels")
        return

    list_str = "\n".join(
        [
            f"{channel_username}"
            for channel_username in bot.forward_channel_target_usernames
        ]
    )
    await event.reply(list_str)


listChannelsToForwardToCommand = Command(
    "/listchannelsforwardto",
    "List channels to forward to",
    listChannelsToForwardToCommandHandler,
)

commands_dict = {
    "initbot": initBotCommand,
    "addchannel": addChannelCommand,
    "deletechannel": deleteChannelCommand,
    "listchannels": listChannelsCommand,
    "setchannelfilter": setChannelMessageFilterCommand,
    "listchannelfilters": listChannelFiltersCommand,
    "addchannelforwardto": addChannelToForwardToCommand,
    "removechannelforwardto": removeChannelToForwardToCommand,
    "listchannelsforwardto": listChannelsToForwardToCommand,
}
