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
"""Components and entities related to discord's Oauth2 flow."""

from __future__ import annotations

__all__ = [
    "Application",
    "ApplicationOwner",
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

from hikari import bases
from hikari import guilds
from hikari import permissions
from hikari import users
from hikari.internal import marshaller
from hikari.internal import more_enums
from hikari.internal import urls

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing


@more_enums.must_be_unique
class OAuth2Scope(str, more_enums.Enum):
    """OAuth2 Scopes that Discord allows.

    These are categories of permissions for applications using the OAuth2 API
    directly. Most users will only ever need the `BOT` scope when developing
    bots.
    """

    ACTIVITIES_READ = "activities.read"
    """Enable the app to fetch a user's "Now Playing/Recently Played" list.

    !!! note
        You must be whitelisted to use this scope.
    """

    ACTIVITIES_WRITE = "activities.write"
    """Enable the app to update a user's activity.

    !!! note
        You must be whitelisted to use this scope.

    !!! note
        This is not required to use the GameSDK activity manager.
    """

    APPLICATIONS_BUILDS_READ = "applications.builds.read"
    """Enable the app to read build data for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_BUILDS_UPLOAD = "applications.builds.upload"
    """Enable the app to upload/update builds for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_ENTITLEMENTS = "applications.entitlements"
    """Enable the app to read entitlements for a user's applications."""

    APPLICATIONS_STORE_UPDATE = "applications.store.update"
    """Enable the app to read and update store data for the user's applications.

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
    """Enable the app to view third-party linked accounts such as Twitch."""

    EMAIL = "email"
    """Enable the app to view the user's email and application info."""

    GROUP_DM_JOIN = "gdm.join"
    """Enable the application to join users into a group DM."""

    GUILDS = "guilds"
    """Enable the app to view the guilds the user is in."""

    GUILDS_JOIN = "guilds.join"
    """Enable the app to add the user to a specific guild.

    !!! note
        This requires you to have set up a bot account for your application.
    """

    IDENTIFY = "identify"
    """Enable the app to view info about itself.

    !!! note
        This does not include email address info. Use the `EMAIL` scope instead
        to retrieve this information.
    """

    RELATIONSHIPS_READ = "relationships.read"
    """Enable the app to view a user's friend list.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC = "rpc"
    """Enable the RPC app to control the local user's Discord client.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC_API = "rpc.api"
    """Enable the RPC app to access the RPC API as the local user.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC_MESSAGES_READ = "messages.read"
    """Enable the RPC app to read messages from all channels the user is in."""

    RPC_NOTIFICATIONS_READ = "rpc.notifications.read"
    """Enable the RPC app to read  from all channels the user is in.

    !!! note
        You must be whitelisted to use this scope.
    """

    WEBHOOK_INCOMING = "webhook.incoming"
    """Used to generate a webhook that is returned in the OAuth2 token response.

    This is used during authorization code grants.
    """


@more_enums.must_be_unique
class ConnectionVisibility(int, more_enums.Enum):
    """Describes who can see a connection with a third party account."""

    NONE = 0
    """Only you can see the connection."""

    EVERYONE = 1
    """Everyone can see the connection."""


def _deserialize_integrations(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Sequence[guilds.GuildIntegration]:
    return [guilds.PartialGuildIntegration.deserialize(integration, **kwargs) for integration in payload]


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class OwnConnection(bases.Entity, marshaller.Deserializable):
    """Represents a user's connection with a third party account.

    Returned by the `GET Current User Connections` endpoint.
    """

    id: str = marshaller.attrib(deserializer=str, eq=True, hash=True, repr=True)
    """The string ID of the third party connected account.

    !!! warning
        Seeing as this is a third party ID, it will not be a snowflake.
    """

    name: str = marshaller.attrib(deserializer=str, eq=False, hash=False, repr=True)
    """The username of the connected account."""

    type: str = marshaller.attrib(deserializer=str, eq=False, hash=False, repr=True)
    """The type of service this connection is for."""

    is_revoked: bool = marshaller.attrib(
        raw_name="revoked", deserializer=bool, if_undefined=False, default=False, eq=False, hash=False,
    )
    """Whether the connection has been revoked."""

    integrations: typing.Sequence[guilds.PartialGuildIntegration] = marshaller.attrib(
        deserializer=_deserialize_integrations,
        if_undefined=list,
        factory=list,
        inherit_kwargs=True,
        eq=False,
        hash=False,
    )
    """A sequence of the partial guild integration objects this connection has."""

    is_verified: bool = marshaller.attrib(raw_name="verified", deserializer=bool, eq=False, hash=False)
    """Whether the connection has been verified."""

    is_friend_syncing: bool = marshaller.attrib(raw_name="friend_sync", deserializer=bool, eq=False, hash=False)
    """Whether friends should be added based on this connection."""

    is_showing_activity: bool = marshaller.attrib(raw_name="show_activity", deserializer=bool, eq=False, hash=False)
    """Whether this connection's activities are shown in the user's presence."""

    visibility: ConnectionVisibility = marshaller.attrib(
        deserializer=ConnectionVisibility, eq=False, hash=False, repr=True
    )
    """The visibility of the connection."""


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class OwnGuild(guilds.PartialGuild):
    """Represents a user bound partial guild object."""

    is_owner: bool = marshaller.attrib(raw_name="owner", deserializer=bool, eq=False, hash=False, repr=True)
    """Whether the current user owns this guild."""

    my_permissions: permissions.Permission = marshaller.attrib(
        raw_name="permissions", deserializer=permissions.Permission, eq=False, hash=False
    )
    """The guild level permissions that apply to the current user or bot."""


@more_enums.must_be_unique
class TeamMembershipState(int, more_enums.Enum):
    """Represents the state of a user's team membership."""

    INVITED = 1
    """Denotes the user has been invited to the team but has yet to accept."""

    ACCEPTED = 2
    """Denotes the user has accepted the invite and is now a member."""


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class TeamMember(bases.Entity, marshaller.Deserializable):
    """Represents a member of a Team."""

    membership_state: TeamMembershipState = marshaller.attrib(deserializer=TeamMembershipState, eq=False, hash=False)
    """The state of this user's membership."""

    permissions: typing.Set[str] = marshaller.attrib(deserializer=set, eq=False, hash=False)
    """This member's permissions within a team.

    Will always be `["*"]` until Discord starts using this.
    """

    team_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, eq=True, hash=True, repr=True)
    """The ID of the team this member belongs to."""

    user: users.User = marshaller.attrib(
        deserializer=users.User.deserialize, inherit_kwargs=True, eq=True, hash=True, repr=True
    )
    """The user object of this team member."""


