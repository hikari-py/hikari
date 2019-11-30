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
User Connection models returned by oauth and user related HTTP endpoints.
"""
from __future__ import annotations

import enum
import typing

from hikari.internal_utilities import data_structures
from hikari.internal_utilities import auto_repr
from hikari.orm import fabric
from hikari.orm.models import interfaces
from hikari.orm.models import integrations


class ConnectionVisibility(enum.IntEnum):
    """The visibility options for a user connection."""

    NONE = 0
    EVERYONE = 1


class Connection(interfaces.IStatefulModel, interfaces.ISnowflake):
    """
    Implementation of the Connection object, found in the oauth2 flow.
    """

    __slots__ = (
        "_fabric",
        "id",
        "name",
        "type",
        "is_revoked",
        "integrations",
        "is_verified",
        "is_friend_synced",
        "is_showing_activity",
        "visibility",
    )

    #: The id of the account.
    #:
    #: :type: :class:`str`
    id: str

    #: The username of the account.
    #:
    #: :type: :class:`str`
    name: str

    #: The service of the connection.
    #:
    #: :type: :class:`str`
    type: str

    #: The state of the connection.
    #:
    #: :type: :class:`bool`
    is_revoked: bool

    #: The server integrations related to this connection.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.orm.models.integrations.PartialIntegration`
    integrations: typing.Sequence[integrations.PartialIntegration]

    #: The verification status of this connection.
    #:
    #: :type: :class:`bool`
    is_verified: bool

    #: The status of friend sync for this connection
    #:
    #: :type: :class:`bool`
    is_friend_synced: bool

    #: Whether activities related to this connection are shared in presence update events.
    #:
    #: :type: :class:`bool`
    is_showing_activity: bool

    #: The visibility of this connection.
    #:
    #: :type: :class:`hikari.orm.models.connections.ConnectionVisibility`
    visibility: ConnectionVisibility

    __repr__ = auto_repr.repr_of("type", "id", "name")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self._fabric = fabric_obj
        self.id = payload["id"]
        self.name = payload["name"]
        self.type = payload["type"]
        self.is_revoked = payload.get("revoked", False)
        self.integrations = [
            integrations.PartialIntegration(i) for i in payload.get("integrations", data_structures.EMPTY_SEQUENCE)
        ]
        self.is_verified = payload["verified"]
        self.is_friend_synced = payload["friend_sync"]
        self.is_showing_activity = payload["show_activity"]
        self.visibility = ConnectionVisibility(payload["visibility"])


__all__ = ["Connection", "ConnectionVisibility"]
