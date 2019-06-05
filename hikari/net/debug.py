#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Provides a simple parser for Discord CGI debugging info. This can be used to determine the data center you are using
on the host running your code.

This API is not officially documented.
"""
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
