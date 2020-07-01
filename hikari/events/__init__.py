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
"""Application and entities that are used to describe Discord gateway events."""

from __future__ import annotations

# noinspection PyUnresolvedReferences
import typing

from hikari.events import base
from hikari.events import channel
from hikari.events import guild
from hikari.events import message
from hikari.events import other
from hikari.events import voice

from hikari.events.base import Event
from hikari.events.channel import *
from hikari.events.guild import *
from hikari.events.message import *
from hikari.events.other import *
from hikari.events.voice import *

__all__: typing.Final[typing.List[str]] = (
    ["Event"] + channel.__all__ + guild.__all__ + message.__all__ + other.__all__ + voice.__all__
)
