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
__all__ = [
    "Application",
    "ApplicationOwner",
    "ConnectionVisibility",
    "OwnConnection",
    "OwnGuild",
    "Team",
    "TeamMember",
    "TeamMembershipState",
]

import enum
import typing

import attr

from hikari import bases
from hikari import guilds
from hikari import permissions
from hikari import users
from hikari.internal import marshaller
from hikari.internal import urls


@enum.unique
class ConnectionVisibility(enum.IntEnum):
    """Describes who can see a connection with a third party account."""

    NONE = 0
    """Only you can see the connection."""

    EVERYONE = 1
    """Everyone can see the connection."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class OwnConnection(bases.HikariEntity, marshaller.Deserializable):
    """Represents a user's connection with a third party account.

    Returned by the `GET Current User Connections` endpoint.
    """

    id: str = marshaller.attrib(deserializer=str)
    """The string ID of the third party connected account.

    !!! warning
        Seeing as this is a third party ID, it will not be a snowflake.
    """

    name: str = marshaller.attrib(deserializer=str)
    """The username of the connected account."""

    type: str = marshaller.attrib(deserializer=str)
    """The type of service this connection is for."""

    is_revoked: bool = marshaller.attrib(raw_name="revoked", deserializer=bool, if_undefined=False, default=False)
    """Whether the connection has been revoked."""

    integrations: typing.Sequence[guilds.PartialGuildIntegration] = marshaller.attrib(
        deserializer=lambda payload: [
            guilds.PartialGuildIntegration.deserialize(integration) for integration in payload
        ],
        if_undefined=list,
        factory=list,
    )
    """A sequence of the partial guild integration objects this connection has."""

    is_verified: bool = marshaller.attrib(raw_name="verified", deserializer=bool)
    """Whether the connection has been verified."""

    is_friend_syncing: bool = marshaller.attrib(raw_name="friend_sync", deserializer=bool)
    """Whether friends should be added based on this connection."""

    is_showing_activity: bool = marshaller.attrib(raw_name="show_activity", deserializer=bool)
    """Whether this connection's activities are shown in the user's presence."""

    visibility: ConnectionVisibility = marshaller.attrib(deserializer=ConnectionVisibility)
    """The visibility of the connection."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class OwnGuild(guilds.PartialGuild):
    """Represents a user bound partial guild object."""

    is_owner: bool = marshaller.attrib(raw_name="owner", deserializer=bool)
    """Whether the current user owns this guild."""

    my_permissions: permissions.Permission = marshaller.attrib(
        raw_name="permissions", deserializer=permissions.Permission
    )
    """The guild level permissions that apply to the current user or bot."""


@enum.unique
class TeamMembershipState(enum.IntEnum):
    """Represents the state of a user's team membership."""

    INVITED = 1
    """Denotes the user has been invited to the team but has yet to accept."""

    ACCEPTED = 2
    """Denotes the user has accepted the invite and is now a member."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class TeamMember(bases.HikariEntity, marshaller.Deserializable):
    """Represents a member of a Team."""

    membership_state: TeamMembershipState = marshaller.attrib(deserializer=TeamMembershipState)
    """The state of this user's membership."""

    permissions: typing.Set[str] = marshaller.attrib(deserializer=set)
    """This member's permissions within a team.

    Will always be `["*"]` until Discord starts using this.
    """

    team_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the team this member belongs to."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize)
    """The user object of this team member."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Team(bases.UniqueEntity, marshaller.Deserializable):
    """Represents a development team, along with all its members."""

    icon_hash: typing.Optional[str] = marshaller.attrib(raw_name="icon", deserializer=str)
    """The hash of this team's icon, if set."""

    members: typing.Mapping[bases.Snowflake, TeamMember] = marshaller.attrib(
        deserializer=lambda members: {m.user.id: m for m in map(TeamMember.deserialize, members)}
    )
    """The member's that belong to this team."""

    owner_user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
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
@attr.s(slots=True, kw_only=True)
class ApplicationOwner(users.User):
    """Represents the user who owns an application, may be a team user."""

    flags: int = marshaller.attrib(deserializer=users.UserFlag)
    """This user's flags."""

    @property
    def is_team_user(self) -> bool:
        """If this user is a Team user (the owner of an application that's owned by a team)."""
        return bool((self.flags >> 10) & 1)


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Application(bases.UniqueEntity, marshaller.Deserializable):
    """Represents the information of an Oauth2 Application."""

    name: str = marshaller.attrib(deserializer=str)
    """The name of this application."""

    description: str = marshaller.attrib(deserializer=str)
    """The description of this application, will be an empty string if unset."""

    is_bot_public: typing.Optional[bool] = marshaller.attrib(
        raw_name="bot_public", deserializer=bool, if_undefined=None, default=None
    )
    """Whether the bot associated with this application is public.

    Will be `None` if this application doesn't have an associated bot.
    """

    is_bot_code_grant_required: typing.Optional[bool] = marshaller.attrib(
        raw_name="bot_require_code_grant", deserializer=bool, if_undefined=None, default=None
    )
    """Whether this application's bot is requiring code grant for invites.

    Will be `None` if this application doesn't have a bot.
    """

    owner: typing.Optional[ApplicationOwner] = marshaller.attrib(
        deserializer=ApplicationOwner.deserialize, if_undefined=None, default=None
    )
    """The object of this application's owner.

    This should always be `None` in application objects retrieved outside
    Discord's oauth2 flow.
    """

    rpc_origins: typing.Optional[typing.Set[str]] = marshaller.attrib(deserializer=set, if_undefined=None, default=None)
    """A collection of this application's rpc origin URLs, if rpc is enabled."""

    summary: str = marshaller.attrib(deserializer=str)
    """This summary for this application's primary SKU if it's sold on Discord.

    Will be an empty string if unset.
    """

    verify_key: typing.Optional[bytes] = marshaller.attrib(
        deserializer=lambda key: bytes(key, "utf-8"), if_undefined=None, default=None
    )
    """The base64 encoded key used for the GameSDK's `GetTicket`."""

    icon_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="icon", deserializer=str, if_undefined=None, default=None
    )
    """The hash of this application's icon, if set."""

    team: typing.Optional[Team] = marshaller.attrib(
        deserializer=Team.deserialize, if_undefined=None, if_none=None, default=None
    )
    """This application's team if it belongs to one."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild this application is linked to if it's sold on Discord."""

    primary_sku_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the primary "Game SKU" of a game that's sold on Discord."""

    slug: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)
    """The URL slug that links to this application's store page.

    Only applicable to applications sold on Discord.
    """

    cover_image_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="cover_image", deserializer=str, if_undefined=None, default=None
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
