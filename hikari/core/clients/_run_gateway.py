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

import click

from hikari.core.clients import gateway_client
from hikari.core.clients import gateway_config
from hikari.core.clients import protocol_config

logger_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "NOTSET")


@click.command()
@click.option("--compression", default=True, type=click.BOOL, help="Enable or disable gateway compression.")
@click.option("--debug", default=False, type=click.BOOL, help="Enable or disable debug mode.")
@click.option("--logger", default="INFO", type=click.Choice(logger_levels), help="Logger verbosity.")
@click.option("--shards", default=1, type=click.IntRange(min=1), help="The number of shards to explicitly use.")
@click.option("--token", required=True, envvar="TOKEN", help="The token to use to authenticate with Discord.")
@click.option("--url", default="wss://gateway.discord.gg/", help="The websocket URL to connect to.")
@click.option("--verify-ssl", default=True, type=click.BOOL, help="Enable or disable SSL verification.")
@click.option("--version", default=7, type=click.IntRange(min=6), help="Version of the gateway to use.")
def run_gateway(compression, debug, logger, shards, token, url, verify_ssl, version):
    """Run the client."""
    logging.basicConfig(level=logger)

    client = gateway_client.GatewayClient(
        config=gateway_config.GatewayConfig(
            debug=debug,
            protocol=protocol_config.HTTPProtocolConfig(verify_ssl=verify_ssl),
            shard_config=gateway_config.ShardConfig(shard_count=shards),
            token=token,
            use_compression=compression,
            version=version,
        ),
        url=url,
    )

    client.run()


run_gateway()  # pylint:disable=no-value-for-parameter
