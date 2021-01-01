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
"""Application and entities related to discord's Oauth2 flow."""

from __future__ import annotations

__all__: typing.List[str] = [
    "Application",
    "ConnectionVisibility",
    "OAuth2Scope",
    "OwnConnection",
    "OwnGuild",
    "Team",
    "TeamMember",
    "TeamMembershipState",
]

import typing

import attr

from hikari import files
from hikari import guilds
from hikari import snowflakes
from hikari import urls
from hikari import users
from hikari.internal import attr_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import permissions as permissions_
    from hikari import traits


@typing.final
class OAuth2Scope(str, enums.Enum):
    """OAuth2 Scopes that Discord allows.

    These are categories of permissions for applications using the OAuth2 API
    directly. Most users will only ever need the `BOT` scope when developing
    bots.
    """

    ACTIVITIES_READ = "activities.read"
    """Enables fetching the "Now Playing/Recently Played" list.

    !!! note
        You must be whitelisted to use this scope.
    """

    ACTIVITIES_WRITE = "activities.write"
    """Enables updating a user's activity.

    !!! note
        You must be whitelisted to use this scope.

    !!! note
        This is not required to use the GameSDK activity manager.
    """

    APPLICATIONS_BUILDS_READ = "applications.builds.read"
    """Enables reading build data for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_BUILDS_UPLOAD = "applications.builds.upload"
    """Enables uploading/updating builds for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_ENTITLEMENTS = "applications.entitlements"
    """Enables reading entitlements for a user's applications."""

    APPLICATIONS_STORE_UPDATE = "applications.store.update"
    """Enables reading/updating store data for the user's applications.

    This includes store listings, achievements, SKU's, etc.

    !!! note
        The store API is deprecated and may be removed in the future.
    """

    BOT = "bot"
    """Enables adding a bot application to a guild.

    !!! note
        This requires you to have set up a bot account for your application.
    """

    CONNECTIONS = "connections"
    """Enables viewing third-party linked accounts such as Twitch."""

    EMAIL = "email"
    """Enable the application to view the user's email and application info."""

    GROUP_DM_JOIN = "gdm.join"
    """Enables joining users into a group DM.

    !!! warning
        This cannot add the bot to a group DM.
    """

    GUILDS = "guilds"
    """Enables viewing the guilds the user is in."""

    GUILDS_JOIN = "guilds.join"
    """Enables adding the user to a specific guild.

    !!! note
        This requires you to have set up a bot account for your application.
    """

    IDENTIFY = "identify"
    """Enables viewing info about itself.

    !!! note
        This does not include email address info. Use the `EMAIL` scope instead
        to retrieve this information.
    """

    RELATIONSHIPS_READ = "relationships.read"
    """Enables viewing a user's friend list.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC = "rpc"
    """Enables the RPC application to control the local user's Discord client.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC_API = "rpc.api"
    """Enables the RPC application to access the RPC API as the local user.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC_MESSAGES_READ = "messages.read"
    """Enables the RPC application to read messages from all channels the user is in."""

    RPC_NOTIFICATIONS_READ = "rpc.notifications.read"
    """Enables the RPC application to read  from all channels the user is in.

    !!! note
        You must be whitelisted to use this scope.
    """

    WEBHOOK_INCOMING = "webhook.incoming"
    """Used to generate a webhook that is returned in the OAuth2 token response.

    This is used during authorization code grants.
    """


@typing.final
class ConnectionVisibility(int, enums.Enum):
    """Describes who can see a connection with a third party account."""

    NONE = 0
    """Implies that only you can see the corresponding connection."""

    EVERYONE = 1
    """Everyone can see the connection."""


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class OwnConnection:
    """Represents a user's connection with a third party account.

    Returned by the `GET Current User Connections` endpoint.
    """

    id: str = attr.ib(eq=True, hash=True, repr=True)
    """The string ID of the third party connected account.

    !!! warning
        Seeing as this is a third party ID, it will not be a snowflakes.
    """

    name: str = attr.ib(eq=False, hash=False, repr=True)
    """The username of the connected account."""

    type: str = attr.ib(eq=False, hash=False, repr=True)
    """The type of service this connection is for."""

    is_revoked: bool = attr.ib(eq=False, hash=False, repr=False)
    """`builtins.True` if the connection has been revoked."""

    integrations: typing.Sequence[guilds.PartialIntegration] = attr.ib(eq=False, hash=False, repr=False)
    """A sequence of the partial guild integration objects this connection has."""

    is_verified: bool = attr.ib(eq=False, hash=False, repr=False)
    """`builtins.True` if the connection has been verified."""

    is_friend_sync_enabled: bool = attr.ib(eq=False, hash=False, repr=False)
    """`builtins.True` if friends should be added based on this connection."""

    is_activity_visible: bool = attr.ib(eq=False, hash=False, repr=False)
    """`builtins.True` if this connection's activities are shown in the user's presence."""

    visibility: typing.Union[ConnectionVisibility, int] = attr.ib(eq=False, hash=False, repr=True)
    """The visibility of the connection."""


@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class OwnGuild(guilds.PartialGuild):
    """Represents a user bound partial guild object."""

    features: typing.Sequence[guilds.GuildFeatureish] = attr.ib(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    is_owner: bool = attr.ib(eq=False, hash=False, repr=True)
    """`builtins.True` when the current user owns this guild."""

    my_permissions: permissions_.Permissions = attr.ib(eq=False, hash=False, repr=False)
    """The guild-level permissions that apply to the current user or bot."""


@typing.final
class TeamMembershipState(int, enums.Enum):
    """Represents the state of a user's team membership."""

    INVITED = 1
    """Denotes the user has been invited to the team but has yet to accept."""

    ACCEPTED = 2
    """Denotes the user has accepted the invite and is now a member."""


