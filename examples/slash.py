# -*- coding: utf-8 -*-
# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""A simple bot with some simple commands."""

import os

import hikari

bot = hikari.GatewayBot(token=os.environ["BOT_TOKEN"])


@bot.listen()
async def on_interaction(event: hikari.InteractionCreateEvent) -> None:
    """Listen for messages being created."""
    if not isinstance(event.interaction, hikari.CommandInteraction):
        # only listen to command interactions, no others!
        return

    if event.interaction.command_name == "ping":
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            f"Pong! {bot.heartbeat_latency * 1_000:.0f}ms",
        )

    elif event.interaction.command_name == "info":
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            "Hello, this is an example bot written in hikari!",
        )


bot.run()
