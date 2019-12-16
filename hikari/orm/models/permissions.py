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
Guild permissions.

Note:
    All the permissions defined in the :class:`Permissions` class are also
    exported into this module namespace. This means you can omit the `Permission`
    part when referring to permissions:

        >>> from hikari.orm.models import permissions
        >>> MODERATOR = permissions.MANAGE_GUILD | permissions.MANAGE_CHANNELS

"""
from __future__ import annotations

import enum
import typing


class Permission(enum.IntFlag):
    """
    Represents the permissions available in a given channel or guild.
    
    This is an int-flag enum. This means that you can **combine multiple 
    permissions together** into one value using the bitwise-OR "`|`" operator.
    
    .. code-block:: python
        
        my_perms = Permission.MANAGE_CHANNELS | Permission.MANAGE_GUILD
        
        your_perms = (
            Permission.CREATE_INSTANT_INVITE
            | Permission.KICK_MEMBERS
            | Permission.BAN_MEMBERS
            | Permission.MANAGE_GUILD
        )
    
    You can **check if a permission is present** in a set of combined 
    permissions by using the bitwise-AND "`&`" operator. This will return
    the int-value of the permission if it is present, or `0` if not present.
    
    .. code-block:: python
        
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
    bitwise-XOR "`^`" operator to check. If the permission is not present, it 
    will return a non-zero value, otherwise if it is present, it will return 0.
    
    .. code-block:: python
    
        my_perms = Permission.MANAGE_CHANNELS | Permission.MANAGE_GUILD
        
        if my_perms ^ Permission.MANAGE_CHANNELS:
            print("Please give me the MANAGE_CHANNELS permission!")
    
    Lastly, if you need all the permissions set except the permission you want,
    you can use the inversion operator "`~`" to do that.
    
    .. code-block:: python
        
        # All permissions except ADMINISTRATOR.
        my_perms = ~Permission.ADMINISTRATOR
    
    """

    #: Empty permission.
    NONE = 0x0
    #: Allows creation of instant invites.
    CREATE_INSTANT_INVITE = 0x1
    #: Allows kicking members
    KICK_MEMBERS = 0x2
    #: Allows banning members.
    BAN_MEMBERS = 0x4
    #: Allows all permissions and bypasses channel permission overwrites.
    ADMINISTRATOR = 0x8
    #: Allows management and editing of channels.
    MANAGE_CHANNELS = 0x10
    #: Allows management and editing of the guild.
    MANAGE_GUILD = 0x20
    #: Allows for the addition of reactions to messages.
    ADD_REACTIONS = 0x40
    #: Allows for viewing of audit logs.
    VIEW_AUDIT_LOG = 0x80
    #: Allows for using priority speaker in a voice channel.
    PRIORITY_SPEAKER = 0x1_00
    #: Allows the user to go live.
    STREAM = 0x2_00
    #: Allows guild members to view a channel, which includes reading messages in text channels.
    VIEW_CHANNEL = 0x4_00
    #: Allows for sending messages in a channel.
    SEND_MESSAGES = 0x8_00
    #: Allows for sending of `/tts` messages.
    SEND_TTS_MESSAGES = 0x10_00
    #: Allows for deletion of other users messages.
    MANAGE_MESSAGES = 0x20_00
    #: Links sent by users with this permission will be auto-embedded.
    EMBED_LINKS = 0x40_00
    #: Allows for uploading images and files
    ATTACH_FILES = 0x80_00
    #: Allows for reading of message history.
    READ_MESSAGE_HISTORY = 0x1_00_00
    #: Allows for using the `@everyone` tag to notify all users in a channel, and the
    #: `@here` tag to notify all online users in a channel.
    MENTION_EVERYONE = 0x2_00_00
    #: Allows the usage of custom emojis from other servers.
    USE_EXTERNAL_EMOJIS = 0x4_00_00
    #: Allows for joining of a voice channel.
    CONNECT = 0x10_00_00
    #: Allows for speaking in a voice channel.
    SPEAK = 0x20_00_00
    #: Allows for muting members in a voice channel.
    MUTE_MEMBERS = 0x40_00_00
    #: Allows for deafening of members in a voice channel.
    DEAFEN_MEMBERS = 0x80_00_00
    #: Allows for moving of members between voice channels.
    MOVE_MEMBERS = 0x1_00_00_00
    #: Allows for using voice-activity-detection in a voice channel.
    USE_VAD = 0x2_00_00_00
    #: Allows for modification of own nickname.
    CHANGE_NICKNAME = 0x4_00_00_00
    #: Allows for modification of other users nicknames.
    MANAGE_NICKNAMES = 0x8_00_00_00
    #: Allows management and editing of roles.
    MANAGE_ROLES = 0x10_00_00_00
    #: Allows management and editing of webhooks.
    MANAGE_WEBHOOKS = 0x20_00_00_00
    #: Allows management and editing of emojis.
    MANAGE_EMOJIS = 0x40_00_00_00


# Note, these are explicitly defined to aid type checkers that will not evaluate dynamically injected globals.
NONE = Permission.NONE
CREATE_INSTANT_INVITE = Permission.CREATE_INSTANT_INVITE
KICK_MEMBERS = Permission.KICK_MEMBERS
BAN_MEMBERS = Permission.BAN_MEMBERS
ADMINISTRATOR = Permission.ADMINISTRATOR
MANAGE_CHANNELS = Permission.MANAGE_CHANNELS
MANAGE_GUILD = Permission.MANAGE_GUILD
ADD_REACTIONS = Permission.ADD_REACTIONS
VIEW_AUDIT_LOG = Permission.VIEW_AUDIT_LOG
PRIORITY_SPEAKER = Permission.PRIORITY_SPEAKER
STREAM = Permission.STREAM
VIEW_CHANNEL = Permission.VIEW_CHANNEL
SEND_MESSAGES = Permission.SEND_MESSAGES
SEND_TTS_MESSAGES = Permission.SEND_TTS_MESSAGES
MANAGE_MESSAGES = Permission.MANAGE_MESSAGES
EMBED_LINKS = Permission.EMBED_LINKS
ATTACH_FILES = Permission.ATTACH_FILES
READ_MESSAGE_HISTORY = Permission.READ_MESSAGE_HISTORY
MENTION_EVERYONE = Permission.MENTION_EVERYONE
USE_EXTERNAL_EMOJIS = Permission.USE_EXTERNAL_EMOJIS
CONNECT = Permission.CONNECT
SPEAK = Permission.SPEAK
MUTE_MEMBERS = Permission.MUTE_MEMBERS
DEAFEN_MEMBERS = Permission.DEAFEN_MEMBERS
MOVE_MEMBERS = Permission.MOVE_MEMBERS
USE_VAD = Permission.USE_VAD
CHANGE_NICKNAME = Permission.CHANGE_NICKNAME
MANAGE_NICKNAMES = Permission.MANAGE_NICKNAMES
MANAGE_ROLES = Permission.MANAGE_ROLES
MANAGE_WEBHOOKS = Permission.MANAGE_WEBHOOKS
MANAGE_EMOJIS = Permission.MANAGE_EMOJIS

#: A valid permissions set. This might be an :class:`int`, a :class:`typing.Collection` of :class:`str` permission
#: names, or a :class:`Permission` object.
PermissionLikeT = typing.Union[int, typing.Collection[str], Permission]


__all__ = ["Permission", "PermissionLikeT"]
