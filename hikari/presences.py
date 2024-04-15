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
"""Application and entities that are used to describe guilds on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
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
)

import typing

import attrs

from hikari import files
from hikari import snowflakes
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import emojis as emojis_
    from hikari import guilds
    from hikari import traits
    from hikari import users


@typing.final
class ActivityType(int, enums.Enum):
    """The activity type."""

    PLAYING = 0
    """Shows up as `Playing <name>`."""

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
    """Shows up as `Watching <name>`."""

    CUSTOM = 4
    """Shows up as `<emoji> <name>`.

    !!! warning
        As of the time of writing, emoji cannot be used by bot accounts.
    """

    COMPETING = 5
    """Shows up as `Competing in <name>`."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class ActivityTimestamps:
    """The datetimes for the start and/or end of an activity session."""

    start: typing.Optional[datetime.datetime] = attrs.field(repr=True)
    """When this activity's session was started, if applicable."""

    end: typing.Optional[datetime.datetime] = attrs.field(repr=True)
    """When this activity's session will end, if applicable."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class ActivityParty:
    """Used to represent activity groups of users."""

    id: typing.Optional[str] = attrs.field(hash=True, repr=True)
    """The string id of this party instance, if set."""

    current_size: typing.Optional[int] = attrs.field(eq=False, hash=False, repr=False)
    """Current size of this party, if applicable."""

    max_size: typing.Optional[int] = attrs.field(eq=False, hash=False, repr=False)
    """Maximum size of this party, if applicable."""


_DYNAMIC_URLS = {"mp": urls.MEDIA_PROXY_URL + "/{}"}


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class ActivityAssets:
    """Used to represent possible assets for an activity."""

    _application_id: typing.Optional[snowflakes.Snowflake] = attrs.field(alias="application_id", repr=False)

    large_image: typing.Optional[str] = attrs.field(repr=False)
    """The ID of the asset's large image, if set."""

    large_text: typing.Optional[str] = attrs.field(repr=True)
    """The text that'll appear when hovering over the large image, if set."""

    small_image: typing.Optional[str] = attrs.field(repr=False)
    """The ID of the asset's small image, if set."""

    small_text: typing.Optional[str] = attrs.field(repr=True)
    """The text that'll appear when hovering over the small image, if set."""

    def _make_asset_url(self, asset: typing.Optional[str], ext: str, size: int) -> typing.Optional[files.URL]:
        if asset is None:
            return None

        try:
            resource, identifier = asset.split(":", 1)
            return files.URL(url=_DYNAMIC_URLS[resource].format(identifier))

        except KeyError:
            raise RuntimeError("Unknown asset type") from None

        except ValueError:
            assert self._application_id is not None
            return routes.CDN_APPLICATION_ASSET.compile_to_file(
                urls.CDN_URL, application_id=self._application_id, hash=asset, size=size, file_format=ext
            )

    @property
    def large_image_url(self) -> typing.Optional[files.URL]:
        """Large image asset URL.

        !!! note
            This will be [`None`][] if no large image asset exists or if the
            asset's dynamic URL (indicated by a `{name}:` prefix) is not known.
        """
        try:
            return self.make_large_image_url()

        except RuntimeError:
            return None

    def make_large_image_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the large image asset URL for this application.

        !!! note
            `ext` and `size` are ignored for images hosted outside of Discord
            or on Discord's media proxy.

        Parameters
        ----------
        ext : str
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no icon exists.

        Raises
        ------
        ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        RuntimeError
            If [`hikari.presences.ActivityAssets.large_image`][] points towards an unknown asset type.
        """
        return self._make_asset_url(self.large_image, ext, size)

    @property
    def small_image_url(self) -> typing.Optional[files.URL]:
        """Small image asset URL.

        !!! note
            This will be [`None`][] if no large image asset exists or if the
            asset's dynamic URL (indicated by a `{name}:` prefix) is not known.
        """
        try:
            return self.make_small_image_url()

        except RuntimeError:
            return None

    def make_small_image_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the small image asset URL for this application.

        Parameters
        ----------
        ext : str
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no icon exists.

        Raises
        ------
        ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        RuntimeError
            If [`hikari.presences.ActivityAssets.small_image`][] points towards an unknown asset type.
        """
        return self._make_asset_url(self.small_image, ext, size)


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class ActivitySecret:
    """The secrets used for interacting with an activity party."""

    join: typing.Optional[str] = attrs.field(repr=False)
    """The secret used for joining a party, if applicable."""

    spectate: typing.Optional[str] = attrs.field(repr=False)
    """The secret used for spectating a party, if applicable."""

    match: typing.Optional[str] = attrs.field(repr=False)
    """The secret used for matching a party, if applicable."""


