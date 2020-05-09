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

from __future__ import annotations

__all__ = ["Emoji", "UnicodeEmoji", "UnknownEmoji", "GuildEmoji"]

import typing

import attr

from hikari import bases
from hikari import files
from hikari import users
from hikari.internal import marshaller

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Emoji(bases.Entity, marshaller.Deserializable):
    """Base class for all emojis."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class UnicodeEmoji(Emoji):
    """Represents a unicode emoji."""

    name: str = marshaller.attrib(deserializer=str, repr=True)
    """The codepoints that form the emoji."""

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
class UnknownEmoji(Emoji, bases.Unique, files.BaseStream):
    """Represents a unknown emoji."""

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, repr=True)
    """The name of the emoji."""

    is_animated: typing.Optional[bool] = marshaller.attrib(
        raw_name="animated", deserializer=bool, if_undefined=False, if_none=None, default=False
    )
    """Whether the emoji is animated.

    Will be `None` when received in Message Reaction Remove and Message
    Reaction Remove Emoji events.
    """

    @property
    def url_name(self) -> str:
        """Get the format of this emoji used in request routes."""
        return f"{self.name}:{self.id}"

    @property
    def url(self) -> str:
        # TODO: implement.
        raise NotImplementedError()

    def __aiter__(self) -> typing.AsyncIterator[bytes]:
        # TODO: implement.
        raise NotImplementedError()


def _deserialize_role_ids(payload: more_typing.JSONArray) -> typing.Set[bases.Snowflake]:
    return {bases.Snowflake(role_id) for role_id in payload}


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildEmoji(UnknownEmoji):
    """Represents a guild emoji."""

    role_ids: typing.Set[bases.Snowflake] = marshaller.attrib(
        raw_name="roles", deserializer=_deserialize_role_ids, if_undefined=set, factory=set,
    )
    """The IDs of the roles that are whitelisted to use this emoji.

    If this is empty then any user can use this emoji regardless of their roles.
    """

    user: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_none=None, if_undefined=None, default=None, inherit_kwargs=True
    )
    """The user that created the emoji.

    !!! note
        This will be `None` if you are missing the `MANAGE_EMOJIS`
        permission in the server the emoji is from.
    """

    is_colons_required: bool = marshaller.attrib(raw_name="require_colons", deserializer=bool)
    """Whether this emoji must be wrapped in colons."""

    is_managed: bool = marshaller.attrib(raw_name="managed", deserializer=bool)
    """Whether the emoji is managed by an integration."""

    is_available: bool = marshaller.attrib(raw_name="available", deserializer=bool)
    """Whether this emoji can currently be used.

    May be `False` due to a loss of Sever Boosts on the emoji's guild.
    """

    @property
    def mention(self) -> str:
        """Get the format of this emoji used for sending it in a channel."""
        return f"<{'a' if self.is_animated else ''}:{self.url_name}>"


def deserialize_reaction_emoji(payload: typing.Dict, **kwargs: typing.Any) -> typing.Union[UnicodeEmoji, UnknownEmoji]:
    """Deserialize a reaction emoji into an emoji."""
    if payload.get("id"):
        return UnknownEmoji.deserialize(payload, **kwargs)

    return UnicodeEmoji.deserialize(payload, **kwargs)
