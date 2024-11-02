from log import log
import re
import channel_utils
import db as db_module
from telethon import events

bots = []


async def handle_user_message_for_bots(event):
    for bot in bots:
        log(
            f"{bot.name}|{event.message.peer_id.channel_id}|{[c.id for c in bot.channels_watched]}"
        )
        if event.message.peer_id.channel_id in [
            c.id for c in bot.channels_watched
        ]:
            log("YES")
            await bot.user_message_handler(event)


class Bot:
    def __init__(self, name, db_name, user_client):
        self.channels_usernames_to_watch = []
        self.channels_watched = []
        self.forward_channel_target_usernames = []
        self.channel_username_to_message_filter = {}

        self.user_client = user_client
        self.name = name
        self.db = db_module.DB(db_name)
        self.db.setup_db()

        (
            channels_usernames_to_watch,
            channel_username_to_message_filter,
            forward_channel_target_usernames,
        ) = self.db.read_db()
        self.channels_usernames_to_watch = channels_usernames_to_watch
        self.channel_username_to_message_filter = (
            channel_username_to_message_filter
        )
        self.forward_channel_target_usernames = (
            forward_channel_target_usernames
        )

        log(f"Bot created {name}")
        bots.append(self)
        log([b.name for b in bots])

        log(f"Channels to watch: {self.channels_usernames_to_watch}")
        log(f"Channel filters: {self.channel_username_to_message_filter}")
        log(
            f"Channel to forward to: {self.forward_channel_target_usernames}"
        )

    async def user_message_handler(self, event):
        channel = await self.user_client.get_entity(event.message.peer_id)

        log(
            f"New message in `{channel.username}`: {event.message.message[:100]}"
        )

        filter_regex = self.channel_username_to_message_filter.get(
            channel.username
        )

        log(f"Test against filter {filter_regex}")

        if filter_regex and re.search(
            filter_regex,
            event.message.message,
        ):
            log("forwarding to", self.forward_channel_target_usernames)

            for (
                forward_channel_target_username
            ) in self.forward_channel_target_usernames:
                channel_destination = await self.user_client.get_entity(
                    "@" + forward_channel_target_username
                )

                log("forwarding to", channel_destination.username)

                await self.user_client.forward_messages(
                    channel_destination,
                    event.message.id,
                    event.message.peer_id,
                )

    def listen_to_channel(self, channel):
        log(f"Listening to channel: {channel.title} {channel.id}")

        self.user_client.add_event_handler(
            handle_user_message_for_bots,
            events.NewMessage(chats=channel.id),
        )

        self.channels_watched.append(channel)

        log(f"Channels watched: {self.channels_watched}")

    def stop_listening_to_channel(self, channel):
        log(f"Stopping listening to channel: {channel.title} {channel.id}")
        self.user_client.remove_event_handler(
            self.user_message_handler, events.NewMessage(chats=channel.id)
        )
        self.channels_watched = [
            c for c in self.channels_watched if channel.id != channel.id
        ]

        log(f"Channels watched: {self.channels_watched}")

    def add_channel_to_watch(self, channel):
        log(f"Adding channel {channel.username} to watch")
        self.channels_usernames_to_watch.append(channel.username)

        self.db.add_channel_to_watch(channel.username)
        self.listen_to_channel(channel)

    def remove_channel_to_watch(self, channel):
        log(f"Removing channel {channel.username} to watch")
        self.channels_usernames_to_watch.remove(channel.username)

        self.db.remove_channel_to_watch(channel.username)
        self.stop_listening_to_channel(channel)

    def set_channel_message_filter(self, channel_username, filter_regex):
        log(f"Setting filter {filter_regex} for channel {channel_username}")
        self.channel_username_to_message_filter[channel_username] = (
            filter_regex
        )

        self.db.set_channel_message_filter(channel_username, filter_regex)

    def add_channel_to_forward_to(self, channel_username):
        log(f"Adding channel {channel_username} to forward to")
        self.forward_channel_target_usernames.append(channel_username)

        self.db.add_channel_forward_target(channel_username)

    def remove_channel_to_forward_to(self, channel_username):
        log(f"Removing channel {channel_username} to forward to")
        self.forward_channel_target_usernames.remove(channel_username)

        self.db.remove_channel_forward_target(channel_username)

    async def init(self, dialogs):
        assert (
            len(self.channels_watched) == 0
        ), "channels_watched not empty when initializing"

        channels = [dialog.entity for dialog in dialogs if dialog.is_channel]
        channels_usernames_subscribed = [
            channel.username for channel in channels
        ]

        channels_to_subscribe_usernames = [
            channel_username
            for channel_username in self.channels_usernames_to_watch
            if channel_username not in channels_usernames_subscribed
        ]

        channels_to_subscribe_inputs = [
            await self.user_client.get_entity("@" + id)
            for id in channels_to_subscribe_usernames
        ]

        for channel in channels_to_subscribe_inputs:
            await channel_utils.subscribe_channel(self.user_client, channel)

        channels_to_listen = [
            channel
            for channel in channels
            if channel.username in self.channels_usernames_to_watch
        ] + channels_to_subscribe_inputs

        for channel in channels_to_listen:
            self.listen_to_channel(channel)

        log("channels_usernames_to_watch", self.channels_usernames_to_watch)
        log("channels_watched", [c.username for c in self.channels_watched])
        log(
            "forward_channel_target_usernames",
            self.forward_channel_target_usernames,
        )
        log(
            "channel_username_to_message_filter",
            self.channel_username_to_message_filter,
        )

        log("setup done")
