# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Core app interface for application implementations."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IApp"]

import abc
import typing

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari import config
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_


class IApp(abc.ABC):
    """The core interface for a Hikari application."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def cache(self) -> cache_.ICacheComponent:
        """Entity cache.

        Returns
        -------
        hikari.api.cache.ICacheComponent
            The cache implementation used in this application.
        """

    @property
    @abc.abstractmethod
    def entity_factory(self) -> entity_factory_.IEntityFactoryComponent:
        """Entity creator and updater facility.

        Returns
        -------
        hikari.api.entity_factory.IEntityFactoryComponent
            The factory object used to produce and update Python entities.
        """

    @property
    @abc.abstractmethod
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        """Thread-pool to utilise for file IO within the library, if set.

        Returns
        -------
        concurrent.futures.Executor or builtins.None
            The custom thread-pool being used for blocking IO. If the
            default event loop thread-pool is being used, then this will
            return `builtins.None` instead.
        """

    @property
    @abc.abstractmethod
    def http_settings(self) -> config.HTTPSettings:
        """HTTP-specific settings."""

    @property
    @abc.abstractmethod
    def is_debug_enabled(self) -> bool:
        """Debug status for the application.

        Returns
        -------
        builtins.bool
            `builtins.True` if the application is running in a debugging mode,
            or `builtins.False` if it is not.

            Generally this will be `builtins.False`.
        """

    @property
    @abc.abstractmethod
    def proxy_settings(self) -> config.ProxySettings:
        """Proxy-specific settings."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Safely shut down all resources."""
