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
    "ActivityParty",
    "ActivitySecret",
    "ActivityTimestamps",
    "ActivityType",
    "ClientStatus",
    "MemberPresence",
    "RichActivity",
    "Status",
)

import typing

import attrs

from hikari import files
from hikari import snowflakes
from hikari import undefined
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import deprecation
from hikari.internal import enums
from hikari.internal import routes
from hikari.internal import typing_extensions

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
@attrs.define(kw_only=True, weakref_slot=False)
class ActivityTimestamps:
    """The datetimes for the start and/or end of an activity session."""

    start: datetime.datetime | None = attrs.field(repr=True)
    """When this activity's session was started, if applicable."""

    end: datetime.datetime | None = attrs.field(repr=True)
    """When this activity's session will end, if applicable."""


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class ActivityParty:
    """Used to represent activity groups of users."""

    id: str | None = attrs.field(hash=True, repr=True)
    """The string id of this party instance, if set."""

    current_size: int | None = attrs.field(eq=False, hash=False, repr=False)
    """Current size of this party, if applicable."""

    max_size: int | None = attrs.field(eq=False, hash=False, repr=False)
    """Maximum size of this party, if applicable."""


_DYNAMIC_URLS = {"mp": urls.MEDIA_PROXY_URL + "/{}"}


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ActivityAssets:
    """Used to represent possible assets for an activity."""

    _application_id: snowflakes.Snowflake | None = attrs.field(alias="application_id", repr=False)

    large_image: str | None = attrs.field(repr=False)
    """The ID of the asset's large image, if set."""

    large_text: str | None = attrs.field(repr=True)
    """The text that'll appear when hovering over the large image, if set."""

    small_image: str | None = attrs.field(repr=False)
    """The ID of the asset's small image, if set."""

    small_text: str | None = attrs.field(repr=True)
    """The text that'll appear when hovering over the small image, if set."""

    def _make_asset_url(
        self,
        *,
        asset: str | None,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        if asset is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        try:
            resource, identifier = asset.split(":", 1)
            return files.URL(url=_DYNAMIC_URLS[resource].format(identifier))

        except KeyError:
            msg = "Unknown asset type"
            raise RuntimeError(msg) from None

        except ValueError:
            assert self._application_id is not None

            return routes.CDN_APPLICATION_ASSET.compile_to_file(
                urls.CDN_URL,
                application_id=self._application_id,
                hash=asset,
                size=size,
                file_format=file_format,
                lossless=lossless,
            )

    @property
    @deprecation.deprecated("Use 'make_large_image_url' instead.")
    def large_image_url(self) -> files.URL | None:
        """Large image asset URL.

        !!! note
            This will be [`None`][] if no large image asset exists or if the
            asset's dynamic URL (indicated by a `{name}:` prefix) is not known.
        """
        deprecation.warn_deprecated(
            "large_image_url", removal_version="2.5.0", additional_info="Use 'make_large_image_url' instead."
        )
        try:
            return self.make_large_image_url()
        except RuntimeError:
            return None

    def make_large_image_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the large image asset URL for this application, if set.

        If no large image is set or if the asset's dynamic URL (indicated by a `{name}:` prefix)
        is not known, this returns [`None`][].

        !!! note
            `file_format`, `size`, and `lossless` are ignored for images
            hosted outside of Discord or Discord's media proxy.

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no large image exists.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        RuntimeError
            If [`hikari.presences.ActivityAssets.large_image`][] points towards an unknown asset type.
        """
        return self._make_asset_url(
            asset=self.large_image, file_format=file_format, size=size, lossless=lossless, ext=ext
        )

    @property
    @deprecation.deprecated("Use 'make_small_image_url' instead.")
    def small_image_url(self) -> files.URL | None:
        """Small image asset URL.

        !!! note
            This will be [`None`][] if no large image asset exists or if the
            asset's dynamic URL (indicated by a `{name}:` prefix) is not known.
        """
        deprecation.warn_deprecated(
            "small_image_url", removal_version="2.5.0", additional_info="Use 'make_small_image_url' instead."
        )
        try:
            return self.make_small_image_url()
        except RuntimeError:
            return None

    def make_small_image_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the small image asset URL for this application, if set.

        If no small image is set or if the asset's dynamic URL (indicated by a `{name}:` prefix)
        is not known, this returns [`None`][].

        !!! note
            `file_format`, `size`, and `lossless` are ignored for images
            hosted outside of Discord or Discord's media proxy.

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no small image exists.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        RuntimeError
            If [`hikari.presences.ActivityAssets.small_image`][] points towards an unknown asset type.
        """
        return self._make_asset_url(
            asset=self.small_image, file_format=file_format, size=size, lossless=lossless, ext=ext
        )


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ActivitySecret:
    """The secrets used for interacting with an activity party."""

    join: str | None = attrs.field(repr=False)
    """The secret used for joining a party, if applicable."""

    spectate: str | None = attrs.field(repr=False)
    """The secret used for spectating a party, if applicable."""

    match: str | None = attrs.field(repr=False)
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
@attrs.define(kw_only=True, weakref_slot=False)
class Activity:
    """Represents a regular activity that can be associated with a presence."""

    name: str = attrs.field()
    """The activity name."""

    state: str | None = attrs.field(default=None)
    """The activities state, if set.

    This field can be use to set a custom status or provide more information
    on the activity.
    """

    url: str | None = attrs.field(default=None, repr=False)
    """The activity URL, if set.

    Only valid for [`hikari.presences.ActivityType.STREAMING`][] activities.
    """

    type: ActivityType | int = attrs.field(converter=ActivityType, default=ActivityType.PLAYING)
    """The activity type."""

    @typing_extensions.override
    def __str__(self) -> str:
        return self.name


@attrs.define(kw_only=True, weakref_slot=False)
class RichActivity(Activity):
    """Represents a rich activity that can be associated with a presence."""

    created_at: datetime.datetime = attrs.field(repr=False)
    """When this activity was added to the user's session."""

    timestamps: ActivityTimestamps | None = attrs.field(repr=False)
    """The timestamps for when this activity's current state will start and end, if applicable."""

    application_id: snowflakes.Snowflake | None = attrs.field(repr=False)
    """The ID of the application this activity is for, if applicable."""

    details: str | None = attrs.field(repr=False)
    """The text that describes what the activity's target is doing, if set."""

    emoji: emojis_.Emoji | None = attrs.field(repr=False)
    """The emoji of this activity, if it is a custom status and set."""

    party: ActivityParty | None = attrs.field(repr=False)
    """Information about the party associated with this activity, if set."""

    assets: ActivityAssets | None = attrs.field(repr=False)
    """Images and their hover over text for the activity."""

    secrets: ActivitySecret | None = attrs.field(repr=False)
    """Secrets for Rich Presence joining and spectating."""

    is_instance: bool | None = attrs.field(repr=False)
    """Whether this activity is an instanced game session."""

    flags: ActivityFlag | None = attrs.field(repr=False)
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
@attrs.define(kw_only=True, weakref_slot=False)
class ClientStatus:
    """The client statuses for this member."""

    desktop: Status | str = attrs.field(repr=True)
    """The status of the target user's desktop session."""

    mobile: Status | str = attrs.field(repr=True)
    """The status of the target user's mobile session."""

    web: Status | str = attrs.field(repr=True)
    """The status of the target user's web session."""


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
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

    visible_status: Status | str = attrs.field(eq=False, hash=False, repr=True)
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
