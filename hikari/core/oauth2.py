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
__all__ = ["Application", "Owner", "OwnGuild", "Team", "TeamMember", "TeamMembershipState"]

import enum
import typing

from hikari.core import entities
from hikari.core import guilds
from hikari.core import permissions
from hikari.core import snowflakes
from hikari.core import users
from hikari.internal_utilities import cdn
from hikari.internal_utilities import marshaller


@marshaller.attrs(slots=True)
class OwnGuild(guilds.PartialGuild):
    """Represents a user bound partial guild object,
    returned by GET Current User Guilds.
    """

    #: Whether the current user owns this guild.
    #:
    #: :type: :obj:`bool`
    is_owner: bool = marshaller.attrib(raw_name="owner", deserializer=bool)

    #: The guild level permissions that apply to the current user or bot.
    #:
    #: :type: :obj:`permissions.Permission`
    my_permissions: permissions.Permission = marshaller.attrib(
        raw_name="permissions", deserializer=permissions.Permission
    )


@enum.unique
class TeamMembershipState(enum.IntEnum):
    """Represents the state of a user's team membership."""

    #: Denotes the user has been invited to the team but has yet to accept.
    INVITED = 1

    #: Denotes the user has accepted the invite and is now a member.
    ACCEPTED = 2


@marshaller.attrs(slots=True)
class TeamMember(entities.HikariEntity, entities.Deserializable):
    """Represents a member of a Team."""

    #: The state of this user's membership.
    #:
    #: :type: :obj:`TeamMembershipState`
    membership_state: TeamMembershipState = marshaller.attrib(deserializer=TeamMembershipState)

    #: This member's permissions within a team.
    #: Will always be ``["*"]`` until Discord starts using this.
    #:
    #: :type: :obj:`typing.Set` [ :obj:`str` ]
    permissions: typing.Set[str] = marshaller.attrib(deserializer=lambda permissions: {p for p in permissions})

    #: The ID of the team this member belongs to.
    #:
    #: :type: :obj:`snowflakes.Snowflake`
    team_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake)

    #: The user object of this team member.
    #:
    #: :type: :obj:`TeamUser`
    user: users.User = marshaller.attrib(deserializer=users.User.deserialize)


@marshaller.attrs(slots=True)
class Team(snowflakes.UniqueEntity, entities.Deserializable):
    """This represents a Team and it's members."""

    #: The hash of this team's icon, if set.
    #:
    #: :type: :obj:`str`, optional
    icon_hash: typing.Optional[str] = marshaller.attrib(raw_name="icon", deserializer=str)

    #: The member's that belong to this team.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`snowflakes.Snowflake`, :obj:`TeamMember` ]
    members: typing.Mapping[snowflakes.Snowflake, TeamMember] = marshaller.attrib(
        deserializer=lambda members: {m.user.id: m for m in map(TeamMember.deserialize, members)}
    )

    #: The snowflake ID of this team's owner.
    #:
    #: :type: :obj:`snowflakes.Snowflake`
    owner_user_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake)

    @property
    def icon_url(self) -> typing.Optional[str]:
        """The url of this team's icon, if set."""
        return self.format_icon_url()

    def format_icon_url(self, fmt: str = "png", size: int = 2048) -> typing.Optional[str]:
        """Generate the icon url for this team if set.

        Parameters
        ----------
        fmt : :obj:`str`
            The format to use for this url, defaults to ``png``.
            Supports ``png``, ``jpeg``, ``jpg`` and ``webp``.
        size : :obj:`int`
            The size to set for the url, defaults to ``2048``. Can be any power
            of two between 16 and 2048 inclusive.

        Returns
        -------
        :obj:`str`, optional
            The string url.
        """
        if self.icon_hash:
            return cdn.generate_cdn_url("team-icons", str(self.id), self.icon_hash, fmt=fmt, size=size)
        return None


@marshaller.attrs(slots=True)
class Owner(users.User):
    """Represents the user who owns an application, may be a team user."""

    #: This user's flags.
    #:
    #: :type: :obj:`int`
    flags: int = marshaller.attrib(deserializer=int)

    @property
    def is_team_user(self) -> bool:
        """If this user is a Team user (the owner of an application that's owned by a team)."""
        return bool((self.flags >> 10) & 1)


