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
"""Bitfield of permissions."""

from __future__ import annotations

__all__ = ["Permission"]

import enum


@enum.unique
class Permission(enum.IntFlag):
    """Represents the permissions available in a given channel or guild.

    This is an int-flag enum. This means that you can **combine multiple
    permissions together** into one value using the bitwise-OR operator (`|`).

        my_perms = Permission.MANAGE_CHANNELS | Permission.MANAGE_GUILD

        your_perms = (
            Permission.CREATE_INSTANT_INVITE
            | Permission.KICK_MEMBERS
            | Permission.BAN_MEMBERS
            | Permission.MANAGE_GUILD
        )

    You can **check if a permission is present** in a set of combined
    permissions by using the bitwise-AND operator (`&`). This will return
    the int-value of the permission if it is present, or `0` if not present.

        my_perms = Permission.MANAGE_CHANNELS | Permission.MANAGE_GUILD

        if my_perms & Permission.MANAGE_CHANNELS:
            if my_perms & Permission.MANAGE_GUILD:
                print("I have the permission to both manage the guild and the channels in it!")
            else:
                print("I have the permission to manage channels!")
        else:
            print("I don't have the permission to manage channels!")

        # Or you could simplify it:

        if my_perms & (Permission.MANAGE_CHANNELS | Permission.MANAGE_GUILD):
            print("I have the permission to both manage the guild and the channels in it!")
        elif my_perms & Permission.MANAGE_CHANNELS:
            print("I have the permission to manage channels!")
        else:
            print("I don't have the permission to manage channels!")

    If you need to **check that a permission is not present**, you can use the
    bitwise-XOR operator (`^`) to check. If the permission is not present, it
    will return a non-zero value, otherwise if it is present, it will return `0`.

        my_perms = Permission.MANAGE_CHANNELS | Permission.MANAGE_GUILD

        if my_perms ^ Permission.MANAGE_CHANNELS:
            print("Please give me the MANAGE_CHANNELS permission!")

    Lastly, if you need all the permissions set except the permission you want,
    you can use the inversion operator (`~`) to do that.

        # All permissions except ADMINISTRATOR.
        my_perms = ~Permission.ADMINISTRATOR

    """

    NONE = 0
    """Empty permission."""

    CREATE_INSTANT_INVITE = 1 << 0
    """Allows creation of instant invites."""

    KICK_MEMBERS = 1 << 1
    """Allows kicking members"""

    BAN_MEMBERS = 1 << 2
    """Allows banning members."""

    ADMINISTRATOR = 1 << 3
    """Allows all permissions and bypasses channel permission overwrites."""

    MANAGE_CHANNELS = 1 << 4
    """Allows management and editing of channels."""

    MANAGE_GUILD = 1 << 5
    """Allows management and editing of the guild."""

    ADD_REACTIONS = 1 << 6
    """Allows for the addition of reactions to messages."""

    VIEW_AUDIT_LOG = 1 << 7
    """Allows for viewing of audit logs."""

    PRIORITY_SPEAKER = 1 << 8
    """Allows for using priority speaker in a voice channel."""

    STREAM = 1 << 9
    """Allows the user to go live."""

    VIEW_CHANNEL = 1 << 10
    """Allows guild members to view a channel, which includes reading messages in text channels."""

    SEND_MESSAGES = 1 << 11
    """Allows for sending messages in a channel."""

    SEND_TTS_MESSAGES = 1 << 12
    """Allows for sending of `/tts` messages."""

    MANAGE_MESSAGES = 1 << 13
    """Allows for deletion of other users messages."""

    EMBED_LINKS = 1 << 14
    """Links sent by users with this permission will be auto-embedded."""

    ATTACH_FILES = 1 << 15
    """Allows for uploading images and files."""

    READ_MESSAGE_HISTORY = 1 << 16
    """Allows for reading of message history."""

    MENTION_ROLES = 1 << 17
    """Allows for using the `@everyone` tag to notify all users in a channel,
    and the `@here` tag to notify all online users in a channel, and the
    `@role` tag (even if the role is not mentionable) to notify all users with
    that role in a channel.
    """

    USE_EXTERNAL_EMOJIS = 1 << 18
    """Allows the usage of custom emojis from other servers."""

    CONNECT = 1 << 20
    """Allows for joining of a voice channel."""

    SPEAK = 1 << 21
    """Allows for speaking in a voice channel."""

    MUTE_MEMBERS = 1 << 22
    """Allows for muting members in a voice channel."""

    DEAFEN_MEMBERS = 1 << 23
    """Allows for deafening of members in a voice channel."""

    MOVE_MEMBERS = 1 << 24
    """Allows for moving of members between voice channels."""

    USE_VAD = 1 << 25
    """Allows for using voice-activity-detection in a voice channel."""

    CHANGE_NICKNAME = 1 << 26
    """Allows for modification of own nickname."""

    MANAGE_NICKNAMES = 1 << 27
    """Allows for modification of other users nicknames."""

    MANAGE_ROLES = 1 << 28
    """Allows management and editing of roles."""

    MANAGE_WEBHOOKS = 1 << 29
    """Allows management and editing of webhooks."""

    MANAGE_EMOJIS = 1 << 30
    """Allows management and editing of emojis."""
