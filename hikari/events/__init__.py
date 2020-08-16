# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
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
