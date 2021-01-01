# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Shard intents for controlling which events the application receives."""

from __future__ import annotations

__all__: typing.List[str] = ["Intents"]

import typing

from hikari.internal import enums


@typing.final
class Intents(enums.Flag):
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
    my_intents = Intents.GUILDS
    ```

    If we wanted to have several intents grouped together, we would use the
    bitwise-or operator to combine them (`|`). This can be done in-place
    with the `|=` operator if needed.

    ```py
    # One or two values that fit on one line.
    my_intents = Intents.GUILD_MESSAGES | Intents.PRIVATE_MESSAGES

    # Several intents together. You may find it useful to format these like
    # so to keep your code readable.
    my_intents = (
        Intents.GUILDS             |
        Intents.GUILD_BANS         |
        Intents.GUILD_EMOJIS       |
        Intents.GUILD_INTEGRATIONS |
        Intents.GUILD_MESSAGES     |
        Intents.PRIVATE_MESSAGES
    )
    ```

    To check if an intent **is present** in a given intents bitfield, you can
    use the bitwise-and operator (`&`) to check. This returns the "intersection"
    or "crossover" between the left and right-hand side of the `&`. You can then
    use the `==` operator to check that specific values are present. You can
    check in-place with the `&=` operator if needed.

    ```py
    # Check if an intent is set:
    if (my_intents & Intents.GUILD_MESSAGES) == Intents.GUILD_MESSAGES:
        print("Guild messages are enabled")

    # Checking if ALL in a combination are set:
    expected_intents = (Intents.GUILD_MESSAGES | Intents.PRIVATE_MESSAGES)
    if (my_intents & expected_intents) == expected_intents:
        print("Messages are enabled in guilds and private messages.")

    # Checking if AT LEAST ONE in a combination is set:
    expected_intents = (Intents.GUILD_MESSAGES | Intents.PRIVATE_MESSAGES)
    if my_intents & expected_intents:
        print("Messages are enabled in guilds or private messages.")
    ```

    Removing one or more intents from a combination can be done with the
    bitwise-xor (`^`) operator. The `^=` operator can do this in-place.

    ```py
    # Remove GUILD_MESSAGES
    my_intents = my_intents ^ Intents.GUILD_MESSAGES
    # or, simplifying:
    my_intents ^= Intents.GUILD_MESSAGES

    # Remove all messages events.
    my_intents = my_intents ^ (Intents.GUILD_MESSAGES | Intents.PRIVATE_MESSAGES)
    # or, simplifying
    my_intents ^= (Intents.GUILD_MESSAGES | Intents.PRIVATE_MESSAGES)
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
    - `INTEGRATION_CREATE`
    - `INTEGRATION_DELETE`
    - `INTEGRATION_UPDATE`
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

    * `INTEGRATION_CREATE`
    * `INTEGRATION_DELETE`
    * `INTEGRATION_UPDATE`
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

    DM_MESSAGES = 1 << 12
    """Subscribes to the following events:

    * `MESSAGE_CREATE` (in private message channels (non-guild bound) only)
    * `MESSAGE_UPDATE` (in private message channels (non-guild bound) only)
    * `MESSAGE_DELETE` (in private message channels (non-guild bound) only)
    """

    DM_MESSAGE_REACTIONS = 1 << 13
    """Subscribes to the following events:

    * `MESSAGE_REACTION_ADD` (in private message channels (non-guild bound) only)
    * `MESSAGE_REACTION_REMOVE` (in private message channels (non-guild bound) only)
    * `MESSAGE_REACTION_REMOVE_ALL` (in private message channels (non-guild bound) only)
    * `MESSAGE_REACTION_REMOVE_EMOJI` (in private message channels (non-guild bound) only)
    """

    DM_MESSAGE_TYPING = 1 << 14
    """Subscribes to the following events

    * `TYPING_START` (in private message channels (non-guild bound) only)
    """

    # Annoyingly, enums hide classmethods and staticmethods from __dir__ in
    # EnumMeta which means if I make methods to generate these, then stuff
    # will not be documented by pdoc. Alas, my dream of being smart with
    # operator.or_ and functools.reduce has been destroyed.

    ALL_GUILDS_UNPRIVILEGED = (
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

    ALL_GUILDS_PRIVILEGED = GUILD_MEMBERS | GUILD_PRESENCES
    """All privileged guild intents.

    !!! warning
        This set of intent is privileged, and requires enabling/whitelisting to
        use.
    """

    ALL_GUILDS = ALL_GUILDS_UNPRIVILEGED | ALL_GUILDS_PRIVILEGED
    """All unprivileged guild intents and all privileged guild intents.

    This combines `Intents.ALL_GUILDS_UNPRIVILEGED` and
    `Intents.ALL_GUILDS_PRIVILEGED`.

    !!! warning
        This set of intent is privileged, and requires enabling/whitelisting to
        use.
    """

    ALL_DMS = DM_MESSAGES | DM_MESSAGE_TYPING | DM_MESSAGE_REACTIONS
    """All private message channel (non-guild bound) intents."""

    ALL_MESSAGES = DM_MESSAGES | GUILD_MESSAGES
    """All message intents."""

    ALL_MESSAGE_REACTIONS = DM_MESSAGE_REACTIONS | GUILD_MESSAGE_REACTIONS
    """All message reaction intents."""

    ALL_MESSAGE_TYPING = DM_MESSAGE_TYPING | GUILD_MESSAGE_TYPING
    """All typing indicator intents."""

    ALL_UNPRIVILEGED = ALL_GUILDS_UNPRIVILEGED | ALL_DMS
    """All unprivileged intents."""

    ALL_PRIVILEGED = ALL_GUILDS_PRIVILEGED
    """All privileged intents.

    !!! warning
        This set of intent is privileged, and requires enabling/whitelisting to
        use.
    """

    ALL = ALL_UNPRIVILEGED | ALL_PRIVILEGED
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
