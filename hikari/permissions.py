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

__all__: typing.Sequence[str] = ("Permissions",)

import typing

from hikari.internal import enums


@typing.final
class Permissions(enums.Flag):
    """Represents the permissions available in a given channel or guild.

    This enum is an [`enum.IntFlag`][], which means that it is stored as a bit field
    where each bit represents a permission. You can use bitwise operators
    to efficiently manipulate and compare permissions.

    Examples
    --------
    You can create an enum which combines multiple permissions using the bitwise OR operator (`|`):

    ```py
       my_perms = Permissions.MANAGE_CHANNELS | Permissions.MANAGE_GUILD

       required_perms = (
           Permissions.CREATE_INSTANT_INVITE
           | Permissions.KICK_MEMBERS
           | Permissions.BAN_MEMBERS
           | Permissions.MANAGE_GUILD
       )
    ```

    To find the intersection of two sets of permissions, use the bitwise AND
    operator (`&`) between them. By then applying the `==` operator, you can check if all
    permissions from one set are present in another set. This is useful, for instance,
    for checking if a user has all the required permissions

    ```py
       if (my_perms & required_perms) == required_perms:
           print("I have all of the required permissions!")
       else:
           print("I am missing at least one required permission!")
    ```

    To determine which permissions from one set are missing from another, you can use the
    bitwise equivalent of the set difference operation, as shown below. This can be used,
    for instance, to find which of a user's permissions are missing from the required permissions.

    ```py
        missing_perms = ~my_perms & required_perms
        if (missing_perms):
            print(f"I'm missing these permissions: {missing_perms}")
    ```

    Lastly, if you need all the permissions from a set except for a few,
    you can use the bitwise NOT operator (`~`).

    ```py
        # All permissions except ADMINISTRATOR.
        my_perms = ~Permissions.ADMINISTRATOR
    ```
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
    """Allows for sending of [/tts][] messages."""

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
    """Allows for using the `@everyone`, `@here` and `@role` (regardless of its mention status) tag to notify users."""

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

    MANAGE_GUILD_EXPRESSIONS = 1 << 30
    """Allows management and editing emojis, stickers and soundboard sounds.

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

    MANAGE_EVENTS = 1 << 33
    """Allows for management and editing scheduled events"""

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
    """Allows for launching activities in a voice channel.

    Activities are applications that have the [`hikari.applications.ApplicationFlags.EMBEDDED`][] flag.
    """

    MODERATE_MEMBERS = 1 << 40
    """Allows for timing out members."""

    VIEW_CREATOR_MONETIZATION_ANALYTICS = 1 << 41
    """Allows for viewing role subscription insights"""

    USE_SOUNDBOARD = 1 << 42
    """Allows the use of soundboard in a voice chat."""

    CREATE_GUILD_EXPRESSIONS = 1 << 43
    """Allows to create guild emojis, stickers and soundboard sounds.

    Additionally, it allows to edit and manage those created by the user.
    """

    CREATE_EVENTS = 1 << 44
    """Allows to create scheduled events.

    Additionally, it allows to edit and manage those created by the user.
    """

    USE_EXTERNAL_SOUNDS = 1 << 45
    """Allows the use of soundboard sounds from external servers."""

    SEND_VOICE_MESSAGES = 1 << 46
    """Allows sending voice messages."""

    @classmethod
    def all_permissions(cls) -> Permissions:
        """Get an instance of [`hikari.permissions.Permissions`][] with all the known permissions.

        Returns
        -------
        Permissions
            A permissions instance with all the known permissions.
        """
        all_perms = Permissions.NONE
        for perm in Permissions:
            all_perms |= perm

        return all_perms
