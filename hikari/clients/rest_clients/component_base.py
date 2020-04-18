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
"""The abstract class that all REST client logic classes should inherit from."""

__all__ = ["BaseRESTComponent"]

import abc
import types
import typing

from hikari.internal import meta
from hikari.net import rest_sessions


class BaseRESTComponent(abc.ABC, metaclass=meta.UniqueFunctionMeta):
    """An abstract class that all REST client logic classes should inherit from.

    This defines the abstract method ``__init__`` which will assign an instance
    of :obj:`~hikari.net.rest_sessions.LowLevelRestfulClient` to the attribute that all
    components will expect to make calls to.
    """

    @abc.abstractmethod
    def __init__(self, session: rest_sessions.LowLevelRestfulClient) -> None:
        self._session: rest_sessions.LowLevelRestfulClient = session

    async def __aenter__(self) -> "BaseRESTComponent":
        return self

    async def __aexit__(
        self, exc_type: typing.Type[BaseException], exc_val: BaseException, exc_tb: types.TracebackType
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Shut down the REST client safely."""
        await self._session.close()

    @property
    def session(self) -> rest_sessions.LowLevelRestfulClient:
        """Get the :obj:`hikari.net.rest_sessions.LowLevelRestfulClient` session object."""
        return self._session