def _deserialize_members(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, TeamMember]:
    return {bases.Snowflake(member["user"]["id"]): TeamMember.deserialize(member, **kwargs) for member in payload}


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class Team(bases.Unique, marshaller.Deserializable):
    """Represents a development team, along with all its members."""

    icon_hash: typing.Optional[str] = marshaller.attrib(raw_name="icon", deserializer=str, eq=False, hash=False)
    """The hash of this team's icon, if set."""

    members: typing.Mapping[bases.Snowflake, TeamMember] = marshaller.attrib(
        deserializer=_deserialize_members, inherit_kwargs=True, eq=False, hash=False
    )
    """The member's that belong to this team."""

    owner_user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, eq=False, hash=False, repr=True)
    """The ID of this team's owner."""

    @property
    def icon_url(self) -> typing.Optional[str]:
        """URL of this team's icon, if set."""
        return self.format_icon_url()

    def format_icon_url(self, fmt: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the icon URL for this team if set.

        Parameters
        ----------
        fmt : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`. Can be any power
            of two between `16` and `4096` inclusive.

        Returns
        -------
        str, optional
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash:
            return urls.generate_cdn_url("team-icons", str(self.id), self.icon_hash, fmt=fmt, size=size)
        return None


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class ApplicationOwner(users.User):
    """Represents the user who owns an application, may be a team user."""

    flags: int = marshaller.attrib(deserializer=users.UserFlag, eq=False, hash=False, repr=True)
    """This user's flags."""

    @property
    def is_team_user(self) -> bool:
        """If this user is a Team user (the owner of an application that's owned by a team)."""
        return bool((self.flags >> 10) & 1)


def _deserialize_verify_key(payload: str) -> bytes:
    return bytes(payload, "utf-8")


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class Application(bases.Unique, marshaller.Deserializable):
    """Represents the information of an Oauth2 Application."""

    name: str = marshaller.attrib(deserializer=str, eq=False, hash=False, repr=True)
    """The name of this application."""

    description: str = marshaller.attrib(deserializer=str, eq=False, hash=False)
    """The description of this application, will be an empty string if unset."""

    is_bot_public: typing.Optional[bool] = marshaller.attrib(
        raw_name="bot_public", deserializer=bool, if_undefined=None, default=None, eq=False, hash=False, repr=True
    )
    """Whether the bot associated with this application is public.

    Will be `None` if this application doesn't have an associated bot.
    """

    is_bot_code_grant_required: typing.Optional[bool] = marshaller.attrib(
        raw_name="bot_require_code_grant", deserializer=bool, if_undefined=None, default=None, eq=False, hash=False
    )
    """Whether this application's bot is requiring code grant for invites.

    Will be `None` if this application doesn't have a bot.
    """

    owner: typing.Optional[ApplicationOwner] = marshaller.attrib(
        deserializer=ApplicationOwner.deserialize,
        if_undefined=None,
        default=None,
        inherit_kwargs=True,
        eq=False,
        hash=False,
        repr=True,
    )
    """The object of this application's owner.

    This should always be `None` in application objects retrieved outside
    Discord's oauth2 flow.
    """

    rpc_origins: typing.Optional[typing.Set[str]] = marshaller.attrib(
        deserializer=set, if_undefined=None, default=None, eq=False, hash=False
    )
    """A collection of this application's rpc origin URLs, if rpc is enabled."""

    summary: str = marshaller.attrib(deserializer=str, eq=False, hash=False)
    """This summary for this application's primary SKU if it's sold on Discord.

    Will be an empty string if unset.
    """

    verify_key: typing.Optional[bytes] = marshaller.attrib(
        deserializer=_deserialize_verify_key, if_undefined=None, default=None, eq=False, hash=False
    )
    """The base64 encoded key used for the GameSDK's `GetTicket`."""

    icon_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="icon", deserializer=str, if_undefined=None, default=None, eq=False, hash=False
    )
    """The hash of this application's icon, if set."""

    team: typing.Optional[Team] = marshaller.attrib(
        deserializer=Team.deserialize,
        if_undefined=None,
        if_none=None,
        default=None,
        eq=False,
        hash=False,
        inherit_kwargs=True,
    )
    """This application's team if it belongs to one."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_undefined=None, default=None, eq=False, hash=False
    )
    """The ID of the guild this application is linked to if sold on Discord."""

    primary_sku_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_undefined=None, default=None, eq=False, hash=False
    )
    """The ID of the primary "Game SKU" of a game that's sold on Discord."""

    slug: typing.Optional[str] = marshaller.attrib(
        deserializer=str, if_undefined=None, default=None, eq=False, hash=False
    )
    """The URL slug that links to this application's store page.

    Only applicable to applications sold on Discord.
    """

    cover_image_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="cover_image", deserializer=str, if_undefined=None, default=None, eq=False, hash=False
    )
    """The hash of this application's cover image on it's store, if set."""

    @property
    def icon_url(self) -> typing.Optional[str]:
        """URL for this team's icon, if set."""
        return self.format_icon_url()

    def format_icon_url(self, fmt: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the icon URL for this application if set.

        Parameters
        ----------
        fmt : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        str, optional
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.icon_hash:
            return urls.generate_cdn_url("app-icons", str(self.id), self.icon_hash, fmt=fmt, size=size)
        return None

    @property
    def cover_image_url(self) -> typing.Optional[str]:
        """URL for this icon's store cover image, if set."""
        return self.format_cover_image_url()

    def format_cover_image_url(self, fmt: str = "png", size: int = 4096) -> typing.Optional[str]:
        """Generate the URL for this application's store page's cover image is set and applicable.

        Parameters
        ----------
        fmt : str
            The format to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        str, optional
            The string URL.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.cover_image_hash:
            return urls.generate_cdn_url("app-assets", str(self.id), self.cover_image_hash, fmt=fmt, size=size)
        return None
