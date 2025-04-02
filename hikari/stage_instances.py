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
"""Application and entities that are used to describe stage instances on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("StageInstance", "StageInstancePrivacyLevel")

import typing

import attrs

from hikari import scheduled_events
from hikari import snowflakes
from hikari import traits
from hikari.internal import attrs_extensions
from hikari.internal import enums


@typing.final
class StageInstancePrivacyLevel(int, enums.Enum):
    """The privacy level of a stage instance."""

    PUBLIC = 1
    """The Stage instance is visible publicly."""

    GUILD_ONLY = 2
    """The Stage instance is visible to only guild members."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class StageInstance(snowflakes.Unique):
    """Represents a stage instance."""

    id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the stage instance."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    channel_id: snowflakes.Snowflake = attrs.field(hash=True, repr=False)
    """The channel ID of the stage instance."""

    guild_id: snowflakes.Snowflake = attrs.field(hash=True, repr=False)
    """The guild ID of the stage instance."""

    topic: str = attrs.field(eq=False, hash=False, repr=False)
    """The topic of the stage instance."""

    privacy_level: StageInstancePrivacyLevel = attrs.field(eq=False, hash=False, repr=False)
    """The privacy level of the stage instance."""

    discoverable_disabled: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether or not stage discovery is disabled."""

    scheduled_event_id: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent] | None = attrs.field(
        eq=False, hash=False, repr=False
    )
    """The ID of the scheduled event for this stage instance, if it exists."""
