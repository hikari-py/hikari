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
Guild permissions.
"""
from __future__ import annotations

__all__ = ("Permission",)

import enum


class Permission(enum.IntFlag):
    NONE = 0x0
    CREATE_INSTANT_INVITE = 0x1
    KICK_MEMBERS = 0x2
    BAN_MEMBERS = 0x4
    ADMINISTRATOR = 0x8
    MANAGE_CHANNELS = 0x10
    MANAGE_GUILD = 0x20
    ADD_REACTIONS = 0x40
    VIEW_AUDIT_LOG = 0x80
    PRIORITY_SPEAKER = 0x100
    VIEW_CHANNEL = 0x400
    SEND_MESSAGES = 0x800
    SEND_TTS_MESSAGES = 0x1000
    MANAGE_MESSAGES = 0x2000
    EMBED_LINKS = 0x4000
    ATTACH_FILES = 0x8000
    READ_MESSAGE_HISTORY = 0x10000
    MENTION_EVERYONE = 0x20000
    USE_EXTERNAL_EMOJIS = 0x40000
    CONNECT = 0x100000
    SPEAK = 0x200000
    MUTE_MEMBERS = 0x400000
    DEAFEN_MEMBERS = 0x800000
    MOVE_MEMBERS = 0x1000000
    USE_VAD = 0x2000000
    MANAGE_ROLES = 0x10000000
    MANAGE_WEBHOOKS = 0x20000000
    MANAGE_EMOJIS = 0x40000000
    ALL = 0x80000000 - 1
