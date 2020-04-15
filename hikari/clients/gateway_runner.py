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
import logging
import os
import sys
import typing

import click

from hikari.clients import configs
from hikari.clients import gateway_managers
from hikari.internal import conversions
from hikari.net import codes
from hikari.state import stateless_event_managers


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
@click.option("--url", default="wss://gateway.discord.gg/", help="The websocket URL to connect to.")
@click.option("--verify-ssl", default=True, type=click.BOOL, help="Enable or disable SSL verification.")
@click.option("--version", default=6, type=click.IntRange(min=6), help="Version of the gateway to use.")
def run_gateway(compression, color, debug, intents, logger, shards, token, url, verify_ssl, version) -> None:
    """:mod:`click` command line client for running a test gateway connection.

    This is provided for internal testing purposes for benchmarking API
    stability, etc.
    """
    if intents is not None:
        intents = intents.split(",")
        intents = conversions.dereference_int_flag(codes.GatewayIntent, intents)

    logging.captureWarnings(True)

    logging.basicConfig(level=logger, format=_COLOR_FORMAT if color else _REGULAR_FORMAT, stream=sys.stdout)

    manager = stateless_event_managers.StatelessEventManagerImpl()

    client = gateway_managers.GatewayManager(
        shard_ids=[*range(shards)],
        shard_count=shards,
        config=configs.WebsocketConfig(
            token=token,
            gateway_version=version,
            debug=debug,
            gateway_use_compression=compression,
            intents=intents,
            verify_ssl=verify_ssl,
        ),
        url=url,
        raw_event_consumer_impl=manager,
        dispatcher=manager.event_dispatcher,
    )

    client.run()


if __name__ == "__main__":
    run_gateway()  # pylint:disable=no-value-for-parameter
