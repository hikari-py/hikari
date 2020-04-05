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
"""Provides a base for any type of websocket client."""

__all__ = ["RunnableClient"]

import abc
import asyncio
import contextlib
import logging
import signal


class RunnableClient(abc.ABC):
    """Base for any websocket client that must be kept alive."""

    __slots__ = ("logger",)

    #: The logger to use for this client.
    #:
    #: :type: :obj:`logging.Logger`
    logger: logging.Logger

    @abc.abstractmethod
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    @abc.abstractmethod
    async def start(self) -> None:  # noqa: D401
        """Start the component."""

    @abc.abstractmethod
    async def close(self, wait: bool = True) -> None:
        """Shut down the component."""

    @abc.abstractmethod
    async def join(self) -> None:
        """Wait for the component to terminate."""

    def run(self) -> None:
        """Execute this component on an event loop.

        Performs the same job as :meth:`start`, but provides additional
        preparation such as registering OS signal handlers for interrupts,
        and preparing the initial event loop.

        This enables the client to be run immediately without having to
        set up the :mod:`asyncio` event loop manually first.
        """
        loop = asyncio.get_event_loop()

        def sigterm_handler(*_):
            raise KeyboardInterrupt()

        ex = None

        try:
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.add_signal_handler(signal.SIGTERM, sigterm_handler)

            loop.run_until_complete(self.start())
            loop.run_until_complete(self.join())

            self.logger.info("client has shut down")

        except KeyboardInterrupt as _ex:
            self.logger.info("received signal to shut down client")
            loop.run_until_complete(self.close())
            # Apparently you have to alias except clauses or you get an
            # UnboundLocalError.
            ex = _ex
        finally:
            loop.run_until_complete(self.close(True))
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.remove_signal_handler(signal.SIGTERM)

        if ex:
            raise ex from ex
