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
Presences for members.
"""
import abc
import datetime
import enum
from typing import List

import typing

from hikari.core.model import base
from hikari.core.utils import transform


@base.dataclass()
class MemberPresence:
    __slots__ = ("activities", "client_status", "status")


class ActivityType(enum.IntEnum):
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3


@base.dataclass()
class Game:
    """
    An old-style activity that is not linked to a rich presence.

    Note:
        The :attr:`url` field is only applicable to the :attr:`ActivityType.STREAMING` activity type. For anything
        else, it will be `None`.
    """
    __slots__ = ("type", "name", "id", "url", "created_at")

    type: ActivityType
    name: str
    id: str
    url: typing.Optional[str]
    created_at: datetime.datetime

    @staticmethod
    def from_dict(payload):
        return Game(
            type=transform.get_cast_or_raw(payload, "type", ActivityType),
        )


class Activity(abc.ABC):
    __slots__ = ("name", )
