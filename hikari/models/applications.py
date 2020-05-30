#!/usr/bin/env python3
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

__all__ = [
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

from hikari.models import bases
from hikari.models import guilds
from hikari.net import urls

if typing.TYPE_CHECKING:
    from hikari.models import permissions as permissions_
    from hikari.models import users


@enum.unique
class OAuth2Scope(str, enum.Enum):
    """OAuth2 Scopes that Discord allows.

    These are categories of permissions for applications using the OAuth2 API
    directly. Most users will only ever need the `BOT` scope when developing
    bots.
    """

    ACTIVITIES_READ = "activities.read"
    """Enable the application to fetch a user's "Now Playing/Recently Played" list.

    !!! note
        You must be whitelisted to use this scope.
    """

    ACTIVITIES_WRITE = "activities.write"
    """Enable the application to update a user's activity.

    !!! note
        You must be whitelisted to use this scope.

    !!! note
        This is not required to use the GameSDK activity manager.
    """

    APPLICATIONS_BUILDS_READ = "applications.builds.read"
    """Enable the application to read build data for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_BUILDS_UPLOAD = "applications.builds.upload"
    """Enable the application to upload/update builds for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_ENTITLEMENTS = "applications.entitlements"
    """Enable the application to read entitlements for a user's applications."""

    APPLICATIONS_STORE_UPDATE = "applications.store.update"
    """Enable the application to read and update store data for the user's applications.

    This includes store listings, achievements, SKU's, etc.

    !!! note
        The store API is deprecated and may be removed in the future.
    """

    BOT = "bot"
    """Used to add OAuth2 bots to a guild.

    !!! note
        This requires you to have set up a bot account for your application.
    """

    CONNECTIONS = "connections"
    """Enable the application to view third-party linked accounts such as Twitch."""

    EMAIL = "email"
    """Enable the application to view the user's email and application info."""

    GROUP_DM_JOIN = "gdm.join"
    """Enable the application to join users into a group DM."""

    GUILDS = "guilds"
    """Enable the application to view the guilds the user is in."""

    GUILDS_JOIN = "guilds.join"
    """Enable the application to add the user to a specific guild.

    !!! note
        This requires you to have set up a bot account for your application.
    """

    IDENTIFY = "identify"
    """Enable the application to view info about itself.

    !!! note
        This does not include email address info. Use the `EMAIL` scope instead
        to retrieve this information.
    """

    RELATIONSHIPS_READ = "relationships.read"
    """Enable the application to view a user's friend list.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC = "rpc"
    """Enable the RPC application to control the local user's Discord client.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC_API = "rpc.api"
    """Enable the RPC application to access the RPC API as the local user.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC_MESSAGES_READ = "messages.read"
    """Enable the RPC application to read messages from all channels the user is in."""

    RPC_NOTIFICATIONS_READ = "rpc.notifications.read"
    """Enable the RPC application to read  from all channels the user is in.

    !!! note
        You must be whitelisted to use this scope.
    """

    WEBHOOK_INCOMING = "webhook.incoming"
    """Used to generate a webhook that is returned in the OAuth2 token response.

    This is used during authorization code grants.
    """


@enum.unique
class ConnectionVisibility(int, enum.Enum):
    """Describes who can see a connection with a third party account."""

    NONE = 0
    """Only you can see the connection."""

    EVERYONE = 1
    """Everyone can see the connection."""


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

    is_revoked: bool = attr.ib(
        eq=False, hash=False,
    )
    """Whether the connection has been revoked."""

    integrations: typing.Sequence[guilds.PartialIntegration] = attr.ib(
        eq=False, hash=False,
    )
    """A sequence of the partial guild integration objects this connection has."""

    is_verified: bool = attr.ib(eq=False, hash=False)
    """Whether the connection has been verified."""

    is_friend_syncing: bool = attr.ib(eq=False, hash=False)
    """Whether friends should be added based on this connection."""

    is_showing_activity: bool = attr.ib(eq=False, hash=False)
    """Whether this connection's activities are shown in the user's presence."""

    visibility: ConnectionVisibility = attr.ib(eq=False, hash=False, repr=True)
    """The visibility of the connection."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class OwnGuild(guilds.PartialGuild):
    """Represents a user bound partial guild object."""

    is_owner: bool = attr.ib(eq=False, hash=False, repr=True)
    """Whether the current user owns this guild."""

    my_permissions: permissions_.Permission = attr.ib(eq=False, hash=False)
    """The guild level permissions that apply to the current user or bot."""


@enum.unique
class TeamMembershipState(int, enum.Enum):
    """Represents the state of a user's team membership."""

    INVITED = 1
    """Denotes the user has been invited to the team but has yet to accept."""

    ACCEPTED = 2
    """Denotes the user has accepted the invite and is now a member."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class TeamMember(bases.Entity):
    """Represents a member of a Team."""

    membership_state: TeamMembershipState = attr.ib(eq=False, hash=False)
    """The state of this user's membership."""

    permissions: typing.Set[str] = attr.ib(eq=False, hash=False)
    """This member's permissions within a team.

    Will always be `["*"]` until Discord starts using this.
    """

    team_id: bases.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    """The ID of the team this member belongs to."""

    user: users.User = attr.ib(eq=True, hash=True, repr=True)
    """The user object of this team member."""


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Team(bases.Entity, bases.Unique):
    """Represents a development team, along with all its members."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The hash of this team's icon, if set."""

    members: typing.Mapping[bases.Snowflake, TeamMember] = attr.ib(eq=False, hash=False)
    """The member's that belong to this team."""

    owner_user_id: bases.Snowflake = attr.ib(eq=False, hash=False, repr=True)
    """The ID of this team's owner."""

    @property
    def icon_url(self) -> typing.Optional[str]:
        """URL of this team's icon, if set."""
        return self.format_icon_url()

    def format_icon_url(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the icon URL for this team if set.

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
        str | None
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash:
            return urls.generate_cdn_url("team-icons", str(self.id), self.icon_hash, format_=format_, size=size)
        return None


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=True)
class Application(bases.Entity, bases.Unique):
    """Represents the information of an Oauth2 Application."""

    name: str = attr.ib(eq=False, hash=False, repr=True)
    """The name of this application."""

    description: str = attr.ib(eq=False, hash=False)
    """The description of this application, will be an empty string if unset."""

    is_bot_public: typing.Optional[bool] = attr.ib(eq=False, hash=False, repr=True)
    """Whether the bot associated with this application is public.

    Will be `None` if this application doesn't have an associated bot.
    """

    is_bot_code_grant_required: typing.Optional[bool] = attr.ib(eq=False, hash=False)
    """Whether this application's bot is requiring code grant for invites.

    Will be `None` if this application doesn't have a bot.
    """

    owner: typing.Optional[users.User] = attr.ib(
        eq=False, hash=False, repr=True,
    )
    """The object of this application's owner.

    This should always be `None` in application objects retrieved outside
    Discord's oauth2 flow.
    """

    rpc_origins: typing.Optional[typing.Set[str]] = attr.ib(eq=False, hash=False)
    """A collection of this application's rpc origin URLs, if rpc is enabled."""

    summary: str = attr.ib(eq=False, hash=False)
    """This summary for this application's primary SKU if it's sold on Discord.

    Will be an empty string if unset.
    """

    verify_key: typing.Optional[bytes] = attr.ib(eq=False, hash=False)
    """The base64 encoded key used for the GameSDK's `GetTicket`."""

    icon_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The hash of this application's icon, if set."""

    team: typing.Optional[Team] = attr.ib(
        eq=False, hash=False,
    )
    """This application's team if it belongs to one."""

    guild_id: typing.Optional[bases.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the guild this application is linked to if sold on Discord."""

    primary_sku_id: typing.Optional[bases.Snowflake] = attr.ib(eq=False, hash=False)
    """The ID of the primary "Game SKU" of a game that's sold on Discord."""

    slug: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The URL slug that links to this application's store page.

    Only applicable to applications sold on Discord.
    """

    cover_image_hash: typing.Optional[str] = attr.ib(eq=False, hash=False)
    """The hash of this application's cover image on it's store, if set."""

    @property
    def icon_url(self) -> typing.Optional[str]:
        """URL for this team's icon, if set."""
        return self.format_icon_url()

    def format_icon_url(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the icon URL for this application if set.

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
        str | None
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash:
            return urls.generate_cdn_url("application-icons", str(self.id), self.icon_hash, format_=format_, size=size)
        return None

    @property
    def cover_image_url(self) -> typing.Optional[str]:
        """URL for this icon's store cover image, if set."""
        return self.format_cover_image_url()

    def format_cover_image_url(self, *, format_: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the URL for this application's store page's cover image is set and applicable.

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
        str | None
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.cover_image_hash:
            return urls.generate_cdn_url(
                "application-assets", str(self.id), self.cover_image_hash, format_=format_, size=size
            )
        return None
