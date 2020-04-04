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
"""Configuration for sharding."""

__all__ = ["ShardConfig"]

import re
import typing

from hikari import entities
from hikari.internal import assertions
from hikari.internal import marshaller


def _parse_shard_info(payload):
    range_matcher = re.search(r"(\d+)\s*(\.{2,3})\s*(\d+)", payload)

    if not range_matcher:
        if isinstance(payload, str):
            payload = int(payload)

        if isinstance(payload, int):
            return [payload]

        raise ValueError('expected shard_ids to be one of int, list of int, or range string ("x..y")')

    minimum, range_mod, maximum = range_matcher.groups()
    minimum, maximum = int(minimum), int(maximum)
    if len(range_mod) == 3:
        maximum += 1

    return [*range(minimum, maximum)]


@marshaller.attrs(kw_only=True, init=False)
class ShardConfig(entities.HikariEntity, entities.Deserializable):
    """Manual sharding configuration.

    All fields are optional kwargs that can be passed to the constructor.

    "Deserialized" and "unspecified" defaults are only applicable if you
    create the object using :meth:`hikari.entities.Deserializable.deserialize`.
    """

    #: The shard IDs to produce shard connections for.
    #:
    #: If being deserialized, this can be several formats.
    #:     ``12``, ``"12"``:
    #:         A specific shard ID.
    #:     ``[0, 1, 2, 3, 8, 9, 10]``, ``["0", "1", "2", "3", "8", "9", "10"]``:
    #:         A sequence of shard IDs.
    #:     ``"5..16"``:
    #:         A range string. Two periods indicate a range of ``[5, 16)``
    #:         (inclusive beginning, exclusive end).
    #:     ``"5...16"``:
    #:         A range string. Three periods indicate a range of
    #:         ``[5, 17]`` (inclusive beginning, inclusive end).
    #:     ``None``:
    #:         The ``shard_count`` will be considered and that many shards will
    #:         be created for you.
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`int` ]
    shard_ids: typing.Sequence[int] = marshaller.attrib(
        deserializer=_parse_shard_info, if_none=None, if_undefined=None,
    )

    #: The number of shards the entire distributed application should consist
    #: of. If you run multiple instances of the bot, you should ensure this
    #: value is consistent.
    #:
    #: :type: :obj:`int`
    shard_count: int = marshaller.attrib(deserializer=int)

    # noinspection PyMissingConstructor
    def __init__(self, *, shard_ids: typing.Optional[typing.Iterable[int]] = None, shard_count: int) -> None:
        self.shard_ids = [*shard_ids] if shard_ids else [*range(shard_count)]

        for shard_id in self.shard_ids:
            assertions.assert_that(shard_id < shard_count, "shard_count must be greater than any shard ids")

        self.shard_count = shard_count
