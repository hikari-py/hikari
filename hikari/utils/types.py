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
Custom data structures.
"""
__all__ = ("DiscordObject",)

import typing

#: Any type that Discord may return.
_DiscordType = typing.Union[
    bool, float, int, None, str, typing.List["DiscordObject"], typing.Dict[str, "DiscordObject"]]

#: Type hint for a Discord-compatible object.
#:
#: This is a :class:`builtins.dict` of :class:`builtins.str` keys that map to any value. Since the :mod:`hikari.net`
#: module does not enforce concrete models for values sent and received, mappings are passed around to represent request
#: and response data. This allows an implementation to use this layer as desired.
DiscordObject = typing.Dict[str, _DiscordType]


class ObjectProxy(typing.Dict[str, typing.Any]):
    """
    A wrapper for a dict that enables accession of valid key names as if they were attributes.

    Example:
        >>> o = ObjectProxy({"foo": 10, "bar": 20})
        >>> print(o["foo"], o.bar)  # 10 20

    """

    def __getattr__(self, item):
        return self[item]