@marshaller.attrs(slots=True)
class Application(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents the information of an Oauth2 Application."""

    #: The name of this application.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str)

    #: The description of this application, will be an empty string if unset.
    #:
    #: :type: :obj:`str`
    description: str = marshaller.attrib(deserializer=str)

    #: Whether the bot associated with this application is public.
    #: Will be ``None`` if this application doesn't have an associated bot.
    #:
    #: :type: :obj:`bool`, optional
    is_bot_public: typing.Optional[bool] = marshaller.attrib(
        raw_name="bot_public", deserializer=bool, if_undefined=None
    )

    #: Whether the bot associated with this application is requiring code grant
    #: for invites. Will be ``None`` if this application doesn't have a bot.
    #:
    #: :type: :obj:`bool`, optional
    is_bot_code_grant_required: typing.Optional[bool] = marshaller.attrib(
        raw_name="bot_require_code_grant", deserializer=bool, if_undefined=None
    )

    #: The object of this application's owner.
    #: This should always be ``None`` in application objects retrieved outside
    #: Discord's oauth2 flow.
    #:
    #: :type: :obj:`Owner`, optional
    owner: typing.Optional[Owner] = marshaller.attrib(deserializer=Owner.deserialize, if_undefined=None)

    #: A collection of this application's rpc origin urls, if rpc is enabled.
    #:
    #: :type: :obj:`typing.Set` [ :obj:`str` ], optional
    rpc_origins: typing.Optional[typing.Set[str]] = marshaller.attrib(deserializer=set, if_undefined=None)

    #: This summary for this application's primary SKU if it's sold on Discord.
    #: Will be an empty string if unset.
    #:
    #: :type: :obj:`str`
    summary: str = marshaller.attrib(deserializer=str)

    #: The base64 encoded key used for the GameSDK's ``GetTicket``.
    #:
    #: :type: :obj:`str`
    verify_key: bytes = marshaller.attrib(deserializer=lambda key: bytes(key, "utf-8"))

    #: The hash of this application's icon if set.
    #:
    #: :type: :obj:`str`, optional
    icon_hash: typing.Optional[str] = marshaller.attrib(raw_name="icon", deserializer=str, if_undefined=None)

    #: This application's team if it belongs to one.
    #:
    #: :type: :obj:`Team`, optional
    team: typing.Optional[Team] = marshaller.attrib(deserializer=Team.deserialize, if_undefined=None, if_none=None)

    #: The ID of the guild this application is linked to
    #: if it's sold on Discord.
    #:
    #: :type: :obj:`snowflakes.Snowflake`, optional
    guild_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake, if_undefined=None
    )

    #: The ID of the primary "Game SKU" of a game that's sold on Discord.
    #:
    #: :type: :obj:`snowflakes.Snowflake`, optional
    primary_sku_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake, if_undefined=None
    )

    #: The url slug that links to this application's store page
    #: if it's sold on Discord.
    #:
    #: :type: :obj:`str`, optional
    slug: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None)

    #: The hash of this application's cover image on it's store, if set.
    #:
    #: :type: :obj:`str`, optional
    cover_image_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="cover_image", deserializer=str, if_undefined=None
    )

    @property
    def icon_url(self) -> typing.Optional[str]:
        """The url for this team's icon, if set."""
        return self.format_icon_url()

    def format_icon_url(self, fmt: str = "png", size: int = 2048) -> typing.Optional[str]:
        """Generate the icon url for this application if set.

        Parameters
        ----------
        fmt : :obj:`str`
            The format to use for this url, defaults to ``png``.
            Supports ``png``, ``jpeg``, ``jpg`` and ```webp``.
        size : :obj:`int`
            The size to set for the url, defaults to ``2048``.
            Can be any power of two between 16 and 2048.

        Returns
        -------
        :obj:`str`, optional
            The string url.
        """
        if self.icon_hash:
            return cdn.generate_cdn_url("app-icons", str(self.id), self.icon_hash, fmt=fmt, size=size)
        return None

    @property
    def cover_image_url(self) -> typing.Optional[str]:
        """The url for this icon's store cover image, if set."""
        return self.format_cover_image_url()

    def format_cover_image_url(self, fmt: str = "png", size: int = 2048) -> typing.Optional[str]:
        """Generate the url for this application's store page's cover image is
        set and applicable.

        Parameters
        ----------
        fmt : :obj:`str`
            The format to use for this url, defaults to ``png``.
            Supports ``png``, ``jpeg``, ``jpg`` and ``webp``.
        size : :obj:`int`
            The size to set for the url, defaults to ``2048``.
            Can be any power of two between 16 and 2048.

        Returns
        -------
        :obj:`str`, optional
            The string url.
        """
        if self.cover_image_hash:
            return cdn.generate_cdn_url("app-assets", str(self.id), self.cover_image_hash, fmt=fmt, size=size)
        return None
