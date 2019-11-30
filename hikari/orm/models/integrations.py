#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import date_helpers
from hikari.orm import fabric
from hikari.orm.models import interfaces
from hikari.orm.models import users


class IntegrationAccount(interfaces.ISnowflake):
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

    __repr__ = auto_repr.repr_of("id", "name")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.id = int(payload["id"])
        self.name = payload.get("name")


class PartialIntegration(interfaces.ISnowflake):
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

    __repr__ = auto_repr.repr_of("id", "name")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]
        self.type = payload["type"]
        self.account = IntegrationAccount(payload["account"])


class Integration(PartialIntegration, interfaces.IStatefulModel):
    """
    A guild integration.
    """

    __slots__ = (
        "_fabric",
        "is_enabled",
        "is_syncing",
        "_role_id",
        "expire_grace_period",
        "user",
        "account",
        "synced_at",
    )

    _role_id: int

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

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(payload)
        self._fabric = fabric_obj
        self.is_enabled = payload["enabled"]
        self.is_syncing = payload["syncing"]
        self._role_id = int(payload["role_id"])
        self.expire_grace_period = int(payload["expire_grace_period"])
        self.user = self._fabric.state_registry.parse_user(payload["user"])
        self.synced_at = date_helpers.parse_iso_8601_ts(payload["synced_at"])


__all__ = ["Integration", "IntegrationAccount", "PartialIntegration"]
