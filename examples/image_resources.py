# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""A simple bot with a `!image` command that shows the image for various things.

This demonstrates how many Hikari objects can act as attachments without any
special treatment.
"""

from __future__ import annotations

import os
import re

import hikari

bot = hikari.GatewayBot(token=os.environ["BOT_TOKEN"])


@bot.listen()
async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
    """Listen for messages being created."""
    if not event.is_human or not event.content or not event.content.startswith("!"):
        # Do not respond to bots, webhooks, or messages without content or without a prefix.
        return

    args = event.content[1:].split()

    if args[0] == "image":
        # If args == 1, then we were only provided "image", nothing else
        what = "" if len(args) == 1 else args[1]

        # Since uploading can take some time, we give a visual indicator to the user by typing
        async with bot.rest.trigger_typing(event.channel_id):
            await inspect_image(event, what.lstrip())


async def inspect_image(event: hikari.GuildMessageCreateEvent, what: str) -> None:
    """Inspect the image and respond to the user."""
    # Show the avatar for the given user ID:
    if user_match := re.match(r"<@!?(\d+)>", what):
        user_id = hikari.Snowflake(user_match.group(1))
        user = bot.cache.get_user(user_id) or await bot.rest.fetch_user(user_id)
        await event.message.respond("User avatar", attachment=user.avatar_url or user.default_avatar_url)

    # Show the guild icon:
    elif what.casefold() in {"guild", "server", "here", "this"}:
        guild = event.get_guild()
        if guild is None:
            await event.message.respond("Guild is missing from the cache :(")
            return

        if (icon_url := guild.icon_url) is None:
            await event.message.respond("This guild doesn't have an icon")
        else:
            await event.message.respond("Guild icon", attachment=icon_url)

    # Show the image for the given emoji if there is some content present:
    elif what:
        emoji = hikari.Emoji.parse(what)
        await event.message.respond(emoji.name, attachment=emoji)

    # If nothing was given, we should just return the avatar of the person who ran the command:
    else:
        await event.message.respond(
            "Your avatar", attachment=event.author.avatar_url or event.author.default_avatar_url
        )


bot.run()
