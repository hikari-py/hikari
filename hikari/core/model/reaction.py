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
import typing

from hikari.core.model import emoji
from hikari.core.model import model_cache


@dataclasses.dataclass()
class Reaction:
    """
    Model for a message reaction object
    """

    __slots__ = ("_state", "count", "me", "emoji")

    _state: typing.Any

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
    #: :type: :class:`hikari.core.model.emoji.Emoji`
    emoji: emoji.Emoji

    def __init__(self, global_state: model_cache.AbstractModelCache, payload):
        self._state = global_state
        self.count = payload["count"]
        self.me = payload.get("me", False)
        #: TODO: get the guild for the emoji by doing an API call if need be
        self.emoji = global_state.parse_emoji(payload.get("emoji"), None)


__all__ = ["Reaction"]
