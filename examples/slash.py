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

# Set this to the guild to create the slash commands in.
# To create global commands, set to `hikari.UNDEFINED`.
#
# It is important to note that global commands can take up to an hour to show in the client
# and should only be used when "publishing" commands after they are built. For testing
# use guild based commands as they are instant.
COMMAND_GUILD_ID = 0


@bot.listen()
async def register_commands(event: hikari.StartingEvent) -> None:
    """Register ping and info commands."""
    application = await bot.rest.fetch_application()

    commands = [
        bot.rest.slash_command_builder("ping", "Get the bot's latency."),
        bot.rest.slash_command_builder("info", "Learn something about the bot."),
        bot.rest.slash_command_builder("ephemeral", "Send a very secret message."),
    ]

    await bot.rest.set_application_commands(application=application.id, commands=commands, guild=COMMAND_GUILD_ID)


@bot.listen()
async def handle_interactions(event: hikari.InteractionCreateEvent) -> None:
    """Listen for slash commands being executed."""
    if not isinstance(event.interaction, hikari.CommandInteraction):
        # only listen to command interactions, no others!
        return

    if event.interaction.command_name == "ping":
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE, f"Pong! {bot.heartbeat_latency * 1_000:.0f}ms"
        )

    elif event.interaction.command_name == "info":
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE, "Hello, this is an example bot written in hikari!"
        )

    elif event.interaction.command_name == "ephemeral":
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            "Only you can see this, keep it a secret :)",
            flags=hikari.MessageFlag.EPHEMERAL,
        )


bot.run()
