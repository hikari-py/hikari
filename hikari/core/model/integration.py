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
__all__ = ("Integration", "IntegrationAccount")

import typing
import datetime

from hikari.core.model import base
from hikari.core.model import user
from hikari.core.model import model_cache
from hikari.core.utils import transform
from hikari.core.utils import dateutils


@base.dataclass()
class IntegrationAccount:
    __slots__ = ("_state", "id", "name")

    _state: typing.Any
    # The id for the account
    id: int
    # The name of the account
    name: str

    @staticmethod
    def from_dict(global_state: model_cache.AbstractModelCache, payload):
        return IntegrationAccount(
            _state=global_state, id=transform.get_cast(payload, "id", int), name=payload.get("name")
        )


@base.dataclass()
class Integration:
    __slots__ = (
        "_state",
        "id",
        "name",
        "type",
        "enabled",
        "syncing",
        "_role_id",
        "expire_behavior",
        "expire_grace_period",
        "user",
        "account",
        "synced_at",
    )

    _state: typing.Any
    # The integration id
    id: int
    # The name of the integration
    name: str
    # The typw of integration, be it twitch, youtube, etc
    type: str
    # Whether the integration is enabled
    enabled: bool
    # Whether the integration is syncing
    syncing: bool
    # Id for the role used for the integration's "subscribers"
    _role_id: int
    # The behaviour of expiring subscribers
    # I assume this to be an enum however docs do not mention anything so god knows
    expire_behavior: int
    #  The grace period for expiring subscribers
    expire_grace_period: int
    # The user for this integration
    user: "user.User"
    # Integration account information
    account: IntegrationAccount
    # When the integration was last synced
    synced_at: datetime.datetime

    @staticmethod
    def from_dict(global_state: model_cache.AbstractModelCache, payload):
        return Integration(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            name=payload.get("name"),
            type=payload.get("type"),
            enabled=transform.get_cast(payload, "enabled", bool),
            syncing=transform.get_cast(payload, "syncing", bool),
            _role_id=transform.get_cast(payload, "role_id", int),
            expire_behavior=transform.get_cast(payload, "expire_behavior", int),
            expire_grace_period=transform.get_cast(payload, "expire_grace_period", int),
            user=global_state.parse_user(payload.get("user")),
            account=IntegrationAccount.from_dict(
                global_state, payload.get("account")
            ),  #  Change this later, slightly hacky way to do it
            synced_at=transform.get_cast(payload, "synced_at", dateutils.parse_iso_8601_datetime),
        )
