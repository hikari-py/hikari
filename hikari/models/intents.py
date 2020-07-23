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
"""Shard intents for controlling which events the application receives.

All intents in the `Intent` class are exported to this package,
thus `intents.Intent.GUILDS` will behave the same as `intents.GUILDS`.
"""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["Intent"]

# noinspection PyUnresolvedReferences
import typing

from hikari.utilities import flag


@typing.final
class Intent(flag.Flag):
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

    This enum is an `enum.IntFlag`, which means that you can use bitwise
    operators to join and splice multiple intents into one value.

    For example, if we wish to only refer to the `GUILDS` intent, then it is
    simply a case of accessing it normally.

    ```py
    my_intents = Intent.GUILDS
    ```

    If we wanted to have several intents grouped together, we would use the
    bitwise-or operator to combine them (`|`). This can be done in-place
    with the `|=` operator if needed.

    ```py
    # One or two values that fit on one line.
    my_intents = Intents.GUILD_MESSAGES | Intents.DIRECT_MESSAGES

    # Several intents together. You may find it useful to format these like
    # so to keep your code readable.
    my_intents = (
        Intents.GUILDS             |
        Intents.GUILD_BANS         |
        Intents.GUILD_EMOJIS       |
        Intents.GUILD_INTEGRATIONS |
        Intents.GUILD_MESSAGES     |
        Intents.DIRECT_MESSAGES
    )
    ```

    To check if an intent **is present** in a given intents bitfield, you can
    use the bitwise-and operator (`&`) to check. This returns the "intersection"
    or "crossover" between the left and right-hand side of the `&`. You can then
    use the `==` operator to check that specific values are present. You can
    check in-place with the `&=` operator if needed.

    ```py
    if (my_intents & Intents.GUILD_MESSAGES) == Intents.GUILD_MESSAGES:
        print("Guild messages are enabled")

    # Checking if ALL in a combination are set:
    expected_intents = (Intents.GUILD_MESSAGES | Intents.DIRECT_MESSAGES)
    if (my_intents & expected_intents) == expected_intents:
        print("Messages are enabled in guilds and direct messages.")

    # Checking if AT LEAST ONE in a combination is set:
    expected_intents = (Intents.GUILD_MESSAGES | Intents.DIRECT_MESSAGES)
    if my_intents & expected_intents:
        print("Messages are enabled in guilds or direct messages.")
    ```

    Removing one or more intents from a combination can be done with the
    bitwise-xor (`^`) operator. The `^=` operator can do this in-place.

    ```py
    # Remove GUILD_MESSAGES
    my_intents = my_intents ^ Intents.GUILD_MESSAGES
    # or, simplifying:
    my_intents ^= Intents.GUILD_MESSAGES

    # Remove all messages events.
    my_intents = my_intents ^ (Intents.GUILD_MESSAGES | Intents.DIRECT_MESSAGES)
    # or, simplifying
    my_intents ^= (Intents.GUILD_MESSAGES | Intents.DIRECT_MESSAGES)
    ```

    What is and is not covered by intents?
    --------------------------------------

    The following unprivileged events require intents to be dispatched:

    - `GUILD_CREATE`
    - `GUILD_UPDATE`
    - `GUILD_DELETE`
    - `GUILD_ROLE_CREATE`
    - `GUILD_ROLE_UPDATE`
    - `GUILD_ROLE_DELETE`
    - `GUILD_BAN_ADD`
    - `GUILD_BAN_REMOVE`
    - `GUILD_EMOJIS_UPDATE`
    - `GUILD_INTEGRATIONS_UPDATE`
    - `INVITE_CREATE`
    - `INVITE_DELETE`
    - `CHANNEL_CREATE`
    - `CHANNEL_UPDATE`
    - `CHANNEL_DELETE`
    - `CHANNEL_PINS_UPDATE (guilds only)`
    - `MESSAGE_CREATE`
    - `MESSAGE_UPDATE`
    - `MESSAGE_DELETE`
    - `MESSAGE_BULK_DELETE`
    - `MESSAGE_REACTION_ADD`
    - `MESSAGE_REACTION_REMOVE`
    - `MESSAGE_REACTION_REMOVE_ALL`
    - `MESSAGE_REACTION_REMOVE_EMOJI`
    - `TYPING_START`
    - `VOICE_STATE_UPDATE`
    - `WEBHOOKS_UPDATE`

    The following privileged events require intents to be dispatched:

    - `GUILD_MEMBER_ADD`
    - `GUILD_MEMBER_UPDATE`
    - `GUILD_MEMBER_REMOVE`
    - `PRESENCE_UPDATE`

    All events not listed above will be dispatched regardless of whether
    intents are used or not.
    """

    NONE = 0
    """Represents no intents."""

    GUILDS = 1 << 0
    """Subscribes to the following events:

    * `GUILD_CREATE`
    * `GUILD_UPDATE`
    * `GUILD_DELETE`
    * `GUILD_ROLE_CREATE`
    * `GUILD_ROLE_UPDATE`
    * `GUILD_ROLE_DELETE`
    * `CHANNEL_CREATE`
    * `CHANNEL_UPDATE`
    * `CHANNEL_DELETE`
    * `CHANNEL_PINS_UPDATE`
    """

    GUILD_MEMBERS = 1 << 1
    """Subscribes to the following events:

    * `GUILD_MEMBER_ADD`
    * `GUILD_MEMBER_UPDATE`
    * `GUILD_MEMBER_REMOVE`

    !!! warning
        This intent is privileged, and requires enabling/whitelisting to use.
    """

    GUILD_BANS = 1 << 2
    """Subscribes to the following events:

    * `GUILD_BAN_ADD`
    * `GUILD_BAN_REMOVE`
    """

    GUILD_EMOJIS = 1 << 3
    """Subscribes to the following events:

    * `GUILD_EMOJIS_UPDATE`
    """

    GUILD_INTEGRATIONS = 1 << 4
    """Subscribes to the following events:

    * `GUILD_INTEGRATIONS_UPDATE`
    """

    GUILD_WEBHOOKS = 1 << 5
    """Subscribes to the following events:

    * `WEBHOOKS_UPDATE`
    """

    GUILD_INVITES = 1 << 6
    """Subscribes to the following events:

    * `INVITE_CREATE`
    * `INVITE_DELETE`
    """

    GUILD_VOICE_STATES = 1 << 7
    """Subscribes to the following events:

    * `VOICE_STATE_UPDATE`
    """

    GUILD_PRESENCES = 1 << 8
    """Subscribes to the following events:

    * `PRESENCE_UPDATE`

    !!! warning
        This intent is privileged, and requires enabling/whitelisting to use."""

    GUILD_MESSAGES = 1 << 9
    """Subscribes to the following events:

    * `MESSAGE_CREATE` (in guilds only)
    * `MESSAGE_UPDATE` (in guilds only)
    * `MESSAGE_DELETE` (in guilds only)
    * `MESSAGE_BULK_DELETE` (in guilds only)
    """

    GUILD_MESSAGE_REACTIONS = 1 << 10
    """Subscribes to the following events:

    * `MESSAGE_REACTION_ADD` (in guilds only)
    * `MESSAGE_REACTION_REMOVE` (in guilds only)
    * `MESSAGE_REACTION_REMOVE_ALL` (in guilds only)
    * `MESSAGE_REACTION_REMOVE_EMOJI` (in guilds only)
    """

    GUILD_MESSAGE_TYPING = 1 << 11
    """Subscribes to the following events:

    * `TYPING_START` (in guilds only)
    """

    PRIVATE_MESSAGES = 1 << 12
    """Subscribes to the following events:

    * `CHANNEL_CREATE` (in private message channels only)
    * `MESSAGE_CREATE` (in private message channels only)
    * `MESSAGE_UPDATE` (in private message channels only)
    * `MESSAGE_DELETE` (in private message channels only)
    """

    PRIVATE_MESSAGE_REACTIONS = 1 << 13
    """Subscribes to the following events:

    * `MESSAGE_REACTION_ADD` (in private message channels only)
    * `MESSAGE_REACTION_REMOVE` (in private message channels only)
    * `MESSAGE_REACTION_REMOVE_ALL` (in private message channels only)
    * `MESSAGE_REACTION_REMOVE_EMOJI` (in private message channels only)
    """

    PRIVATE_MESSAGE_TYPING = 1 << 14
    """Subscribes to the following events

    * `TYPING_START` (in private message channels only)
    """

    # Annoyingly, enums hide classmethods and staticmethods from __dir__ in
    # EnumMeta which means if I make methods to generate these, then stuff
    # won't be documented by pdoc. Alas, my dream of being smart with
    # operator.or_ and functools.reduce has been destroyed.

    ALL_GUILDS = (
        GUILDS
        | GUILD_BANS
        | GUILD_EMOJIS
        | GUILD_INTEGRATIONS
        | GUILD_WEBHOOKS
        | GUILD_INVITES
        | GUILD_VOICE_STATES
        | GUILD_MESSAGES
        | GUILD_MESSAGE_REACTIONS
        | GUILD_MESSAGE_TYPING
    )
    """All unprivileged guild-related intents."""

    ALL_GUILDS_PRIVILEGED = ALL_GUILDS | GUILD_MEMBERS | GUILD_PRESENCES
    """All unprivileged guild intents and all privileged guild intents.

    This combines `Intent.ALL_GUILDS`, `Intent.GUILD_MEMBERS` and
    `Intent.GUILD_PRESENCES`.

    !!! warning
        This set of intent is privileged, and requires enabling/whitelisting to
        use.
    """

    ALL_DIRECT = PRIVATE_MESSAGES | PRIVATE_MESSAGE_TYPING | PRIVATE_MESSAGE_REACTIONS
    """All direct message intents."""

    ALL_MESSAGES = PRIVATE_MESSAGES | GUILD_MESSAGES
    """All message intents."""

    ALL_MESSAGE_REACTIONS = PRIVATE_MESSAGE_REACTIONS | GUILD_MESSAGE_REACTIONS
    """All message reaction intents."""

    ALL_MESSAGE_TYPING = PRIVATE_MESSAGE_TYPING | GUILD_MESSAGE_TYPING
    """All typing indicator intents."""

    ALL = (
        GUILDS
        | GUILD_BANS
        | GUILD_EMOJIS
        | GUILD_INTEGRATIONS
        | GUILD_WEBHOOKS
        | GUILD_INVITES
        | GUILD_VOICE_STATES
        | GUILD_MESSAGES
        | GUILD_MESSAGE_REACTIONS
        | GUILD_MESSAGE_TYPING
        | PRIVATE_MESSAGES
        | PRIVATE_MESSAGE_REACTIONS
        | PRIVATE_MESSAGE_TYPING
    )
    """All unprivileged intents."""

    ALL_PRIVILEGED = ALL | GUILD_MEMBERS | GUILD_PRESENCES
    """All unprivileged and privileged intents.

    !!! warning
        This set of intent is privileged, and requires enabling/whitelisting to
        use.
    """

    @property
    def is_privileged(self) -> bool:
        """Determine whether the intent requires elevated privileges.

        If this is `builtins.True`, you will be required to opt-in to using
        this intent on the Discord Developer Portal before you can utilise it
        in your application.
        """
        return bool(self & (self.GUILD_MEMBERS | self.GUILD_PRESENCES))


def __getattr__(name: str) -> Intent:
    return typing.cast("Intent", getattr(Intent, name))
