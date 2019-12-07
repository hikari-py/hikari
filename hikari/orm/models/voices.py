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
"""
Voice models.
"""
from __future__ import annotations

import typing

from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.orm import fabric
from hikari.orm.models import guilds
from hikari.orm.models import interfaces
from hikari.orm.models import members


class VoiceServer(interfaces.IStatefulModel):
    """
    The voice server information used for establishing a voice connection.
    """

    __slots__ = ("_fabric", "token", "guild_id", "endpoint")

    #: The token used for accessing the voice websocket endpoint.
    #:
    #: :type: :class:`str`
    token: str

    #: The id of the guild this server is hosting.
    #:
    #: :type: :class:`int`
    guild_id: int

    #: The endpoint of the voice server host
    #:
    #: :type: :class:`str`
    endpoint: str

    __repr__ = auto_repr.repr_of("guild_id", "endpoint")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self._fabric = fabric_obj
        self.token = payload["token"]
        self.guild_id = int(payload["guild_id"])
        self.update_state(payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        self.endpoint = payload["endpoint"]


class VoiceState(interfaces.IStatefulModel):
    """
    A user's voice connection status.
    """

    __slots__ = (
        "_fabric",
        "guild_id",
        "channel_id",
        "user_id",
        "member",
        "session_id",
        "is_deaf",
        "is_mute",
        "is_self_deaf",
        "is_self_mute",
        "is_self_stream",
        "is_suppressed",
    )

    #: The ID of the guild this state is for.
    #:
    #: :type: :class:`int` or `None`
    guild_id: typing.Optional[int]

    #: The ID of the channel this state is for.
    #:
    #: :type: :class:`int`
    channel_id: int

    #: The ID of the user this state is for.
    #:
    #: :type: :class:`int`
    user_id: int

    #: The guild member this voice state is for.
    #:
    #: :type: :class:`hikari.orm.models.members.Member` or `None`
    member: typing.Optional[members.Member]

    #: This voice session's ID.
    #:
    #: :type: :class:`str`
    session_id: str

    #: Whether this user has been deafened in this guild.
    #:
    #: :type: :class:`bool`
    is_deaf: bool

    #: Whether this user has been muted in this guild.
    #:
    #: :type: :class:`bool`
    is_mute: bool

    #: Whether this user is locally deafened.
    #:
    #: :type: :class:`bool`
    is_self_deaf: bool

    #: Whether this user is locally muted.
    #:
    #: :type: :class:`bool`
    is_self_mute: bool

    #: Whether this user has an active Go Live stream.
    #:
    #: :type: :class:`bool`
    is_self_stream: bool

    #: Whether this user is muted by the current user.
    #:
    #: :type: :class:`bool`
    is_suppressed: bool

    __repr__ = auto_repr.repr_of("user_id", "channel_id", "guild_id", "session_id")

    def __init__(
        self, fabric_obj: fabric.Fabric, guild_obj: guilds.Guild, payload: data_structures.DiscordObjectT
    ) -> None:
        self._fabric = fabric_obj
        self.user_id = int(payload["user_id"])
        self.guild_id = guild_obj.id
        self.session_id = payload["session_id"]

        member_obj = payload.get("member")
        if member_obj:
            self.member = self._fabric.state_registry.parse_member(member_obj, guild_obj)
        else:
            self.member = None

        self.update_state(payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        self.channel_id = int(payload["channel_id"])
        self.is_deaf = payload.get("deaf", False)
        self.is_mute = payload.get("mute", False)
        self.is_self_deaf = payload.get("self_deaf", False)
        self.is_self_mute = payload.get("self_mute", False)
        self.is_self_stream = payload.get("self_stream", False)
        self.is_suppressed = payload.get("suppress", False)


class VoiceRegion(interfaces.IModel):
    """
    Voice region model.
    """

    __slots__ = ("id", "name", "is_vip", "is_optimal", "is_deprecated", "is_custom")

    #: The region's ID.
    #:
    #: :type: :class:`str`
    id: str

    #: This region's name.
    #:
    #: :type: :class:`str`
    name: str

    #: Whether this region is vip-exclusive.
    #:
    #: :type: :class:`bool`
    is_vip: bool

    #: Whether this region is the closest to the client.
    #:
    #: :type: :class:`bool`
    is_optimal: bool

    #: Whether this voice region is deprecated.
    #:
    #: :type: :class:`bool`
    is_deprecated: bool

    #: Whether this voice region is custom (e.g. for an event).
    #:
    #: :type: :class:`bool`
    is_custom: bool

    __repr__ = auto_repr.repr_of("name", "is_vip", "is_deprecated")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.id = payload["id"]
        self.name = payload["name"]
        self.is_vip = payload["vip"]
        self.is_optimal = payload["optimal"]
        self.is_deprecated = payload["deprecated"]
        self.is_custom = payload["custom"]


__all__ = ["VoiceServer", "VoiceState", "VoiceRegion"]