@typing.final
class ActivityFlag(enums.Flag):
    """Flags that describe what an activity includes.

    This can be more than one using bitwise-combinations.
    """

    INSTANCE = 1 << 0
    """Instance."""

    JOIN = 1 << 1
    """Join."""

    SPECTATE = 1 << 2
    """Spectate."""

    JOIN_REQUEST = 1 << 3
    """Join Request."""

    SYNC = 1 << 4
    """Sync."""

    PLAY = 1 << 5
    """Play."""

    PARTY_PRIVACY_FRIENDS = 1 << 6
    """Party privacy: friends only."""

    PARTY_PRIVACY_VOICE_CHANNEL = 1 << 7
    """Party privacy: voice channel only."""

    EMBEDDED = 1 << 8
    """An activity that's embedded into a voice channel."""


# TODO: add strict type checking to gateway for this type in an invariant way.
@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class Activity:
    """Represents a regular activity that can be associated with a presence."""

    name: str = attrs.field()
    """The activity name."""

    state: typing.Optional[str] = attrs.field(default=None)
    """The activities state, if set.

    This field can be use to set a custom status or provide more information
    on the activity.
    """

    url: typing.Optional[str] = attrs.field(default=None, repr=False)
    """The activity URL, if set.

    Only valid for [`hikari.presences.ActivityType.STREAMING`][] activities.
    """

    type: typing.Union[ActivityType, int] = attrs.field(converter=ActivityType, default=ActivityType.PLAYING)
    """The activity type."""

    def __str__(self) -> str:
        return self.name


@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class RichActivity(Activity):
    """Represents a rich activity that can be associated with a presence."""

    created_at: datetime.datetime = attrs.field(repr=False)
    """When this activity was added to the user's session."""

    timestamps: typing.Optional[ActivityTimestamps] = attrs.field(repr=False)
    """The timestamps for when this activity's current state will start and end, if applicable."""

    application_id: typing.Optional[snowflakes.Snowflake] = attrs.field(repr=False)
    """The ID of the application this activity is for, if applicable."""

    details: typing.Optional[str] = attrs.field(repr=False)
    """The text that describes what the activity's target is doing, if set."""

    emoji: typing.Optional[emojis_.Emoji] = attrs.field(repr=False)
    """The emoji of this activity, if it is a custom status and set."""

    party: typing.Optional[ActivityParty] = attrs.field(repr=False)
    """Information about the party associated with this activity, if set."""

    assets: typing.Optional[ActivityAssets] = attrs.field(repr=False)
    """Images and their hover over text for the activity."""

    secrets: typing.Optional[ActivitySecret] = attrs.field(repr=False)
    """Secrets for Rich Presence joining and spectating."""

    is_instance: typing.Optional[bool] = attrs.field(repr=False)
    """Whether this activity is an instanced game session."""

    flags: typing.Optional[ActivityFlag] = attrs.field(repr=False)
    """Flags that describe what the activity includes, if present."""

    buttons: typing.Sequence[str] = attrs.field(repr=False)
    """A sequence of up to 2 of the button labels shown in this rich presence."""


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


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class ClientStatus:
    """The client statuses for this member."""

    desktop: typing.Union[Status, str] = attrs.field(repr=True)
    """The status of the target user's desktop session."""

    mobile: typing.Union[Status, str] = attrs.field(repr=True)
    """The status of the target user's mobile session."""

    web: typing.Union[Status, str] = attrs.field(repr=True)
    """The status of the target user's web session."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class MemberPresence:
    """Used to represent a guild member's presence."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    user_id: snowflakes.Snowflake = attrs.field(repr=True, hash=True)
    """The ID of the user this presence belongs to."""

    guild_id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of the guild this presence belongs to."""

    visible_status: typing.Union[Status, str] = attrs.field(eq=False, hash=False, repr=True)
    """This user's current status being displayed by the client."""

    activities: typing.Sequence[RichActivity] = attrs.field(eq=False, hash=False, repr=False)
    """All active user activities.

    You can assume the first activity is the one that the GUI Discord client
    will show.
    """

    client_status: ClientStatus = attrs.field(eq=False, hash=False, repr=False)
    """Platform-specific user-statuses."""

    async def fetch_user(self) -> users.User:
        """Fetch the user this presence is for.

        Returns
        -------
        hikari.users.User
            The requested user.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_user(self.user_id)

    async def fetch_member(self) -> guilds.Member:
        """Fetch the member this presence is for.

        Returns
        -------
        hikari.guilds.Member
            The requested member.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_member(self.guild_id, self.user_id)
