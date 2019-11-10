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

from hikari.core.models import base
from hikari.core.models import emojis as _emoji
from hikari.core.models import messages as _message
from hikari.internal_utilities import auto_repr


@dataclasses.dataclass()
class Reaction(base.HikariModel):
    """
    Model for a message reaction object
    """

    __slots__ = ("count", "emoji", "message")

    #: The number of times the emoji has been used on this message.
    #:
    #: :type: :class:`int`
    #:
    #: Warning:
    #:     This value may not be completely accurate. To get an accurate count, either request the message from the
    #:     HTTP API, or request the list of users who reacted to it.
    count: int

    #: The emoji used for the reaction.
    #:
    #: :type: :class:`hikari.core.models.emoji.AbstractEmoji`
    emoji: _emoji.Emoji

    #: The message that was reacted on.
    #:
    #: :type: :class:`hikari.core.models.message.Message`
    message: _message.Message

    __repr__ = auto_repr.repr_of("count", "emoji", "message.id")


__all__ = ["Reaction"]
