# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Events related to polls."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("PollVoteCreateEvent", "PollVoteDeleteEvent")

import typing

import attrs

from hikari.events import shard_events
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class BasePollVoteEvent(shard_events.ShardEvent):
    """Event base for any event that involves a user voting on a poll."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflakes.Snowflake = attrs.field()
    """ID of the user that added their vote to the poll."""

    channel_id: snowflakes.Snowflake = attrs.field()
    """ID of the channel that the poll is in."""

    message_id: snowflakes.Snowflake = attrs.field()
    """ID of the message that the poll is in."""

    guild_id: snowflakes.Snowflake | None = attrs.field()
    """ID of the guild that the poll is in."""

    answer_id: int = attrs.field()
    """ID of the answer that the user voted for."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class PollVoteCreateEvent(BasePollVoteEvent):
    """Event that is fired when a user add their vote to a poll.

    If the poll allows multiple selection, one event will be fired for each vote.
    """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class PollVoteDeleteEvent(BasePollVoteEvent):
    """Event that is fired when a user remove their vote to a poll.

    If the poll allows multiple selection, one event will be fired for each vote.
    """
