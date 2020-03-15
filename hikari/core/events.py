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

__all__ = [
    "HikariEvent",
    "ConnectedEvent",
    "DisconnectedEvent",
    "ReconnectedEvent",
    "StartedEvent",
    "StoppingEvent",
    "StoppedEvent",
    "ReadyEvent",
    "ResumedEvent",
    "ChannelCreateEvent",
    "ChannelUpdateEvent",
    "ChannelDeleteEvent",
    "ChannelPinAddEvent",
    "ChannelPinRemoveEvent",
    "GuildCreateEvent",
    "GuildUpdateEvent",
    "GuildDeleteEvent",
    "GuildBanAddEvent",
    "GuildBanRemoveEvent",
    "GuildEmojisUpdateEvent",
    "GuildIntegrationsUpdateEvent",
    "GuildMemberAddEvent",
    "GuildMemberUpdateEvent",
    "GuildMemberRemoveEvent",
    "GuildRoleCreateEvent",
    "GuildRoleUpdateEvent",
    "GuildRoleDeleteEvent",
    "InviteCreateEvent",
    "InviteDeleteEvent",
    "MessageCreateEvent",
    "MessageUpdateEvent",
    "MessageDeleteEvent",
    "MessageDeleteBulkEvent",
    "MessageReactionAddEvent",
    "MessageReactionRemoveEvent",
    "MessageReactionRemoveAllEvent",
    "MessageReactionRemoveEmojiEvent",
    "PresenceUpdateEvent",
    "TypingStartEvent",
    "UserUpdateEvent",
    "VoiceStateUpdateEvent",
    "VoiceServerUpdateEvent",
    "WebhookUpdate",
]

import typing

import attr

from hikari.core import entities
from hikari.core import guilds as guilds_
from hikari.core import users

T_contra = typing.TypeVar("T_contra", contravariant=True)


@attr.s(slots=True, auto_attribs=True)
class HikariEvent(entities.HikariEntity):
    ...


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class ConnectedEvent(HikariEvent):
    ...


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class DisconnectedEvent(HikariEvent):
    ...


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class ReconnectedEvent(HikariEvent):
    ...


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StartedEvent(HikariEvent):
    ...


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StoppingEvent(HikariEvent):
    ...


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StoppedEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class ReadyEvent(HikariEvent):
    v: int
    user: users.User
    guilds: guilds_.Guild
    session_id: str
    shard_id: int
    shard_count: int


@attr.s(slots=True, auto_attribs=True)
class ResumedEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelCreateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelDeleteEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelPinAddEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelPinRemoveEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildCreateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildDeleteEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildBanAddEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildBanRemoveEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildEmojisUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildIntegrationsUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildMemberAddEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildMemberRemoveEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildMemberUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildRoleCreateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildRoleUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildRoleDeleteEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class InviteCreateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class InviteDeleteEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageCreateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageDeleteEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageDeleteBulkEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionAddEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionRemoveEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionRemoveAllEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionRemoveEmojiEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class PresenceUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class TypingStartEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class UserUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class VoiceStateUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class VoiceServerUpdateEvent(HikariEvent):
    ...


@attr.s(slots=True, auto_attribs=True)
class WebhookUpdate(HikariEvent):
    ...
