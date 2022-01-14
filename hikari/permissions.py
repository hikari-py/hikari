# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Bitfield of permissions."""

from __future__ import annotations

__all__: typing.List[str] = ["Permissions"]

import functools
import operator
import typing

from hikari.internal import enums


@typing.final
class Permissions(enums.Flag):
    """Represents the permissions available in a given channel or guild.

    This enum is an `enum.IntFlag`. This means that you can **combine multiple
    permissions together** into one value using the bitwise-OR operator (`|`).

        my_perms = Permissions.MANAGE_CHANNELS | Permissions.MANAGE_GUILD

        your_perms = (
            Permissions.CREATE_INSTANT_INVITE
            | Permissions.KICK_MEMBERS
            | Permissions.BAN_MEMBERS
            | Permissions.MANAGE_GUILD
        )

    You can **check if a permission is present** in a set of combined
    permissions by using the bitwise-AND operator (`&`). This will return
    the int-value of the permission if it is present, or `0` if not present.

        my_perms = Permissions.MANAGE_CHANNELS | Permissions.MANAGE_GUILD

        if my_perms & Permissions.MANAGE_CHANNELS:
            if my_perms & Permissions.MANAGE_GUILD:
                print("I have the permission to both manage the guild and the channels in it!")
            else:
                print("I have the permission to manage channels!")
        else:
            print("I don't have the permission to manage channels!")

        # Or you could simplify it:

        if my_perms & (Permissions.MANAGE_CHANNELS | Permissions.MANAGE_GUILD):
            print("I have the permission to both manage the guild and the channels in it!")
        elif my_perms & Permissions.MANAGE_CHANNELS:
            print("I have the permission to manage channels!")
        else:
            print("I don't have the permission to manage channels!")

    If you need to **check that a permission is not present**, you can use the
    bitwise-XOR operator (`^`) to check. If the permission is not present, it
    will return a non-zero value, otherwise if it is present, it will return `0`.

        my_perms = Permissions.MANAGE_CHANNELS | Permissions.MANAGE_GUILD

        if my_perms ^ Permissions.MANAGE_CHANNELS:
            print("Please give me the MANAGE_CHANNELS permission!")

    Lastly, if you need all the permissions set except the permission you want,
    you can use the inversion operator (`~`) to do that.

        # All permissions except ADMINISTRATOR.
        my_perms = ~Permissions.ADMINISTRATOR

    """

    NONE = 0
    """Empty permission."""

    CREATE_INSTANT_INVITE = 1 << 0
    """Allows creation of instant invites."""

    KICK_MEMBERS = 1 << 1
    """Allows kicking members.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    BAN_MEMBERS = 1 << 2
    """Allows banning members.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    ADMINISTRATOR = 1 << 3
    """Allows all permissions and bypasses channel permission overwrites.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    MANAGE_CHANNELS = 1 << 4
    """Allows management and editing of channels.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    MANAGE_GUILD = 1 << 5
    """Allows management and editing of the guild.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

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
    """Allows for deletion of other users messages.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

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
    """Allows the usage of custom emojis from other guilds."""

    VIEW_GUILD_INSIGHTS = 1 << 19
    """Allows the user to view guild insights for eligible guilds."""

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

    USE_VOICE_ACTIVITY = 1 << 25
    """Allows for using voice-activity-detection in a voice channel."""

    CHANGE_NICKNAME = 1 << 26
    """Allows for modification of own nickname."""

    MANAGE_NICKNAMES = 1 << 27
    """Allows for modification of other users nicknames."""

    MANAGE_ROLES = 1 << 28
    """Allows management and editing of roles.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    MANAGE_WEBHOOKS = 1 << 29
    """Allows management and editing of webhooks.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    MANAGE_EMOJIS_AND_STICKERS = 1 << 30
    """Allows management and editing of emojis and stickers.

    !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    USE_APPLICATION_COMMANDS = 1 << 31
    """Allows for using the application commands of guild integrations within a text channel."""

    REQUEST_TO_SPEAK = 1 << 32
    """Allows for requesting to speak in stage channels.

    !!! warning
        This permissions is currently defined as being "under active
        development" by Discord meaning that "it may be changed or removed"
        without warning.
    """

    MANAGE_THREADS = 1 << 34
    """Allows for deleting and archiving threads, and viewing all private threads.

     !!! note
        In guilds with server-wide 2FA enabled this permission can only be used
        by users who have two-factor authentication enabled on their account
        (or their owner's account in the case of bot users) and the guild owner.
    """

    CREATE_PUBLIC_THREADS = 1 << 35
    """Allows for creating threads."""

    CREATE_PRIVATE_THREADS = 1 << 36
    """Allows for creating private threads."""

    USE_EXTERNAL_STICKERS = 1 << 37
    """Allows the usage of custom stickers from other servers."""

    SEND_MESSAGES_IN_THREADS = 1 << 38
    """Allows for sending messages in threads."""

    START_EMBEDDED_ACTIVITIES = 1 << 39
    """Allows for launching activities (applications with the `EMBEDDED` flag) in a voice channel."""

    MODERATE_MEMBERS = 1 << 40
    """Allows for timing out members."""

    @classmethod
    def all_permissions(cls) -> Permissions:
        """Get an instance of `Permissions` with all the known permissions.

        Returns
        -------
        Permissions
            A permissions instance with all the known permissions.
        """
        return functools.reduce(operator.ior, Permissions)
