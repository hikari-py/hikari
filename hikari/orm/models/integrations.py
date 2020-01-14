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
Account integrations.
"""
from __future__ import annotations

import datetime
import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import dates
from hikari.internal_utilities import reprs
from hikari.orm import fabric
from hikari.orm.models import bases
from hikari.orm.models import users


class IntegrationAccount(bases.BaseModel, bases.SnowflakeMixin):
    """
    An account used for an integration.
    """

    __slots__ = ("id", "name")

    #: The id for the account
    #:
    #: :type: :class:`int`
    id: int

    #: The name of the account
    #:
    #: :type: :class:`str`
    name: str

    __repr__ = reprs.repr_of("id", "name")

    def __init__(self, payload: containers.JSONObject) -> None:
        self.id = int(payload["id"])
        self.name = payload.get("name")


class PartialIntegration(bases.BaseModel, bases.SnowflakeMixin):
    """
    A partial guild integration, seen in AuditLogs.
    """

    __slots__ = ("id", "name", "type", "account")

    #: The integration ID
    #:
    #: :type: :class:`int`
    id: int

    #: The name of the integration
    #:
    #: :type: :class:`str`
    name: str

    #: The type of integration (e.g. twitch, youtube, etc)
    #:
    #: :type: :class:`str`
    type: str

    #: Integration account information.
    #:
    #: :type: :class:`hikari.orm.models.integrations.IntegrationAccount`
    account: IntegrationAccount

    __repr__ = reprs.repr_of("id", "name")

    def __init__(self, payload: containers.JSONObject) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]
        self.type = payload["type"]
        self.account = IntegrationAccount(payload["account"])


class Integration(PartialIntegration, bases.BaseModelWithFabric):
    """
    A guild integration.
    """

    __slots__ = (
        "_fabric",
        "is_enabled",
        "is_syncing",
        "role_id",
        "expire_grace_period",
        "user",
        "account",
        "synced_at",
    )

    role_id: int

    #: Whether the integration is enabled or not.
    #:
    #: :type: :class:`bool`
    is_enabled: bool

    #: Whether the integration is currently synchronizing.
    #:
    #: :type: :class:`bool`
    is_syncing: bool

    #: The grace period for expiring subscribers.
    #:
    #: :type: :class:`int`
    expire_grace_period: int

    #: The user for this integration
    #:
    #: :type: :class:`hikari.orm.models.users.User`
    user: users.User

    #: The time when the integration last synchronized.
    #:
    #: :type: :class:`datetime.datetime`
    synced_at: datetime.datetime

    __repr__ = reprs.repr_of("id", "name", "is_enabled")

    def __init__(self, fabric_obj: fabric.Fabric, payload: containers.JSONObject) -> None:
        super().__init__(payload)
        self._fabric = fabric_obj
        self.is_enabled = payload["enabled"]
        self.is_syncing = payload["syncing"]
        self.role_id = int(payload["role_id"])
        self.expire_grace_period = int(payload["expire_grace_period"])
        self.user = self._fabric.state_registry.parse_user(payload["user"])
        self.synced_at = dates.parse_iso_8601_ts(payload["synced_at"])


#: Any type of :class:`PartialIntegration` (including :class:`Integration`),
#: or the :class:`int`/:class:`str` ID of one.
PartialIntegrationLikeT = typing.Union[bases.RawSnowflakeT, PartialIntegration]


#: An instance of :class:`Integration`, or the :class:`int`/:class:`str` ID of one.
IntegrationLikeT = typing.Union[bases.RawSnowflakeT, Integration]

__all__ = ["Integration", "IntegrationAccount", "PartialIntegration", "PartialIntegrationLikeT", "IntegrationLikeT"]
