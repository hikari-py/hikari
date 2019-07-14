#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
Provides a simple parser for Discord CGI debugging info. This can be used to determine the data center you are using
on the host running your code.

This API is not officially documented.
"""
from __future__ import annotations

__all__ = ("get_debug_data",)

import datetime
import re

import aiohttp

from hikari.model import server_debug


async def get_debug_data() -> server_debug.DebugData:
    """
    Query the DiscordApp CDN CGI trace to determine debugging info such as the data center that you are likely using.
    This will then query `http://airlinecodes.co.uk` to determine the data center location from the provided
    airport code in this response.
    """
    async with aiohttp.request("get", "https://discordapp.com/cdn-cgi/trace") as resp:
        resp.raise_for_status()
        content = await resp.text()

    pairs = {}
    for line in content.splitlines(False):
        line = line.strip()
        if line:
            k, _, v = line.partition("=")
            pairs[k] = v

    async with aiohttp.request(
        "post", "http://www.airlinecodes.co.uk/aptcoderes.asp", data={"iatacode": pairs["colo"]}
    ) as resp:
        resp.raise_for_status()
        content = await resp.text()

    location_match = re.search(r"<td.*?>Location:</td>\s*?<td>(.*?)</td>", content, re.I | re.M)
    airport_match = re.search(r"<td.*?>Airport:</td>\s*?<td>(.*?)</td>", content, re.I | re.M)
    country_match = re.search(r"<td.*?>Country:</td>\s*?<td>(.*?)</td>", content, re.I | re.M)

    location = location_match.group(1).strip() if location_match else "Unknown"
    airport = airport_match.group(1).strip() if airport_match else "Unknown"
    country = country_match.group(1).strip() if country_match else "Unknown"

    pairs["colo"] = server_debug.DataCenter(pairs["colo"], location, airport, country)
    pairs["ts"] = datetime.datetime.fromtimestamp(float(pairs["ts"]), datetime.timezone.utc)
    return server_debug.DebugData(**pairs)
