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
"""The abstract class that all RESTSession client logic classes should inherit from."""

from __future__ import annotations

__all__ = ["BaseRESTComponent"]

import abc
import typing

from hikari.internal import meta

if typing.TYPE_CHECKING:
    import types

    from hikari.components import application

    from . import session as rest_session


class BaseRESTComponent(abc.ABC, metaclass=meta.UniqueFunctionMeta):
    """An abstract class that all RESTSession client logic classes should inherit from.

    This defines the abstract method `__init__` which will assign an instance
    of `hikari.net.rest.RESTSession` to the attribute that all application will expect
    to make calls to.
    """

    @abc.abstractmethod
    def __init__(self, app: application.Application, session: rest_session.RESTSession) -> None:
        self._app = app
        self._session = session

    async def __aenter__(self) -> BaseRESTComponent:
        return self

    async def __aexit__(
        self, exc_type: typing.Type[BaseException], exc_val: BaseException, exc_tb: types.TracebackType
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Shut down the RESTSession client safely."""
        await self._session.close()

    @property
    def global_ratelimit_queue_size(self) -> int:
        """Count of API calls waiting for the global ratelimiter to release.

        If this is non-zero, then you are being globally ratelimited.
        """
        return len(self._session.global_ratelimiter.queue)

    @property
    def route_ratelimit_queue_size(self) -> int:
        """Count of API waiting for a route-specific ratelimit to release.

        If this is non-zero, then you are being ratelimited somewhere.
        """
        return sum(len(r.queue) for r in self._session.bucket_ratelimiters.real_hashes_to_buckets.values())
