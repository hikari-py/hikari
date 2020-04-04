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
"""Basic utilities for handling the cdn.

|internal|
"""

__all__ = [
    "generate_cdn_url",
]

import typing
import urllib.parse


BASE_CDN_URL = "https://cdn.discordapp.com"


def generate_cdn_url(*route_parts: str, fmt: str, size: typing.Optional[int]) -> str:
    """Generate a link for a cdn entry.

    Parameters
    ----------
    route_parts : :obj:`str`
        The string route parts that will be used to form the link.
    fmt : :obj:`str`
        The format to use for the wanted cdn entity, will usually be one of
        ``webp``, ``png``, ``jpeg``, ``jpg`` or ``gif`` (which will be invalid
        if the target entity doesn't have an animated version available).
    size : :obj:`int`, optional
        The size to specify for the image in the query string if applicable,
        should be passed through as ``None`` to avoid the param being set.

    Returns
    -------
    :obj:`str`
        The formed cdn url.
    """
    path = "/".join(urllib.parse.unquote(part) for part in route_parts)
    url = urllib.parse.urljoin(BASE_CDN_URL, "/" + path) + "." + str(fmt)
    query = urllib.parse.urlencode({"size": size}) if size is not None else None
    return f"{url}?{query}" if query else url
