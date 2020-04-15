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
"""Components and entities that are used to describe both custom and Unicode emojis on Discord."""
import typing

import attr

from hikari import entities
from hikari import snowflakes
from hikari import users
from hikari.internal import marshaller

__all__ = ["Emoji", "UnicodeEmoji", "UnknownEmoji", "GuildEmoji"]


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Emoji(entities.HikariEntity, entities.Deserializable):
    """Base class for all emojis."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class UnicodeEmoji(Emoji):
    """Represents a unicode emoji."""

    #: The codepoints that form the emoji.
    #:
    #: :type: :obj:`str`
    name: str = marshaller.attrib(deserializer=str)

    @property
    def url_name(self) -> str:
        """Get the format of this emoji used in request routes."""
        return self.name

    @property
    def mention(self) -> str:
        """Get the format of this emoji used for sending it in a channel."""
        return self.name


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class UnknownEmoji(Emoji, snowflakes.UniqueEntity):
    """Represents a unknown emoji."""

    #: The name of the emoji.
    #:
    #: :type: :obj:`str`, optional
    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None)

    #: Whether the emoji is animated.
    #:
    #: :type: :obj:`bool`
    is_animated: bool = marshaller.attrib(
        raw_name="animated", deserializer=bool, if_undefined=False, if_none=None, default=False
    )

    @property
    def url_name(self) -> str:
        """Get the format of this emoji used in request routes."""
        return f"{self.name}:{self.id}"


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildEmoji(UnknownEmoji):
    """Represents a guild emoji."""

    #: The whitelisted role IDs to use this emoji.
    #:
    #: :type: :obj:`typing.Set` [ :obj:`hikari.snowflakes.Snowflake` ]
    role_ids: typing.Set[snowflakes.Snowflake] = marshaller.attrib(
        raw_name="roles",
        deserializer=lambda roles: {snowflakes.Snowflake.deserialize(r) for r in roles},
        if_undefined=dict,
        factory=dict,
    )

    #: The user that created the emoji.
    #:
    #: Note
    #: ----
    #: This will be :obj:`None` if you are missing the ``MANAGE_EMOJIS``
    #: permission in the server the emoji is from.
    #:
    #:
    #: :type: :obj:`hikari.users.User`, optional
    user: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_none=None, if_undefined=None, default=None
    )

    #: Whether this emoji must be wrapped in colons.
    #:
    #: :type: :obj:`bool`, optional
    is_colons_required: typing.Optional[bool] = marshaller.attrib(
        raw_name="require_colons", deserializer=bool, if_undefined=None, default=None
    )

    #: Whether the emoji is managed by an integration.
    #:
    #: :type: :obj:`bool`, optional
    is_managed: typing.Optional[bool] = marshaller.attrib(
        raw_name="managed", deserializer=bool, if_undefined=None, default=None
    )

    @property
    def mention(self) -> str:
        """Get the format of this emoji used for sending it in a channel."""
        return f"<{'a' if self.is_animated else ''}:{self.url_name}>"


def deserialize_reaction_emoji(payload: typing.Dict) -> typing.Union[UnicodeEmoji, UnknownEmoji]:
    """Deserialize a reaction emoji into an emoji."""
    if payload.get("id"):
        return UnknownEmoji.deserialize(payload)

    return UnicodeEmoji.deserialize(payload)
