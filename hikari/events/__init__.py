# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Events that can be fired by Hikari's gateway implementation."""

from __future__ import annotations

import typing

from hikari.events import channel_events
from hikari.events import guild_events
from hikari.events import lifetime_events
from hikari.events import member_events
from hikari.events import message_events
from hikari.events import reaction_events
from hikari.events import role_events
from hikari.events import shard_events
from hikari.events import typing_events
from hikari.events import user_events
from hikari.events import voice_events
from hikari.events.base_events import Event
from hikari.events.base_events import ExceptionEvent
from hikari.events.channel_events import *
from hikari.events.guild_events import *
from hikari.events.lifetime_events import *
from hikari.events.member_events import *
from hikari.events.message_events import *
from hikari.events.reaction_events import *
from hikari.events.role_events import *
from hikari.events.shard_events import *
from hikari.events.typing_events import *
from hikari.events.user_events import *
from hikari.events.voice_events import *

__all__: typing.List[str] = (
    ["Event", "ExceptionEvent"]
    + channel_events.__all__
    + guild_events.__all__
    + lifetime_events.__all__
    + member_events.__all__
    + message_events.__all__
    + reaction_events.__all__
    + role_events.__all__
    + shard_events.__all__
    + typing_events.__all__
    + user_events.__all__
    + voice_events.__all__
)
