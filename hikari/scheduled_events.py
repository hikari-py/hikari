# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Application and entities that are used to describe guild scheduled events on Discord."""
from __future__ import annotations

__all__: typing.Sequence[str] = [
    "EventPiracyLevel",
    "ScheduledEventType",
    "ScheduledEventStatus",
    "ScheduledEvent",
    "ScheduledExternalEvent",
    "ScheduledStageEvent",
    "ScheduledVoiceEvent",
    "ScheduledEventUser",
]

import typing

import attr

from hikari import snowflakes
from hikari import urls
from hikari.internal import attr_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import files
    from hikari import guilds
    from hikari import traits
    from hikari import users


class EventPiracyLevel(int, enums.Enum):
    GUILD_ONLY = 2


class ScheduledEventType(int, enums.Enum):
    STAGE_INSTANCE = 1
    VOICE = 2
    EXTERNAL = 3


class ScheduledEventStatus(int, enums.Enum):
    SCHEDULED = 1
    ACTIVE = 2
    COMPLETED = 3
    CANCELED = 4
    CANCELLED = CANCELED


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class ScheduledEvent(snowflakes.Unique):
    # entity_id is ignored right now due to always being null
    # creator_id is ignored as it just dupes creator.id

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    guild_id: snowflakes.Snowflake = attr.field(hash=False, repr=True)
    name: str = attr.field(hash=False, repr=True)
    description: typing.Optional[str] = attr.field(hash=False, repr=False)
    start_time: datetime.datetime = attr.field(hash=False, repr=False)
    end_time: typing.Optional[datetime.datetime] = attr.field(hash=False, repr=False)
    privacy_level: EventPiracyLevel = attr.field(hash=False, repr=False)
    status: ScheduledEventStatus = attr.field(hash=False, repr=True)
    entity_type: ScheduledEventType = attr.field(hash=False, repr=True)
    creator: typing.Optional[users.User] = attr.field(hash=False, repr=False)
    user_count: typing.Optional[int] = attr.field(hash=False, repr=False)
    # user_count is None on gateway events and when creating/editing an event
    image_hash: typing.Optional[str] = attr.field(hash=False, repr=False)

    @property
    def image_url(self) -> typing.Optional[files.URL]:
        """Cover image for this scheduled event, if set."""
        return self.make_icon_url()

    def make_icon_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the cover image for this scheduled event, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no cover image is set.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two between 16 and 4096 (inclusive).
        """
        if self.image_hash is None:
            return None

        return routes.SCHEDULED_EVENT_COVER.compile_to_file(
            urls.CDN_URL,
            scheduled_event_id=self.id,
            hash=self.image_hash,
            size=size,
            file_format=ext,
        )


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class ScheduledExternalEvent(ScheduledEvent):
    location: str = attr.field(hash=False, repr=False)
    end_time: datetime.datetime = attr.field(hash=False, repr=False)


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class ScheduledStageEvent(ScheduledEvent):
    channel_id: snowflakes.Snowflake = attr.field(hash=False, repr=False)


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class ScheduledVoiceEvent(ScheduledEvent):
    channel_id: snowflakes.Snowflake = attr.field(hash=False, repr=False)


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class ScheduledEventUser:
    event_id: snowflakes.Snowflake = attr.field(hash=False, repr=True)
    user: users.User = attr.field(hash=True, repr=True)
    member: typing.Optional[guilds.Member] = attr.field(hash=False, repr=False)
