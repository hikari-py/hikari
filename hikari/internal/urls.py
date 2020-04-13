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
"""Discord-specific URIs that have to be hard-coded.

|internal|
"""

__all__ = [
    "generate_cdn_url",
]

import typing
import urllib.parse

from hikari.internal import assertions

#: The URL for the CDN.
#:
#: :type: :obj:`str`
BASE_CDN_URL: typing.Final[str] = "https://cdn.discordapp.com"

#: The URL for the REST API. This contains a version number parameter that
#: should be interpolated.
#:
#: :type: :obj:`str`
REST_API_URL: typing.Final[str] = "https://discordapp.com/api/v{0.version}"


def generate_cdn_url(*route_parts: str, fmt: str, size: typing.Optional[int]) -> str:
    """Generate a link for a Discord CDN media resource.

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
        should be passed through as :obj:`None` to avoid the param being set.
        Must be any power of two between 16 and 4096.

    Returns
    -------
    :obj:`str`
        The URL to the resource on the Discord CDN.

    Raises
    ------
    :obj:`ValueError`
        If ``size`` is not a power of two or not between 16 and 4096.
    """
    if size:
        assertions.assert_in_range(size, 16, 4096)
        assertions.assert_is_int_power(size, 2)

    path = "/".join(urllib.parse.unquote(part) for part in route_parts)
    url = urllib.parse.urljoin(BASE_CDN_URL, "/" + path) + "." + str(fmt)
    query = urllib.parse.urlencode({"size": size}) if size is not None else None
    return f"{url}?{query}" if query else url
