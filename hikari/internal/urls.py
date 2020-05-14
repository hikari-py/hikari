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
"""Discord-specific URIs that have to be hard-coded."""

from __future__ import annotations

__all__ = [
    "generate_cdn_url",
]

import typing
import urllib.parse


BASE_CDN_URL: typing.Final[str] = "https://cdn.discordapp.com"
"""The URL for the CDN."""

REST_API_URL: typing.Final[str] = "https://discord.com/api/v{0.version}"
"""The URL for the REST API. This contains a version number parameter that
should be interpolated.
"""

OAUTH2_API_URL: typing.Final[str] = "https://discord.com/api/oauth2"
"""The URL to the Discord OAuth2 API."""

TWEMOJI_PNG_BASE_URL: typing.Final[str] = "https://github.com/twitter/twemoji/raw/master/assets/72x72/"
"""The URL for Twemoji PNG artwork for built-in emojis."""

TWEMOJI_SVG_BASE_URL: typing.Final[str] = "https://github.com/twitter/twemoji/raw/master/assets/svg/"
"""The URL for Twemoji SVG artwork for built-in emojis."""


def generate_cdn_url(*route_parts: str, format_: str, size: typing.Optional[int]) -> str:
    """Generate a link for a Discord CDN media resource.

    Parameters
    ----------
    *route_parts : str
        The string route parts that will be used to form the link.
    format_ : str
        The format to use for the wanted cdn entity, will usually be one of
        `webp`, `png`, `jpeg`, `jpg` or `gif` (which will be invalid
        if the target entity doesn't have an animated version available).
    size : int, optional
        The size to specify for the image in the query string if applicable,
        should be passed through as None to avoid the param being set.
        Must be any power of two between 16 and 4096.

    Returns
    -------
    str
        The URL to the resource on the Discord CDN.

    Raises
    ------
    ValueError
        If `size` is not a power of two or not between 16 and 4096.
    """
    if size and not 16 <= size <= 4096:
        raise ValueError("Size must be in the inclusive range of 16 and 4096")
    if size and size % 2 != 0:
        raise ValueError("Size must be an integer power of 2")

    path = "/".join(urllib.parse.unquote(part) for part in route_parts)
    url = urllib.parse.urljoin(BASE_CDN_URL, "/" + path) + "." + str(format_)
    query = urllib.parse.urlencode({"size": size}) if size is not None else None
    return f"{url}?{query}" if query else url
