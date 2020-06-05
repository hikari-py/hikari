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
"""Basic implementation of a cache for general bots and gateway apps."""

from __future__ import annotations

__all__ = ["InMemoryCacheImpl"]

import typing

from hikari.api import cache

if typing.TYPE_CHECKING:
    from hikari.api import app as app_


class InMemoryCacheImpl(cache.ICache):
    """In-memory cache implementation."""

    def __init__(self, app: app_.IApp) -> None:
        self._app = app

    @property
    def app(self) -> app_.IApp:
        return self._app
