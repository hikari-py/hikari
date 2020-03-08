#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
A helper utility class that polls the API status pages every so often to check
if the API is having any difficulties. If any are detected, this is printed to
the logs.
"""
__all__ = ["log_api_incidents"]

import asyncio

import aiohttp

from hikari.internal_utilities import loggers
from hikari.net import ratelimits
from hikari.net import status_info_client

logger = loggers.get_named_logger(__name__)


_OPERATIONAL = "Operational"


async def log_api_incidents(client: status_info_client.StatusInfoClient, period: float = 300) -> None:
    """Log API status changes.

    Polls the API status pages using the given client at the given period.

    Any notable new incidents or status pages will be logged.

    Parameters
    ----------
    client : :obj:`hikari.net.status_info_client.StatusInfoClient`
        The status info client to use.

    period : :obj:`float`
        How often to check for updates.
    """
    try:
        logger.debug("fetching initial API status info")

        backoff = ratelimits.ExponentialBackOff()
        previous_status = await _fetch_latest(client, backoff)

        _log_initial_state(previous_status)

        while True:
            await asyncio.sleep(period)
            current_status = await _fetch_latest(client, backoff)

            _log_change_in_status(previous_status, current_status)

            previous_status = current_status

    except asyncio.CancelledError:
        logger.debug("stopping task that is monitoring API status")


def _log_initial_state(status):
    logger.info(
        "Current API status\n    %r (updated at %s)\n    Extra info: %s\n    See %s for more details.",
        _indicator(status.status.indicator),
        status.page.updated_at,
        status.status.description,
        status.page.url,
    )


def _log_change_in_status(previous_status, current_status):
    if current_status.status.indicator != previous_status.status.indicator:
        logger.warning(
            "API status update"
            "    Status changed from %r to %r (updated at %r)\n"
            "        Extra info: %s\n"
            "        See %s for more details.",
            _indicator(previous_status.status.indicator),
            _indicator(current_status.status.indicator),
            current_status.page.updated_at,
            current_status.status.description,
            current_status.page.url,
        )


async def _fetch_latest(client, backoff):
    while True:
        try:
            status = await client.fetch_status()
            backoff.reset()
            return status
        except aiohttp.ClientError:
            sleep_for = next(backoff)
            logger.warning("failed to retrieve API status because %s, will try again...")
            await asyncio.sleep(sleep_for)


def _indicator(raw_indicator):
    if raw_indicator == "none":
        return _OPERATIONAL
    return raw_indicator
