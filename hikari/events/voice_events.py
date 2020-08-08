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
"""Events that fire when voice state changes."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "VoiceEvent",
    "VoiceStateUpdateEvent",
    "VoiceServerUpdateEvent",
]

import abc
import typing

import attr

from hikari.events import base_events
from hikari.events import shard_events
from hikari.models import intents
from hikari.utilities import attr_extensions

if typing.TYPE_CHECKING:
    from hikari.api import shard as gateway_shard
    from hikari.models import voices
    from hikari.utilities import snowflake


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VoiceEvent(shard_events.ShardEvent, abc.ABC):
    """Base for any voice-related event."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflake.Snowflake:
        """ID of the guild this event is for.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The guild ID of the guild this event relates to.
        """


@base_events.requires_intents(intents.Intent.GUILD_VOICE_STATES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VoiceStateUpdateEvent(VoiceEvent):
    """Event fired when a user changes their voice state.

    Sent when a user joins, leaves or moves voice channel(s).

    This is also fired for the application user, and is used when preparing
    to connect to the voice gateway to stream audio or video content.
    """

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring>>.

    state: voices.VoiceState = attr.ib(repr=True)
    """Voice state that this update contained.

    Returns
    -------
    hikari.models.voices.VoiceState
        The voice state that was updated.
    """

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from VoiceEvent>>
        return self.state.guild_id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VoiceServerUpdateEvent(VoiceEvent):
    """Event fired when a voice server is changed.

    Sent when initially connecting to voice and when the current voice instance
    falls over to a new server.
    """

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    # <<inherited docstring from VoiceEvent>>

    token: str = attr.ib(repr=False)
    """Token that should be used to authenticate with the voice gateway.

    Returns
    -------
    builtins.str
        The token to use to authenticate with the voice gateway.
    """

    raw_endpoint: str = attr.ib(repr=True)
    """Raw endpoint URL that Discord sent.

    This will always be incorrect, because sending a correct URL would be too
    useful to you.

    Returns
    -------
    builtins.str
        The incorrect endpoint URL for the voice gateway server to connect to.
    """

    @property
    def endpoint(self) -> str:
        """URI for this voice server host, with the correct port and protocol.

        Returns
        -------
        builtins.str
            The URI to use to connect to the voice gateway.
        """
        # Discord have had this wrong for like 4 years, bleh.
        uri, _, _ = self.raw_endpoint.rpartition(":")
        return f"wss://{uri}:443"
