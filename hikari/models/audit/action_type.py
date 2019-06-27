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
Audit log events that can be specified.
"""
__all__ = ("ActionType", "ActionTypeCategory")

import enum


from hikari.compat import typing


class ActionTypeCategory(enum.IntEnum):
    GUILD = 0
    CHANNEL = 1
    MEMBER = 2
    ROLE = 3
    INVITE = 4
    WEBHOOK = 5
    EMOJI = 6
    MESSAGE = 7

    @property
    def events(self) -> typing.Set["ActionTypeCategory"]:
        """Get all corresponding events for the given category."""
        return {event for event in ActionType if event.value // 10 == self}


class ActionType(enum.IntEnum):
    GUILD_UPDATE = 1
    CHANNEL_CREATE = 10
    CHANNEL_UPDATE = 11
    CHANNEL_DELETE = 12
    CHANNEL_OVERWRITE_CREATE = 13
    CHANNEL_OVERWRITE_UPDATE = 14
    CHANNEL_OVERWRITE_DELETE = 15
    MEMBER_KICK = 20
    MEMBER_PRUNE = 21
    MEMBER_BAN_ADD = 22
    MEMBER_UPDATE = 24
    MEMBER_ROLE_UPDATE = 25
    ROLE_CREATE = 30
    ROLE_UPDATE = 31
    ROLE_DELETE = 32
    INVITE_CREATE = 40
    INVITE_UPDATE = 41
    INVITE_DELETE = 42
    WEBHOOK_CREATE = 50
    WEBHOOK_UPDATE = 51
    WEBHOOK_DELETE = 52
    EMOJI_CREATE = 60
    EMOJI_UPDATE = 61
    EMOJI_DELETE = 62
    MESSAGE_DELETE = 72

    @property
    def category(self) -> ActionTypeCategory:
        """Get the category for the given event."""
        return ActionTypeCategory(self.value // 10)
