#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""An executable module to be used to test that the gateway works as intended.

This is only for use by developers of this library, regular users do not need
to use this.
"""
import datetime
import logging
import math
import os
import re
import sys
import time
import typing

import click

import hikari
from hikari.internal import conversions
from hikari.net import codes

_LOGGER_LEVELS: typing.Final[typing.Sequence[str]] = ["DEBUG", "INFO", "WARNING", "ERROR", "NOTSET"]


def _supports_color():
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (plat != "win32" or "ANSICON" in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return supported_platform and is_a_tty


_COLOR_FORMAT: typing.Final[str] = (
    "\033[1;35m%(levelname)1.1s \033[0;37m%(name)25.25s \033[0;31m%(asctime)23.23s \033[1;34m%(module)-15.15s "
    "\033[1;32m#%(lineno)-4d \033[0m:: \033[0;33m%(message)s\033[0m"
)

_REGULAR_FORMAT: typing.Final[str] = (
    "%(levelname)1.1s %(name)25.25s %(asctime)23.23s %(module)-15.15s #%(lineno)-4d :: %(message)s"
)


@click.command()
@click.option("--compression", default=True, type=click.BOOL, help="Enable or disable gateway compression.")
@click.option("--color", default=_supports_color(), type=click.BOOL, help="Whether to enable or disable color.")
@click.option("--debug", default=False, type=click.BOOL, help="Enable or disable debug mode.")
@click.option("--intents", default=None, type=click.STRING, help="Intent names to enable (comma separated)")
@click.option("--logger", envvar="LOGGER", default="INFO", type=click.Choice(_LOGGER_LEVELS), help="Logger verbosity.")
@click.option("--shards", default=1, type=click.IntRange(min=1), help="The number of shards to explicitly use.")
@click.option("--token", required=True, envvar="TOKEN", help="The token to use to authenticate with Discord.")
@click.option("--verify-ssl", default=True, type=click.BOOL, help="Enable or disable SSL verification.")
@click.option("--version", default=6, type=click.IntRange(min=6), help="Version of the gateway to use.")
def run_gateway(compression, color, debug, intents, logger, shards, token, verify_ssl, version) -> None:
    """:mod:`click` command line client for running a test gateway connection.

    This is provided for internal testing purposes for benchmarking API
    stability, etc.
    """
    if intents is not None:
        intents = intents.split(",")
        intents = conversions.dereference_int_flag(codes.GatewayIntent, intents)

    logging.captureWarnings(True)

    logging.basicConfig(level=logger, format=_COLOR_FORMAT if color else _REGULAR_FORMAT, stream=sys.stdout)

    client = hikari.StatelessBot(
        hikari.BotConfig(
            token=token,
            gateway_version=version,
            debug=debug,
            gateway_use_compression=compression,
            intents=intents,
            verify_ssl=verify_ssl,
            shard_count=shards,
            initial_activity=hikari.GatewayActivity(name="people mention me", type=hikari.ActivityType.LISTENING,),
        )
    )

    bot_id = 0
    bot_avatar_url = "about:blank"
    startup_time = 0

    @client.on()
    async def on_start(_: hikari.StartingEvent):
        nonlocal startup_time
        startup_time = time.perf_counter()

    @client.on()
    async def on_ready(event: hikari.ReadyEvent) -> None:
        nonlocal bot_id, bot_avatar_url
        bot_id = event.my_user.id
        bot_avatar_url = event.my_user.avatar_url

    def since(epoch):
        if math.isnan(epoch):
            return "never"
        return datetime.timedelta(seconds=time.perf_counter() - epoch)

    @client.on()
    async def on_message(event: hikari.MessageCreateEvent) -> None:
        if not event.author.is_bot and re.match(f"^<@!?{bot_id}>$", event.content):
            start = time.perf_counter()
            message = await client.rest.create_message(event.channel_id, content="Pong!")
            rest_time = time.perf_counter() - start

            active_intents = str(client.gateway._config.intents or "not provided")

            shard_infos = []
            for shard_id, shard in client.gateway.shards.items():
                shard_info = (
                    f"latency: {shard.heartbeat_latency * 1_000:.0f} ms\n"
                    f"seq: {shard.seq}\n"
                    f"session id: {shard.session_id}\n"
                    f"reconnects: {shard.reconnect_count}\n"
                    f"heartbeat interval: {shard.heartbeat_interval} s\n"
                    f"state: {shard.connection_state.name}\n"
                )

                shard_infos.append(hikari.EmbedField(name=f"Shard {shard_id}", value=shard_info, is_inline=False))

            gw_info = (
                f"average latency: {client.gateway.latency * 1_000:.0f} ms\n"
                f"shards: {len(client.gateway.shards)}\n"
                f"version: {version}\n"
                f"compression: {compression}\n"
                f"debug: {debug}\n"
                f"intents: {hex(intents)} ({active_intents})"
            )

            rest_info = (
                f"message edit time: {rest_time * 1_000:.0f} ms\n"
                f"global rate limiter backlog: {len(client.rest._session.global_ratelimiter.queue)}\n"
                f"bucket rate limiter active routes: {len(client.rest._session.ratelimiter.routes_to_hashes)}\n"
                f"bucket rate limiter active buckets: {len(client.rest._session.ratelimiter.real_hashes_to_buckets)}\n"
                "bucket rate limiter backlog: "
                f"{sum(len(b.queue) for b in client.rest._session.ratelimiter.real_hashes_to_buckets.values())}\n"
                f"bucket rate limiter GC: {getattr(client.rest._session.ratelimiter.gc_task, '_state', 'dead')}\n"
            )

            embed = hikari.Embed(
                author=hikari.EmbedAuthor(name=hikari.__copyright__),
                url=hikari.__url__,
                title=f"Hikari {hikari.__version__} debugging test client",
                footer=hikari.EmbedFooter(text=hikari.__license__),
                description=f"Uptime: {since(startup_time)}",
                fields=[
                    hikari.EmbedField(name="REST", value=rest_info, is_inline=False),
                    hikari.EmbedField(name="Gateway Manager", value=gw_info, is_inline=False),
                    *shard_infos[:3],
                ],
                thumbnail=hikari.EmbedThumbnail(url=bot_avatar_url),
                color=hikari.Color["#F660AB"],
            )

            await client.rest.update_message(message, message.channel_id, content="Pong!", embed=embed)

    client.run()


if __name__ == "__main__":
    run_gateway()  # pylint:disable=no-value-for-parameter
