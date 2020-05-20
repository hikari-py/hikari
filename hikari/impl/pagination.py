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
from __future__ import annotations

__all__ = []

import datetime

from hikari import pagination
from hikari.models import applications
from hikari.models import bases
from hikari.models import guilds
from hikari.models import messages
from hikari.models import users


class GuildPaginator(pagination.BufferedPaginatedResults[guilds.Guild]):
    __slots__ = ("_app", "_session", "_newest_first", "_first_id")

    def __init__(self, app, newest_first, first_item, session):
        super().__init__()
        self._app = app
        self._newest_first = newest_first
        self._first_id = self._prepare_first_id(
            first_item, bases.Snowflake.max() if newest_first else bases.Snowflake.min(),
        )
        self._session = session

    async def _next_chunk(self):
        kwargs = {"before" if self._newest_first else "after": self._first_id}

        chunk = await self._session.get_current_user_guilds(**kwargs)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]

        return (applications.OwnGuild.deserialize(g, app=self._app) for g in chunk)


class MemberPaginator(pagination.BufferedPaginatedResults[guilds.GuildMember]):
    __slots__ = ("_app", "_guild_id", "_first_id", "_session")

    def __init__(self, app, guild, created_after, session):
        super().__init__()
        self._app = app
        self._guild_id = str(int(guild))
        self._first_id = self._prepare_first_id(created_after)
        self._session = session

    async def _next_chunk(self):
        chunk = await self._session.list_guild_members(self._guild_id, after=self._first_id)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]

        return (guilds.GuildMember.deserialize(m, app=self._app) for m in chunk)


class MessagePaginator(pagination.BufferedPaginatedResults[messages.Message]):
    __slots__ = ("_app", "_channel_id", "_direction", "_first_id", "_session")

    def __init__(self, app, channel, direction, first, session) -> None:
        super().__init__()
        self._app = app
        self._channel_id = str(int(channel))
        self._direction = direction
        self._first_id = (
            str(bases.Snowflake.from_datetime(first)) if isinstance(first, datetime.datetime) else str(int(first))
        )
        self._session = session

    async def _next_chunk(self):
        kwargs = {
            self._direction: self._first_id,
            "channel": self._channel_id,
            "limit": 100,
        }

        chunk = await self._session.get_channel_messages(**kwargs)

        if not chunk:
            return None
        if self._direction == "after":
            chunk.reverse()

        self._first_id = chunk[-1]["id"]

        return (messages.Message.deserialize(m, app=self._app) for m in chunk)


class ReactionPaginator(pagination.BufferedPaginatedResults[messages.Reaction]):
    __slots__ = ("_app", "_channel_id", "_message_id", "_first_id", "_emoji", "_session")

    def __init__(self, app, channel, message, emoji, users_after, session) -> None:
        super().__init__()
        self._app = app
        self._channel_id = str(int(channel))
        self._message_id = str(int(message))
        self._emoji = getattr(emoji, "url_name", emoji)
        self._first_id = self._prepare_first_id(users_after)
        self._session = session

    async def _next_chunk(self):
        chunk = await self._session.get_reactions(
            channel_id=self._channel_id, message_id=self._message_id, emoji=self._emoji, after=self._first_id
        )

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]

        return (users.User.deserialize(u, app=self._app) for u in chunk)
