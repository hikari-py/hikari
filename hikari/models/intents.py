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
"""Shard intents for controlling which events the application receives."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["Intent"]

import enum

# noinspection PyUnresolvedReferences
import typing


@enum.unique
@typing.final
class Intent(enum.IntFlag):
    """Represents an intent on the gateway.

    This is a bitfield representation of all the categories of event
    that you wish to receive.

    Any events not in an intent category will be fired regardless of what
    intents you provide.

    !!! info
        Discord now places limits on certain events you can receive without
        whitelisting your bot first. On the `Bot` tab in the developer's portal
        for your bot, you should now have the option to enable functionality
        for receiving these events.

        If you attempt to request an intent type that you have not whitelisted
        your bot for, you will be disconnected on startup with a `4014` closure
        code.

    !!! warning
        If you are using the V7 Gateway, you will be REQUIRED to provide some
        form of intent value when you connect. Failure to do so may result in
        immediate termination of the session server-side.
    """

    GUILDS = 1 << 0
    """Subscribes to the following events:

    * GUILD_CREATE
    * GUILD_UPDATE
    * GUILD_DELETE
    * GUILD_ROLE_CREATE
    * GUILD_ROLE_UPDATE
    * GUILD_ROLE_DELETE
    * CHANNEL_CREATE
    * CHANNEL_UPDATE
    * CHANNEL_DELETE
    * CHANNEL_PINS_UPDATE
    """

    GUILD_MEMBERS = 1 << 1
    """Subscribes to the following events:

    * GUILD_MEMBER_ADD
    * GUILD_MEMBER_UPDATE
    * GUILD_MEMBER_REMOVE

    !!! warning
        This intent is privileged, and requires enabling/whitelisting to use.
    """

    GUILD_BANS = 1 << 2
    """Subscribes to the following events:

    * GUILD_BAN_ADD
    * GUILD_BAN_REMOVE
    """

    GUILD_EMOJIS = 1 << 3
    """Subscribes to the following events:

    * GUILD_EMOJIS_UPDATE
    """

    GUILD_INTEGRATIONS = 1 << 4
    """Subscribes to the following events:

    * GUILD_INTEGRATIONS_UPDATE
    """

    GUILD_WEBHOOKS = 1 << 5
    """Subscribes to the following events:

    * WEBHOOKS_UPDATE
    """

    GUILD_INVITES = 1 << 6
    """Subscribes to the following events:

    * INVITE_CREATE
    * INVITE_DELETE
    """

    GUILD_VOICE_STATES = 1 << 7
    """Subscribes to the following events:

    * VOICE_STATE_UPDATE
    """

    GUILD_PRESENCES = 1 << 8
    """Subscribes to the following events:

    * PRESENCE_UPDATE

    !!! warning
        This intent is privileged, and requires enabling/whitelisting to use."""

    GUILD_MESSAGES = 1 << 9
    """Subscribes to the following events:

    * MESSAGE_CREATE
    * MESSAGE_UPDATE
    * MESSAGE_DELETE
    * MESSAGE_BULK
    """

    GUILD_MESSAGE_REACTIONS = 1 << 10
    """Subscribes to the following events:

    * MESSAGE_REACTION_ADD
    * MESSAGE_REACTION_REMOVE
    * MESSAGE_REACTION_REMOVE_ALL
    * MESSAGE_REACTION_REMOVE_EMOJI
    """

    GUILD_MESSAGE_TYPING = 1 << 11
    """Subscribes to the following events:

    * TYPING_START
    """

    DIRECT_MESSAGES = 1 << 12
    """Subscribes to the following events:

    * CHANNEL_CREATE
    * MESSAGE_CREATE
    * MESSAGE_UPDATE
    * MESSAGE_DELETE
    """

    DIRECT_MESSAGE_REACTIONS = 1 << 13
    """Subscribes to the following events:

    * MESSAGE_REACTION_ADD
    * MESSAGE_REACTION_REMOVE
    * MESSAGE_REACTION_REMOVE_ALL
    """

    DIRECT_MESSAGE_TYPING = 1 << 14
    """Subscribes to the following events

    * TYPING_START
    """

    def __str__(self) -> str:
        return self.name

    @property
    def is_privileged(self) -> bool:
        """Whether the intent requires elevated privileges.

        If this is `True`, you will be required to opt-in to using this intent
        on the Discord Developer Portal before you can utilise it in your
        application.
        """
        return bool(self & (Intent.GUILD_MEMBERS | Intent.GUILD_PRESENCES))
