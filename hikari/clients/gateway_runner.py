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

import click

from hikari.clients import shard_client
from hikari import entities

from hikari.clients import gateway_client
from hikari.clients import gateway_config
from hikari.clients import protocol_config
from hikari.clients import shard_config
from hikari.state import raw_event_consumer

logger_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "NOTSET")


def _supports_color():
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (plat != "win32" or "ANSICON" in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return supported_platform and is_a_tty


_color_format = (
    "\033[1;35m%(levelname)1.1s \033[0;31m%(asctime)23.23s \033[1;34m%(module)-15.15s "
    "\033[1;32m#%(lineno)-4d \033[0m:: \033[0;33m%(message)s\033[0m"
)
_regular_format = "%(levelname)1.1s %(asctime)23.23s %(module)-15.15s #%(lineno)-4d :: %(message)s"


@click.command()
@click.option("--compression", default=True, type=click.BOOL, help="Enable or disable gateway compression.")
@click.option("--color", default=_supports_color(), type=click.BOOL, help="Whether to enable or disable color.")
@click.option("--debug", default=False, type=click.BOOL, help="Enable or disable debug mode.")
@click.option("--logger", default="INFO", type=click.Choice(logger_levels), help="Logger verbosity.")
@click.option("--shards", default=1, type=click.IntRange(min=1), help="The number of shards to explicitly use.")
@click.option("--token", required=True, envvar="TOKEN", help="The token to use to authenticate with Discord.")
@click.option("--url", default="wss://gateway.discord.gg/", help="The websocket URL to connect to.")
@click.option("--verify-ssl", default=True, type=click.BOOL, help="Enable or disable SSL verification.")
@click.option("--version", default=7, type=click.IntRange(min=6), help="Version of the gateway to use.")
def run_gateway(compression, color, debug, logger, shards, token, url, verify_ssl, version) -> None:
    """:mod:`click` command line client for running a test gateway connection.

    This is provided for internal testing purposes for benchmarking API
    stabiltiy, etc.
    """
    logging.captureWarnings(True)

    logging.basicConfig(level=logger, format=_color_format if color else _regular_format, stream=sys.stdout)

    class _DummyConsumer(raw_event_consumer.RawEventConsumer):
        def process_raw_event(
            self, _client: shard_client.ShardClient, _name: str, _payload: entities.RawEntityT
        ) -> None:
            pass

    client = gateway_client.GatewayClient(
        config=gateway_config.GatewayConfig(
            debug=debug,
            protocol=protocol_config.HTTPProtocolConfig(verify_ssl=verify_ssl),
            shard_config=shard_config.ShardConfig(shard_count=shards),
            token=token,
            use_compression=compression,
            version=version,
        ),
        url=url,
        raw_event_consumer_impl=_DummyConsumer(),
    )

    client.run()


if __name__ == "__main__":
    run_gateway()  # pylint:disable=no-value-for-parameter
