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

__all__ = ["IBaseApp"]

import abc
import logging
import typing

from concurrent import futures

if typing.TYPE_CHECKING:
    from hikari import cache as cache_
    from hikari import entity_factory as entity_factory_


class IBaseApp(abc.ABC):
    """Core components that any Hikari-based application will usually need."""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def logger(self) -> logging.Logger:
        """Logger for logging messages."""

    @property
    @abc.abstractmethod
    def cache(self) -> cache_.ICache:
        """Entity cache."""

    @property
    @abc.abstractmethod
    def entity_factory(self) -> entity_factory_.IEntityFactory:
        """Entity creator and updater facility."""

    @property
    @abc.abstractmethod
    def thread_pool(self) -> typing.Optional[futures.ThreadPoolExecutor]:
        """The optional library-wide thread-pool to utilise for file IO."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Safely shut down all resources."""
