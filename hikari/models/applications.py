# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Application and entities related to discord's Oauth2 flow."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "Application",
    "ConnectionVisibility",
    "OAuth2Scope",
    "OwnConnection",
    "OwnGuild",
    "Team",
    "TeamMember",
    "TeamMembershipState",
]

import enum
import typing

import attr

from hikari.models import guilds
from hikari.utilities import cdn
from hikari.utilities import files
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    from hikari.api import rest
    from hikari.models import permissions as permissions_
    from hikari.models import users


@enum.unique
@typing.final
class OAuth2Scope(str, enum.Enum):
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

    !!! warn
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

    def __str__(self) -> str:
        return self.name


@enum.unique
@typing.final
class ConnectionVisibility(int, enum.Enum):
    """Describes who can see a connection with a third party account."""

    NONE = 0
    """Implies that only you can see the corresponding connection."""

    EVERYONE = 1
    """Everyone can see the connection."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class OwnConnection:
    """Represents a user's connection with a third party account.

    Returned by the `GET Current User Connections` endpoint.
    """

    id: str = attr.ib(eq=True, hash=True, repr=True)
    """The string ID of the third party connected account.

    !!! warning
        Seeing as this is a third party ID, it will not be a snowflake.
    """

    name: str = attr.ib(eq=False, hash=False, repr=True)
    """The username of the connected account."""

    type: str = attr.ib(eq=False, hash=False, repr=True)
    """The type of service this connection is for."""

    is_revoked: bool = attr.ib(eq=False, hash=False, repr=False)
    """`True` if the connection has been revoked."""

    integrations: typing.Sequence[guilds.PartialIntegration] = attr.ib(eq=False, hash=False, repr=False)
    """A sequence of the partial guild integration objects this connection has."""

    is_verified: bool = attr.ib(eq=False, hash=False, repr=False)
    """`True` if the connection has been verified."""

    is_friend_sync_enabled: bool = attr.ib(eq=False, hash=False, repr=False)
    """`True` if friends should be added based on this connection."""

    is_activity_visible: bool = attr.ib(eq=False, hash=False, repr=False)
    """`True` if this connection's activities are shown in the user's presence."""

    visibility: ConnectionVisibility = attr.ib(eq=False, hash=False, repr=True)
    """The visibility of the connection."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class OwnGuild(guilds.PartialGuild):
    """Represents a user bound partial guild object."""

    is_owner: bool = attr.ib(eq=False, hash=False, repr=True)
    """`True` when the current user owns this guild."""

    my_permissions: permissions_.Permission = attr.ib(eq=False, hash=False, repr=False)
    """The guild-level permissions that apply to the current user or bot."""