@attr_extensions.with_copy
@attr.s(eq=False, hash=False, init=True, kw_only=True, slots=True, weakref_slot=False)
class TeamMember(users.User):
    """Represents a member of a Team."""

    membership_state: typing.Union[TeamMembershipState, int] = attr.ib(repr=False)
    """The state of this user's membership."""

    permissions: typing.Sequence[str] = attr.ib(repr=False)
    """This member's permissions within a team.

    At the time of writing, this will always be a sequence of one `builtins.str`,
    which will always be `"*"`. This may change in the future, however.
    """

    team_id: snowflakes.Snowflake = attr.ib(repr=True)
    """The ID of the team this member belongs to."""

    user: users.User = attr.ib(repr=True)
    """The user representation of this team member."""

    @property
    def app(self) -> traits.RESTAware:
        """Return the app that is bound to the user object."""
        return self.user.app

    @property
    def avatar_hash(self) -> typing.Optional[str]:
        return self.user.avatar_hash

    @property
    def avatar_url(self) -> typing.Optional[files.URL]:
        return self.user.avatar_url

    @property
    def default_avatar_url(self) -> files.URL:
        return self.user.default_avatar_url

    @property
    def discriminator(self) -> str:
        return self.user.discriminator

    @property
    def flags(self) -> users.UserFlag:
        return self.user.flags

    @property
    def id(self) -> snowflakes.Snowflake:
        return self.user.id

    @id.setter
    def id(self, value: snowflakes.Snowflake) -> None:
        raise TypeError("Cannot mutate the ID of a member")

    @property
    def is_bot(self) -> bool:
        return self.user.is_bot

    @property
    def is_system(self) -> bool:
        return self.user.is_system

    @property
    def mention(self) -> str:
        return self.user.mention

    @property
    def username(self) -> str:
        return self.user.username

    async def fetch_dm_channel(self) -> channels.DMChannel:
        return await self.user.fetch_dm_channel()

    def __str__(self) -> str:
        return str(self.user)

    def __hash__(self) -> int:
        return hash(self.user)

    def __eq__(self, other: object) -> bool:
        return self.user == other


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Team(snowflakes.Unique):
    """Represents a development team, along with all its members."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN hash of this team's icon.

    If no icon is provided, this will be `builtins.None`.
    """

    members: typing.Mapping[snowflakes.Snowflake, TeamMember] = attr.ib(eq=False, hash=False, repr=False)
    """A mapping containing each member in this team.

    The mapping maps keys containing the member's ID to values containing the
    member object.
    """

    owner_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of this team's owner."""

    def __str__(self) -> str:
        return f"Team {self.id}"

    @property
    def icon_url(self) -> typing.Optional[files.URL]:
        """Team icon.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no icon exists.
        """
        return self.format_icon()

    def format_icon(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the icon for this team if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`. Can be any power
            of two between `16` and `4096` inclusive.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no icon exists.

        Raises
        ------
        builtins.ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.icon_hash is None:
            return None

        return routes.CDN_TEAM_ICON.compile_to_file(
            urls.CDN_URL,
            team_id=self.id,
            hash=self.icon_hash,
            size=size,
            file_format=ext,
        )


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class Application(guilds.PartialApplication):
    """Represents the information of an Oauth2 Application."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    is_bot_public: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=True)
    """`builtins.True` if the bot associated with this application is public.

    Will be `builtins.None` if this application doesn't have an associated bot.
    """

    is_bot_code_grant_required: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=False)
    """`builtins.True` if this application's bot is requiring code grant for invites.

    Will be `builtins.None` if this application doesn't have a bot.
    """

    owner: users.User = attr.ib(eq=False, hash=False, repr=True)
    """The application's owner."""

    rpc_origins: typing.Optional[typing.Sequence[str]] = attr.ib(eq=False, hash=False, repr=False)
    """A collection of this application's RPC origin URLs, if RPC is enabled."""

    verify_key: typing.Optional[bytes] = attr.ib(eq=False, hash=False, repr=False)
    """The base64 encoded key used for the GameSDK's `GetTicket`."""

    team: typing.Optional[Team] = attr.ib(eq=False, hash=False, repr=False)
    """The team this application belongs to.

    If the application is not part of a team, this will be `builtins.None`.
    """

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the guild this application is linked to if sold on Discord."""

    primary_sku_id: typing.Optional[snowflakes.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the primary "Game SKU" of a game that's sold on Discord."""

    slug: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The URL "slug" that is used to point to this application's store page.

    Only applicable to applications sold on Discord.
    """

    cover_image_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN's hash of this application's cover image, used on the store."""

    @property
    def cover_image_url(self) -> typing.Optional[files.URL]:
        """Cover image used on the store.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no cover image exists.
        """
        return self.format_cover_image()

    def format_cover_image(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the cover image used in the store, if set.

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
            The URL, or `builtins.None` if no cover image exists.

        Raises
        ------
        builtins.ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.cover_image_hash is None:
            return None

        return routes.CDN_APPLICATION_COVER.compile_to_file(
            urls.CDN_URL,
            application_id=self.id,
            hash=self.cover_image_hash,
            size=size,
            file_format=ext,
        )
