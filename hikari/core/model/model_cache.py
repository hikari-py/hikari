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
__all__ = ("AbstractModelCache",)

import abc

from hikari.core.utils import types


class AbstractModelCache(abc.ABC):
    """
    Provides the relational interface between different types of objects and the overall cache.
    
    This class provides abstract definitions only to enable a user to implement their own cache system if they prefer.
    """

    __slots__ = ()

    @abc.abstractmethod
    def parse_user(self, user: types.DiscordObject):
        ...

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int):
        ...

    @abc.abstractmethod
    def parse_guild(self, guild: types.DiscordObject):
        ...

    @abc.abstractmethod
    def get_guild_by_id(self, guild_id: int):
        ...

    @abc.abstractmethod
    def parse_member(self, member: types.DiscordObject, guild_id: int):
        ...

    @abc.abstractmethod
    def parse_role(self, role: types.DiscordObject):
        ...

    @abc.abstractmethod
    def parse_emoji(self, guild_id: int, emoji: types.DiscordObject):
        ...

    @abc.abstractmethod
    def parse_message(self, message: types.DiscordObject):
        ...

    @abc.abstractmethod
    def get_message_by_id(self, message_id: int):
        ...

    @abc.abstractmethod
    def parse_channel(self, channel: types.DiscordObject):
        ...

    @abc.abstractmethod
    def get_dm_channel_by_id(self, channel_id: int):
        ...

    @abc.abstractmethod
    def get_guild_channel_by_id(self, guild_channel_id: int):
        ...

    @abc.abstractmethod
    def parse_webhook(self, webhook: types.DiscordObject):
        ...
