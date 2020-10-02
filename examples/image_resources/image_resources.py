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
    if not event.is_human or not event.content or not event.content.startswith("!"):
        # Do not respond to bots, webhooks, or messages without content or without a prefix.
        return

    command, _, args = event.content[1:].partition(" ")

    if command == "image":
        await inspect_image(event, args.lstrip())


async def inspect_image(event: hikari.GuildMessageCreateEvent, what: str) -> None:
    # Show the avatar for the given user ID:
    if user_match := re.match(r"<@!?(\d+)>", what):
        user_id = hikari.Snowflake(user_match.group(1))
        user = bot.cache.get_user(user_id) or await bot.rest.fetch_user(user_id)
        await event.message.reply("User avatar", attachment=user.avatar_url or user.default_avatar_url)

    # Show the guild icon:
    elif what.casefold() in ("guild", "server", "here", "this"):
        await event.message.reply("Guild icon", attachment=event.guild.icon_url)

    # Show the image for the given custom emoji:
    elif custom_emoji_match := re.match(r"<a?:([^:]+):(\d+)>", what):
        name, emoji_id = custom_emoji_match.group(1), hikari.Snowflake(custom_emoji_match.group(2))
        emoji = bot.cache.get_emoji(emoji_id)
        await event.message.reply(f"Emoji {name}", attachment=emoji)

    # If any content exists, try treating it as a unicode emoji; only upload if it is actually valid:
    elif what.strip():
        # If this is not a valid emoji, this will raise hikari.NotFoundError
        emoji = hikari.UnicodeEmoji.from_emoji(what)
        await event.message.reply("Unicode Emoji", attachment=emoji)

    # If nothing was given, we should just return the avatar of the person who ran the command:
    else:
        await event.message.reply("Your avatar", attachment=event.author.avatar_url or event.author.default_avatar_url)


bot.run()
