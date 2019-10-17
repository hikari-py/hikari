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
Reactions to a message.
"""
from __future__ import annotations

import dataclasses

from hikari.core.internal import state_registry
from hikari.core.models import emoji, base
from hikari.core.models import message
from hikari.core.utils import auto_repr
from hikari.core.utils import custom_types


@dataclasses.dataclass()
class Reaction(base.HikariModel):
    """
    Model for a message reaction object
    """

    __slots__ = ("_state", "count", "me", "emoji", "message")

    _state: state_registry.StateRegistry

    #: The number of times the emoji has been used on this message.
    #:
    #: :type: :class:`int`
    count: int

    #: True if the bot added this.
    #:
    #: :type: :class:`bool`
    me: bool

    #: The emoji used for the reaction
    #:
    #: :type: :class:`hikari.core.models.emoji.AbstractEmoji`
    emoji: emoji.Emoji

    #: The message that was reacted on
    #:
    #: :type: :class:`hikari.core.models.message.Message`
    message: message.Message

    __repr__ = auto_repr.repr_of("me", "count", "emoji")

    def __init__(
        self,
        global_state: state_registry.StateRegistry,
        payload: custom_types.DiscordObject,
        message_obj: message.Message,
    ) -> None:
        self._state = global_state
        self.count = payload["count"]
        self.me = payload.get("me", False)
        self.emoji = global_state.parse_emoji(payload["emoji"], None)
        self.message = message_obj


__all__ = ["Reaction"]
