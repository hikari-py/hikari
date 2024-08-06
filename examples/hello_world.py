# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""A simple bot with only a `!ping` command."""

from __future__ import annotations

import os

import hikari

bot = hikari.GatewayBot(token=os.environ["BOT_TOKEN"])


@bot.listen()
async def on_message(event: hikari.MessageCreateEvent) -> None:
    """Listen for messages being created."""
    if not event.is_human:
        # Do not respond to bots or webhooks!
        return

    if event.content == "!ping":
        await event.message.respond(f"Pong! {bot.heartbeat_latency * 1_000:.0f}ms")


bot.run()
