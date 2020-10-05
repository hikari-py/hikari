# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""A simple bot with a `!image` command that shows the image for various things.

This demonstrates how many Hikari objects can act as attachments without any
special treatment.
"""

import os
import re

import hikari

bot = hikari.BotApp(token=os.environ["BOT_TOKEN"])


@bot.listen()
async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
    """Listen for messages being created."""
    if not event.is_human or not event.content or not event.content.startswith("!"):
        # Do not respond to bots, webhooks, or messages without content or without a prefix.
        return

    args = event.content[1:].split()

    if args[0] == "image":
        if len(args) == 1:
            # No more args where provided
            what = ""
        else:
            what = args[1]

        # Since uploading can take some time, we give a visual indicator to the user by typing
        async with bot.rest.trigger_typing(event.channel_id):
            await inspect_image(event, what.lstrip())


async def inspect_image(event: hikari.GuildMessageCreateEvent, what: str) -> None:
    """Inspect the image and respond to the user."""
    # Show the avatar for the given user ID:
    if user_match := re.match(r"<@!?(\d+)>", what):
        user_id = hikari.Snowflake(user_match.group(1))
        user = bot.cache.get_user(user_id) or await bot.rest.fetch_user(user_id)
        await event.message.reply("User avatar", attachment=user.avatar_url or user.default_avatar_url)

    # Show the guild icon:
    elif what.casefold() in ("guild", "server", "here", "this"):
        if event.guild is None:
            await event.message.reply("Guild is missing from the cache :(")
            return

        icon = event.guild.icon_url
        if icon is None:
            await event.message.reply("This guild doesn't have an icon")
        else:
            await event.message.reply("Guild icon", attachment=icon)

    # Show the image for the given emoji if there is some content present:
    elif what:
        emoji = hikari.Emoji.parse(what)
        await event.message.reply(emoji.name, attachment=emoji)

    # If nothing was given, we should just return the avatar of the person who ran the command:
    else:
        await event.message.reply("Your avatar", attachment=event.author.avatar_url or event.author.default_avatar_url)


bot.run()
