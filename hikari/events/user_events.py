# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Events fired when the account user is updated."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["OwnUserUpdateEvent"]

import typing

import attr

from hikari.events import shard_events

if typing.TYPE_CHECKING:
    from hikari.api import shard as gateway_shard
    from hikari.models import users


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class OwnUserUpdateEvent(shard_events.ShardEvent):
    """Event fired when the account user is updated."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    user: users.OwnUser = attr.ib()
    """This application user.

    Returns
    -------
    hikari.models.users.OwnUser
        This application user.
    """
