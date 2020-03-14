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
class ReadyEvent(HikariEvent, entities.Deserializable):
    v: int
    user: users.User
    guilds: guilds_.Guild
    session_id: str
    shard_id: int
    shard_count: int


@attr.s(slots=True, auto_attribs=True)
class ResumedEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelCreateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelDeleteEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelPinAddEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class ChannelPinRemoveEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildCreateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildDeleteEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildBanAddEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildBanRemoveEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildEmojisUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildIntegrationsUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildMemberAddEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildMemberRemoveEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildMemberUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildRoleCreateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildRoleUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class GuildRoleDeleteEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class InviteCreateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class InviteDeleteEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageCreateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageDeleteEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageDeleteBulkEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionAddEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionRemoveEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionRemoveAllEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class MessageReactionRemoveEmojiEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class PresenceUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class TypingStartEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class UserUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class VoiceStateUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class VoiceServerUpdateEvent(HikariEvent, entities.Deserializable):
    ...


@attr.s(slots=True, auto_attribs=True)
class WebhookUpdate(HikariEvent, entities.Deserializable):
    ...
