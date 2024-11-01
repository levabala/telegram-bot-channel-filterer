import os
import asyncio
import commands as commands_module
import bot as bot_module
import db_bot_list as db_bot_list_module
import consts
from telethon import TelegramClient
from telethon import functions, events, types


api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

admin_usernames = os.environ.get("ADMIN_USERNAME").split(",")

print(f"Admin usernames: {admin_usernames}")

assert api_id is not None and len(api_id) > 0, "API_ID must be set"
assert api_hash is not None and len(api_hash) > 0, "API_HASH must be set"
assert bot_token is not None and len(bot_token) > 0, "BOT_TOKEN must be set"
assert len(admin_usernames) > 0, "ADMIN_USERNAME must be set"

user_client = TelegramClient("session_name", api_id, api_hash)
bot_client = TelegramClient("bot", api_id, api_hash)

if not os.path.exists(consts.DB_DIRECTORY):
    os.makedirs(consts.DB_DIRECTORY)

print(f"{consts.DB_DIRECTORY}/bots.db")

db_bot_list = db_bot_list_module.DBBotList(f"{consts.DB_DIRECTORY}/bots.db")
db_bot_list.setup_db()

bot_list = db_bot_list.get_bots_list()

print(f"Bots list: {bot_list}")


routines_to_run = []
bots = {}


def get_bot_key(sender_username):
    return f"{sender_username}'s minion"


async def start_bot(bot_config, dialogs):
    print(f"Starting bot {bot_config.name}")

    bot = bot_module.Bot(bot_config.name, bot_config.db_name, user_client)

    bots[bot_config.name] = bot

    already_initialized = bot_config in db_bot_list.get_bots_list()
    if not already_initialized:
        db_bot_list.add_bot(bot_config)

    await bot.init(dialogs)
    routines_to_run.append(
        asyncio.create_task(user_client.run_until_disconnected())
    )


commands_list = commands_module.commands_dict.values()
commands = commands_module.commands_dict


async def set_commands():
    bot_commands = [
        types.BotCommand(
            command.name[1:],
            command.description,
        )
        for command in commands_list
    ]

    print(f"Bot commands count: {len(bot_commands)}")

    await bot_client(
        functions.bots.SetBotCommandsRequest(
            scope=types.BotCommandScopeDefault(),
            lang_code="en",
            commands=bot_commands,
        )
    )


async def bot_message_handler(event):
    sender = await event.get_sender()
    message = event.message.message
    sender_username = sender.username

    print(f"New message from {sender_username}: {message}")

    if sender.username not in admin_usernames:
        await event.reply("hui")
        return

    bot_key = get_bot_key(sender_username)
    bot = bots.get(bot_key)

    args = [
        event,
        message,
        user_client,
        start_bot,
        sender_username,
        bot,
        bot_key,
    ]

    try:
        message_command = message.split(" ")[0]
        if message_command == commands["initbot"].name:
            await commands["initbot"].handler(*args)
            return

        if bot is None:
            await event.reply("no bot exists for you")
            return

        print(f"Processed by: {bot.name}")

        for command in commands_list:
            if message_command == command.name:
                await command.handler(*args)
                return

        await event.reply("Unknown command")
    except Exception as e:
        print(f"Error handling command {message}")
        await event.reply("Error handling command")

        raise e


async def run_bots():
    global routines_to_run

    await user_client.start()
    await bot_client.start(bot_token=bot_token)

    await set_commands()

    bot_client.add_event_handler(bot_message_handler, events.NewMessage)

    dialogs = await user_client.get_dialogs()

    channels = [dialog.entity for dialog in dialogs if dialog.is_channel]
    for channel in channels:
        print(
            f"Channel: {channel.title} - "
            f"Username: {channel.username} - "
            f"ID: {channel.id}"
        )

    try:
        routines_to_run.append(
            asyncio.create_task(bot_client.run_until_disconnected())
        )

        for bot_config in bot_list:
            await start_bot(bot_config, dialogs)

        print("Bots initialized")
        print(f"Bots: {bots}")

        while routines_to_run:
            temp = routines_to_run
            routines_to_run = []

            await asyncio.gather(*temp)
    finally:
        await user_client.disconnect()
        await bot_client.disconnect()


asyncio.run(run_bots())
