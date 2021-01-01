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
"""Application and entities that are used to describe guilds on Discord."""

from __future__ import annotations

__all__: typing.List[str] = [
    "Activity",
    "ActivityAssets",
    "ActivityFlag",
    "ActivitySecret",
    "ActivityTimestamps",
    "ActivityType",
    "ActivityParty",
    "ClientStatus",
    "MemberPresence",
    "RichActivity",
    "Status",
]

import typing

import attr

from hikari import snowflakes
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime

    from hikari import emojis as emojis_
    from hikari import traits


@typing.final
class ActivityType(int, enums.Enum):
    """The activity type."""

    PLAYING = 0
    """Shows up as `Playing <name>`"""

    STREAMING = 1
    """Shows up as `Streaming` and links to a Twitch or YouTube stream/video.

    !!! warning
        You **MUST** provide a valid Twitch or YouTube stream URL to the
        activity you create in order for this to be valid. If you fail to
        do this, then the activity **WILL NOT** update.
    """

    LISTENING = 2
    """Shows up as `Listening to <name>`."""

    WATCHING = 3
    """Shows up as `Watching <name>`.

    !!! warning
        This is not documented by Discord, and was supposedly going to be
        removed a long time ago, but that never happened. This may be
        removed at any time without warning by Discord, so use this at
        your own risk.
    """

    CUSTOM = 4
    """A custom status.

    To set an emoji with the status, place a unicode emoji or Discord emoji
    (`:smiley:`) as the first part of the status activity name.

    !!! warning
        Bots **DO NOT** support setting custom statuses.
    """

    COMPETING = 5
    """Shows up as `Competing in <name>`."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class ActivityTimestamps:
    """The datetimes for the start and/or end of an activity session."""

    start: typing.Optional[datetime.datetime] = attr.ib(repr=True)
    """When this activity's session was started, if applicable."""

    end: typing.Optional[datetime.datetime] = attr.ib(repr=True)
    """When this activity's session will end, if applicable."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class ActivityParty:
    """Used to represent activity groups of users."""

    id: typing.Optional[str] = attr.ib(eq=True, hash=True, repr=True)
    """The string id of this party instance, if set."""

    current_size: typing.Optional[int] = attr.ib(eq=False, hash=False, repr=False)
    """Current size of this party, if applicable."""

    max_size: typing.Optional[int] = attr.ib(eq=False, hash=False, repr=False)
    """Maximum size of this party, if applicable."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class ActivityAssets:
    """Used to represent possible assets for an activity."""

    large_image: typing.Optional[str] = attr.ib(repr=False)
    """The ID of the asset's large image, if set."""

    large_text: typing.Optional[str] = attr.ib(repr=False)
    """The text that'll appear when hovering over the large image, if set."""

    small_image: typing.Optional[str] = attr.ib(repr=False)
    """The ID of the asset's small image, if set."""

    small_text: typing.Optional[str] = attr.ib(repr=False)
    """The text that'll appear when hovering over the small image, if set."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class ActivitySecret:
    """The secrets used for interacting with an activity party."""

    join: typing.Optional[str] = attr.ib(repr=False)
    """The secret used for joining a party, if applicable."""

    spectate: typing.Optional[str] = attr.ib(repr=False)
    """The secret used for spectating a party, if applicable."""

    match: typing.Optional[str] = attr.ib(repr=False)
    """The secret used for matching a party, if applicable."""


@typing.final
class ActivityFlag(enums.Flag):
    """Flags that describe what an activity includes.

    This can be more than one using bitwise-combinations.
    """

    INSTANCE = 1 << 0
    """Instance"""

    JOIN = 1 << 1
    """Join"""

    SPECTATE = 1 << 2
    """Spectate"""

    JOIN_REQUEST = 1 << 3
    """Join Request"""

    SYNC = 1 << 4
    """Sync"""

    PLAY = 1 << 5
    """Play"""


# TODO: add strict type checking to gateway for this type in an invariant way.
@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class Activity:
    """Represents a regular activity that can be associated with a presence."""

    name: str = attr.ib()
    """The activity name."""

    url: typing.Optional[str] = attr.ib(default=None, repr=False)
    """The activity URL. Only valid for `STREAMING` activities."""

    type: typing.Union[ActivityType, int] = attr.ib(converter=ActivityType, default=ActivityType.PLAYING)
    """The activity type."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class RichActivity(Activity):
    """Represents a rich activity that can be associated with a presence."""

    created_at: datetime.datetime = attr.ib(repr=False)
    """When this activity was added to the user's session."""

    timestamps: typing.Optional[ActivityTimestamps] = attr.ib(repr=False)
    """The timestamps for when this activity's current state will start and
    end, if applicable.
    """

    application_id: typing.Optional[snowflakes.Snowflake] = attr.ib(repr=False)
    """The ID of the application this activity is for, if applicable."""

    details: typing.Optional[str] = attr.ib(repr=False)
    """The text that describes what the activity's target is doing, if set."""

    state: typing.Optional[str] = attr.ib(repr=False)
    """The current status of this activity's target, if set."""

    emoji: typing.Optional[emojis_.Emoji] = attr.ib(repr=False)
    """The emoji of this activity, if it is a custom status and set."""

    party: typing.Optional[ActivityParty] = attr.ib(repr=False)
    """Information about the party associated with this activity, if set."""

    assets: typing.Optional[ActivityAssets] = attr.ib(repr=False)
    """Images and their hover over text for the activity."""

    secrets: typing.Optional[ActivitySecret] = attr.ib(repr=False)
    """Secrets for Rich Presence joining and spectating."""

    is_instance: typing.Optional[bool] = attr.ib(repr=False)
    """Whether this activity is an instanced game session."""

    flags: typing.Optional[ActivityFlag] = attr.ib(repr=False)
    """Flags that describe what the activity includes, if present."""


@typing.final
class Status(str, enums.Enum):
    """The status of a member."""

    ONLINE = "online"
    """Online/green."""

    IDLE = "idle"
    """Idle/yellow."""

    DO_NOT_DISTURB = "dnd"
    """Do not disturb/red."""

    OFFLINE = "offline"
    """Offline or invisible/grey."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class ClientStatus:
    """The client statuses for this member."""

    desktop: typing.Union[Status, str] = attr.ib(repr=True)
    """The status of the target user's desktop session."""

    mobile: typing.Union[Status, str] = attr.ib(repr=True)
    """The status of the target user's mobile session."""

    web: typing.Union[Status, str] = attr.ib(repr=True)
    """The status of the target user's web session."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class MemberPresence:
    """Used to represent a guild member's presence."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    user_id: snowflakes.Snowflake = attr.ib(repr=True, eq=False, hash=True)
    """The ID of the user this presence belongs to."""

    guild_id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of the guild this presence belongs to."""

    visible_status: typing.Union[Status, str] = attr.ib(eq=False, hash=False, repr=True)
    """This user's current status being displayed by the client."""

    activities: typing.Sequence[RichActivity] = attr.ib(eq=False, hash=False, repr=False)
    """All active user activities.

    You can assume the first activity is the one that the GUI Discord client
    will show.
    """

    client_status: ClientStatus = attr.ib(eq=False, hash=False, repr=False)
    """Platform-specific user-statuses."""