@enum.unique
class TeamMembershipState(int, enum.Enum):
    """Represents the state of a user's team membership."""

    INVITED = 1
    """Denotes the user has been invited to the team but has yet to accept."""

    ACCEPTED = 2
    """Denotes the user has accepted the invite and is now a member."""

    def __str__(self) -> str:
        return self.name


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class TeamMember:
    """Represents a member of a Team."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    membership_state: TeamMembershipState = attr.ib(eq=False, hash=False, repr=False)
    """The state of this user's membership."""

    permissions: typing.Set[str] = attr.ib(eq=False, hash=False, repr=False)
    """This member's permissions within a team.

    At the time of writing, this will always be a set of one `str`, which
    will always be `"*"`. This may change in the future, however.
    """

    team_id: snowflake.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of the team this member belongs to."""

    user: users.User = attr.ib(eq=True, hash=True, repr=True)
    """The user representation of this team member."""

    def __str__(self) -> str:
        return str(self.user)


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Team(snowflake.Unique):
    """Represents a development team, along with all its members."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN hash of this team's icon.

    If no icon is provided, this will be `None`.
    """

    members: typing.Mapping[snowflake.Snowflake, TeamMember] = attr.ib(eq=False, hash=False, repr=False)
    """A mapping containing each member in this team.

    The mapping maps keys containing the member's ID to values containing the
    member object.
    """

    owner_user_id: snowflake.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of this team's owner."""

    def __str__(self) -> str:
        return f"Team {self.id}"

    @property
    def icon_url(self) -> typing.Optional[files.URL]:
        """Team icon.

        Returns
        -------
        hikari.utilities.files.URL or None
            The URL, or `None` if no icon exists.
        """
        return self.format_icon()

    def format_icon(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the icon for this team if set.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`. Can be any power
            of two between `16` and `4096` inclusive.

        Returns
        -------
        hikari.utilities.files.URL or None
            The URL, or `None` if no icon exists.

        Raises
        ------
        ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.icon_hash is None:
            return None

        return cdn.generate_cdn_url("team-icons", str(self.id), self.icon_hash, format_=format_, size=size)


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Application(snowflake.Unique):
    """Represents the information of an Oauth2 Application."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    name: str = attr.ib(eq=False, hash=False, repr=True)
    """The name of this application."""

    # TODO: default to None for consistency?
    description: str = attr.ib(eq=False, hash=False, repr=False)
    """The description of this application, or an empty string if undefined."""

    is_bot_public: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=True)
    """`True` if the bot associated with this application is public.

    Will be `None` if this application doesn't have an associated bot.
    """

    is_bot_code_grant_required: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=False)
    """`True` if this application's bot is requiring code grant for invites.

    Will be `None` if this application doesn't have a bot.
    """

    owner: typing.Optional[users.User] = attr.ib(eq=False, hash=False, repr=True)
    """The application's owner.

    This should always be `None` in application objects retrieved outside
    Discord's oauth2 flow.
    """

    rpc_origins: typing.Optional[typing.Set[str]] = attr.ib(eq=False, hash=False, repr=False)
    """A collection of this application's RPC origin URLs, if RPC is enabled."""

    summary: str = attr.ib(eq=False, hash=False, repr=False)
    """This summary for this application's primary SKU if it's sold on Discord.

    Will be an empty string if undefined.
    """

    verify_key: typing.Optional[bytes] = attr.ib(eq=False, hash=False, repr=False)
    """The base64 encoded key used for the GameSDK's `GetTicket`."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN hash of this application's icon, if set."""

    team: typing.Optional[Team] = attr.ib(eq=False, hash=False, repr=False)
    """The team this application belongs to.

    If the application is not part of a team, this will be `None`.
    """

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the guild this application is linked to if sold on Discord."""

    primary_sku_id: typing.Optional[snowflake.Snowflake] = attr.ib(eq=False, hash=False, repr=False)
    """The ID of the primary "Game SKU" of a game that's sold on Discord."""

    slug: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The URL "slug" that is used to point to this application's store page.

    Only applicable to applications sold on Discord.
    """

    cover_image_hash: typing.Optional[str] = attr.ib(eq=False, hash=False, repr=False)
    """The CDN's hash of this application's cover image, used on the store."""

    def __str__(self) -> str:
        return self.name

    @property
    def icon(self) -> typing.Optional[files.URL]:
        """Team icon, if there is one.

        Returns
        -------
        hikari.utilities.files.URL or None
            The URL, or `None` if no icon exists.
        """
        return self.format_icon()

    def format_icon(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the icon for this application.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        hikari.utilities.files.URL or None
            The URL, or `None` if no icon exists.

        Raises
        ------
        ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.icon_hash is None:
            return None

        return cdn.generate_cdn_url("application-icons", str(self.id), self.icon_hash, format_=format_, size=size)

    @property
    def cover_image(self) -> typing.Optional[files.URL]:
        """Cover image used on the store.

        Returns
        -------
        hikari.utilities.files.URL or None
            The URL, or `None` if no cover image exists.
        """
        return self.format_cover_image()

    def format_cover_image(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the cover image used in the store, if set.

        Parameters
        ----------
        format_ : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        hikari.utilities.files.URL or None
            The URL, or `None` if no cover image exists.

        Raises
        ------
        ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.cover_image_hash is None:
            return None

        return cdn.generate_cdn_url(
            "application-assets", str(self.id), self.cover_image_hash, format_=format_, size=size
        )
