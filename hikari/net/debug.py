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
__all__ = ("DataCenter", "DebugData", "get_debug_data")

import datetime
import re
from dataclasses import dataclass

import aiohttp


@dataclass(frozen=True)
class DataCenter:
    """Represents a data center. These are represented by an IATA airport code."""

    __slots__ = ("iata_code", "location", "airport", "country")

    #: Airport code
    iata_code: str
    #: Data center location
    location: str
    #: Data center airport name
    airport: str
    #: Data center country
    country: str

    def __str__(self):
        return f"{self.airport} ({self.iata_code}), {self.location}, {self.country}"


@dataclass(frozen=True)
class DebugData:
    """The response provided from Discord's CGI trace."""

    __slots__ = ("fl", "ip", "ts", "h", "visit_scheme", "uag", "colo", "http", "loc", "tls", "sni", "warp")

    #: Unknown, possibly some form of correlation ID.
    fl: str
    #: Your IP
    ip: str
    #: UTC unix timestamp.
    ts: datetime.datetime
    #: The host that was hit.
    h: str
    #: Scheme used
    visit_scheme: str
    #: User agent used
    uag: str
    #: Data Center info.
    colo: DataCenter
    #: HTTP version used.
    http: str
    #: Apparent location
    loc: str
    #: TLS/SSL version used.
    tls: str
    #: Unknown, possibly the content type of this response.
    sni: str
    #: Unknown.
    warp: str


async def get_debug_data() -> DebugData:
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

    location = location_match and location_match.group(1).strip() or "Unknown"
    airport = airport_match and airport_match.group(1).strip() or "Unknown"
    country = country_match and country_match.group(1).strip() or "Unknown"

    pairs["colo"] = DataCenter(pairs["colo"], location, airport, country)
    pairs["ts"] = datetime.datetime.fromtimestamp(float(pairs["ts"]), datetime.timezone.utc)
    return DebugData(**pairs)
