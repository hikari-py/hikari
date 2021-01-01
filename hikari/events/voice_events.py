# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = [
    "VoiceEvent",
    "VoiceStateUpdateEvent",
    "VoiceServerUpdateEvent",
]

import abc
import typing

import attr

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import snowflakes
    from hikari import traits
    from hikari import voices
    from hikari.api import shard as gateway_shard


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VoiceEvent(shard_events.ShardEvent, abc.ABC):
    """Base for any voice-related event."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild this event is for.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The guild ID of the guild this event relates to.
        """


@base_events.requires_intents(intents.Intents.GUILD_VOICE_STATES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VoiceStateUpdateEvent(VoiceEvent):
    """Event fired when a user changes their voice state.

    Sent when a user joins, leaves or moves voice channel(s).

    This is also fired for the application user, and is used when preparing
    to connect to the voice gateway to stream audio or video content.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring>>.

    old_state: typing.Optional[voices.VoiceState] = attr.ib(repr=True)
    """The old voice state.

    This will be `builtins.None` if the voice state missing from the cache.
    """

    state: voices.VoiceState = attr.ib(repr=True)
    """Voice state that this update contained.

    Returns
    -------
    hikari.voices.VoiceState
        The voice state that was updated.
    """

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from VoiceEvent>>
        return self.state.guild_id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class VoiceServerUpdateEvent(VoiceEvent):
    """Event fired when a voice server is changed.

    Sent when initially connecting to voice and when the current voice instance
    falls over to a new server.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attr.ib(repr=True)
    # <<inherited docstring from VoiceEvent>>

    token: str = attr.ib(repr=False)
    """Token that should be used to authenticate with the voice gateway.

    Returns
    -------
    builtins.str
        The token to use to authenticate with the voice gateway.
    """

    raw_endpoint: str = attr.ib(repr=True)
    """Raw endpoint URI that Discord sent.

    !!! warning
        This will not contain the scheme to use. Use the `endpoint` property
        to get a representation that has this prepended.

    Returns
    -------
    builtins.str
        A scheme-less endpoint URI for the endpoint to use for a new voice
        websocket.
    """

    @property
    def endpoint(self) -> str:
        """URI for this voice server host, with the correct scheme prepended.

        Returns
        -------
        builtins.str
            The URI to use to connect to the voice gateway.
        """
        return f"wss://{self.raw_endpoint}"
