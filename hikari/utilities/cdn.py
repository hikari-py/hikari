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
"""Discord-specific URIs that have to be hard-coded."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["generate_cdn_url", "get_default_avatar_url", "get_default_avatar_index"]

import typing
import urllib.parse

from hikari.net import strings
from hikari.utilities import files


def generate_cdn_url(*route_parts: str, format_: str, size: typing.Optional[int]) -> files.URL:
    """Generate a link for a Discord CDN media resource.

    Parameters
    ----------
    *route_parts : str
        The string _route parts that will be used to form the link.
    format_ : str
        The format to use for the wanted cdn entity, will usually be one of
        `webp`, `png`, `jpeg`, `jpg` or `gif` (which will be invalid
        if the target entity doesn't have an animated version available).
    size : int or None
        The size to specify for the image in the query string if applicable,
        should be passed through as None to avoid the param being set.
        Must be any power of two between 16 and 4096.

    Returns
    -------
    hikari.utilities.files.URL
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
    url = urllib.parse.urljoin(strings.CDN_URL, "/" + path) + "." + str(format_)
    query = urllib.parse.urlencode({"size": size}) if size is not None else None
    return files.URL(f"{url}?{query}" if query else url)


def get_default_avatar_index(discriminator: str) -> int:
    """Get the index of the default avatar for the given discriminator.

    Parameters
    ----------
    discriminator : str
        The integer discriminator, as a string.

    Returns
    -------
    int
        The index.
    """
    return int(discriminator) % 5


def get_default_avatar_url(discriminator: str) -> files.URL:
    """URL for this user's default avatar.

    Parameters
    ----------
    discriminator : str
        The integer discriminator, as a string.

    Returns
    -------
    hikari.utilities.files.URL
        The avatar URL.
    """
    return generate_cdn_url("embed", "avatars", str(get_default_avatar_index(discriminator)), format_="png", size=None)
