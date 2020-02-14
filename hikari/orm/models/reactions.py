#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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

import typing

from hikari.internal_utilities import reprs
from hikari.orm.models import bases

if typing.TYPE_CHECKING:
    from hikari.orm import _fabric
    from hikari.orm.models import channels as _channel
    from hikari.orm.models import messages as _message
    from hikari.orm.models import emojis as _emoji


class Reaction(bases.BaseModelWithFabric):
    """
    Model for a message reaction object
    """

    __slots__ = ("_fabric", "count", "emoji", "channel_id", "message_id")

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
    #: :type: :class:`hikari.orm.models.emojis.Emoji`
    emoji: _emoji.Emoji

    #: The ID of the channel that was reacted in.
    #:
    #: :type: :class:`int`
    channel_id: int

    #: The ID of the message that was reacted on.
    #:
    #: :type: :class:`int`
    message_id: int

    def __init__(
        self, fabric_obj: _fabric.Fabric, count: int, emoji: _emoji.Emoji, message_id: int, channel_id: int
    ) -> None:
        self._fabric = fabric_obj
        self.count = count
        self.emoji = emoji
        self.channel_id = channel_id
        self.message_id = message_id

    async def fetch_channel(self) -> _channel.Channel:
        """
        Retrieve the channel this reaction happened in with a REST request.

        Returns:
            A `hikari.orm.models.channel.Channel` object.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If the current token doesn't have access to the channel.
            hikari.net.errors.NotFoundHTTPError:
                If the channel does not exist.
        """
        return await self._fabric.http_adapter.fetch_channel(channel=self.channel_id)

    def get_channel(self) -> typing.Optional[_channel.Channel]:
        """
        Get the channel this reaction happened in from the cache.

        Returns:
            A `hikari.orm.models.channel.Channel` object or :class:`None`.
        """
        return self._fabric.state_registry.get_channel_by_id(channel_id=self.channel_id)

    async def fetch_message(self) -> _message.Message:
        """
        Retrieve the message this reaction is attached to with a REST request.

        Returns:
            A `hikari.orm.models.message.Message` object.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack permission to see the message.
            hikari.net.errors.NotFoundHTTPError:
                If the message ID or channel ID is not found.
        """
        return await self._fabric.http_adapter.fetch_message(message=self.message_id, channel=self.channel_id)

    def get_message(self) -> typing.Optional[_message.Message]:
        """
        Get the message this reaction is attached to from the cache.

        Returns:
            A `hikari.orm.models.message.Message` object or :class:`None`.
        """
        return self._fabric.state_registry.get_message_by_id(message_id=self.message_id)

    __repr__ = reprs.repr_of("count", "emoji", "channel_id", "message_id")


__all__ = ["Reaction"]
