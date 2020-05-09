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
"""A library wide base for storing client components."""

from __future__ import annotations

__all__ = ["Components"]

import typing

import attr

if typing.TYPE_CHECKING:
    from hikari.clients import configs  # pylint: disable=cyclic-import
    from hikari.clients import rest  # pylint: disable=cyclic-import
    from hikari.clients import shards  # pylint: disable=cyclic-import
    from hikari.events import dispatchers, event_managers


@attr.s(repr=False)
class Components:
    """A base that defines placement for set of components used in the library."""

    config: configs.BotConfig = attr.attrib(default=None)
    """The config used for this bot."""

    event_dispatcher: dispatchers.EventDispatcher = attr.attrib(default=None)
    """The event dispatcher for this bot."""

    event_manager: event_managers.EventManager = attr.attrib(default=None)
    """The event manager for this bot."""

    rest: rest.RESTClient = attr.attrib(default=None)
    """The REST HTTP client to use for this bot."""

    shards: typing.Mapping[int, shards.ShardClient] = attr.attrib(default=None)
    """Shards registered to this bot.

    These will be created once the bot has started execution.
    """
