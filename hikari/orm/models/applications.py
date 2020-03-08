#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Application models.
"""
from __future__ import annotations

__all__ = ["Application"]

import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import reprs
from hikari.internal_utilities import transformations
from hikari.internal_utilities import type_hints
from hikari.orm.models import bases
from hikari.orm.models import teams

if typing.TYPE_CHECKING:
    from hikari.orm import fabric
    from hikari.orm.models import users


class Application(bases.BaseModel, bases.SnowflakeMixin):
    """
    An Oauth2 application's information.
    """

    __slots__ = (
        "id",
        "name",
        "icon_hash",
        "description",
        "rpc_origins",
        "is_bot_public",
        "is_bot_code_grant_required",
        "owner",
        "summary",
        "verify_key",
        "team",
        "guild_id",
        "primary_sku_id",
        "slug_url",
        "cover_image_hash",
    )

    #: The application's snowflake ID.
    #:
    #: :type: :class:`int`
    id: int

    #: The application's name.
    #:
    #: :type: :class:`str`
    name: str

    #: The hash of the application's icon.
    #:
    #: :type: :class:`str` or `None`
    icon_hash: type_hints.Nullable[str]

    #: The application's description
    #:
    #: :type: :class:`str`
    description: str

    #: An array of the rpc origin urls for the application if rpc is enabled.
    #:
    #: :type: :class:`typing.Sequence` of :class:`str`
    rpc_origins: typing.Sequence[str]

    #: Whether this application's bot is set to public.
    #:
    #: :type: :class:`bool`
    is_bot_public: bool

    #: Whether this application's bot requires completion of the full oauth2 grant flow for guild invites.
    #:
    #: :type: :class:`bool`
    is_bot_code_grant_required: bool

    #: The application's owner.
    #:
    #: :type: :class:`hikari.orm.models.users.IUser`
    owner: users.BaseUser

    #: The summary field for this application's primary SKU's store page if this is a game sold on Discord.
    #:
    #: :type: :class:`str` or `None`
    summary: type_hints.Nullable[str]

    #: The base64 encoded key used for "GetTicket" in the GameSDK.
    #:
    #: :type: :class:`str`
    verify_key: str

    #: The team that the application belongs to if applicable.
    #:
    #: :type: :class:`hikari.orm.models.teams.Team` or `None`
    team: type_hints.Nullable[teams.Team]

    #: The ID of the guild the application is linked to if it's a game sold on Discord.
    #:
    #: :type: :class:`int` or `None`
    guild_id: type_hints.Nullable[int]

    #: The ID of the application's linked Game SKU if it's a game sold on Discord.
    #:
    #: :type: :class:`int` or `None`
    primary_sku_id: type_hints.Nullable[int]

    #: The URL slug that links to the application's store page if it's a game sold on Discord.
    #:
    #: :type: :class:`str` or `None`
    slug_url: type_hints.Nullable[str]

    #: The hash of the application's store embed image if it is a game sold on Discord.
    #:
    #: :type: :class:`str` or `None`
    cover_image_hash: type_hints.Nullable[str]

    __repr__ = reprs.repr_of("id", "name", "description")

    def __init__(self, fabric_obj: fabric.Fabric, payload: type_hints.JSONObject) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]
        self.icon_hash = payload.get("icon")
        self.description = payload["description"]
        self.rpc_origins = [url for url in payload.get("rpc_origins", containers.EMPTY_SEQUENCE)]
        self.is_bot_public = payload["bot_public"]
        self.is_bot_code_grant_required = payload["bot_require_code_grant"]
        self.owner = fabric_obj.state_registry.parse_user(payload["owner"])
        self.summary = payload.get("summary")
        self.verify_key = payload["verify_key"]
        self.team = teams.Team(fabric_obj, payload["team"]) if payload.get("team") else None
        self.guild_id = transformations.nullable_cast(payload.get("guild_id"), int)
        self.primary_sku_id = transformations.nullable_cast(payload.get("primary_sku_id"), int)
        self.slug_url = payload.get("slug")
        self.cover_image_hash = payload.get("cover_image")
