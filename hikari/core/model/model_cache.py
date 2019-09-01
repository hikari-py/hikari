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
Handles managing the state of the bot, and the cache.
"""
from __future__ import annotations

import abc

import typing

from hikari.core.model import channel
from hikari.core.model import emoji
from hikari.core.model import guild
from hikari.core.model import message
from hikari.core.model import role
from hikari.core.model import user
from hikari.core.model import webhook
from hikari.core.utils import types


class AbstractModelCache(abc.ABC):
    """
    Provides the relational interface between different types of objects and the overall cache.
    
    This class provides abstract definitions only to enable a user to implement their own cache system if they prefer.
    """

    __slots__ = ()

    @abc.abstractmethod
    def parse_user(self, user: types.DiscordObject) -> user.User:
        ...

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int) -> typing.Optional[user.User]:
        ...

    @abc.abstractmethod
    def parse_guild(self, guild: types.DiscordObject) -> guild.Guild:
        ...

    @abc.abstractmethod
    def get_guild_by_id(self, guild_id: int) -> typing.Optional[guild.Guild]:
        ...

    @abc.abstractmethod
    def parse_member(self, member: types.DiscordObject, guild_id: int) -> user.Member:
        ...

    @abc.abstractmethod
    def parse_role(self, role: types.DiscordObject) -> role.Role:
        ...

    @abc.abstractmethod
    def parse_emoji(self, guild_id: int, emoji: types.DiscordObject) -> emoji.Emoji:
        ...

    @abc.abstractmethod
    def parse_message(self, message: types.DiscordObject) -> message.Message:
        ...

    @abc.abstractmethod
    def get_message_by_id(self, message_id: int) -> typing.Optional[message.Message]:
        ...

    @abc.abstractmethod
    def parse_channel(self, channel: types.DiscordObject) -> channel.Channel:
        ...

    @abc.abstractmethod
    def get_dm_channel_by_id(self, channel_id: int) -> typing.Optional[channel.DMChannel]:
        ...

    @abc.abstractmethod
    def get_guild_channel_by_id(self, guild_channel_id: int) -> typing.Optional[channel.GuildChannel]:
        ...

    @abc.abstractmethod
    def parse_webhook(self, webhook: types.DiscordObject) -> webhook.Webhook:
        ...


__all__ = ["AbstractModelCache"]
