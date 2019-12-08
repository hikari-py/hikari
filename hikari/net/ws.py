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
"""
Subclass for :class:`aiohttp.ClientWebSocketResponse` that provides some more useful
functionality for general websocket interaction.
"""
from __future__ import annotations

import dataclasses
import typing
import warnings

import aiohttp.client

from hikari.net import opcodes


def _promote_to_bytes(str_like: typing.AnyStr, encoding="utf-8") -> bytes:
    return str_like.encode(encoding, errors="ignore") if isinstance(str_like, str) else str_like


@dataclasses.dataclass(frozen=True)
class WebSocketClosure(RuntimeError):
    """
    Raised when the server shuts down the connection unexpectedly.
    """

    __slots__ = ("code", "reason")

    #: The closure code provided.
    code: int
    #: The message provided.
    reason: str


_NO_REASON = "no reason"

# Ignore the warning aiohttp provides us.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # noinspection PyMethodOverriding
    class WebSocketClientSession(aiohttp.ClientSession):
        """
        Wraps an aiohttp ClientSession and provides the defaults needed to work with websockets
        easily.

        Warning:
            This must be initialized within a coroutine while an event loop is active
            and registered to the current thread.
        """

        __slots__ = ()

        def __init__(self, **kwargs) -> None:
            kwargs["ws_response_class"] = WebSocketClientResponse
            super().__init__(**kwargs)

        # noinspection PyProtectedMember
        def ws_connect(self, url: str, **kwargs):
            """
            Wraps around :meth:`aiohttp.ClientSession.ws_connect` to provide sane defaults.
            All arguments are otherwise inherited normally, except for `max_msg_size` which is
            disabled in this implementation unless specified by default; `autoping` which is
            forced to be enabled, and `autoclose` which is forced to be disabled.
            """
            # Disable max message size, as Discord is awkward with how they chunk messages.

            kwargs.setdefault("max_msg_size", 0)
            kwargs["autoclose"] = False
            kwargs["autoping"] = True
            return super().ws_connect(url, **kwargs)

        # Suppress inheritance DeprecationWarning.
        @classmethod
        def __init_subclass__(cls, **kwargs):
            pass


# noinspection PyMethodOverriding
class WebSocketClientResponse(aiohttp.ClientWebSocketResponse):
    """
    Specialization of :class:`aiohttp.ClientWebSocketResponse` which provides exception-based
    handling of server-side closures, and the ability to receive str-or-bytes arbitrarily.

    Also provides a :class:`str`-based interface for handling closure messages rather than relying
    on manual decoding and encoding.
    """

    __slots__ = ()

    def close(
        self, *, code: int = opcodes.GatewayClosure.NORMAL_CLOSURE, reason: str = _NO_REASON
    ) -> typing.Awaitable[bool]:
        """
        Closes the connection.

        Args:
            code:
                The code to close with, defaults to 1000.
            reason:
                The reason to close with, defaults to "no reason"

        Returns:
            True if the connection just closed, False if it was already closed.
        """
        return super().close(code=code, message=_promote_to_bytes(reason))

    async def receive_any_str(self, timeout: typing.Optional[float] = None) -> typing.AnyStr:
        """
        Receives either a :class:`str` or a :class:`bytes` message and returns it.

        Args:
            timeout:
                optional timeout to fail after, if not specified, no timeout is applied.

        Returns:
            the :class:`str` or :class:`bytes` that was returned.

        Raises:
            TypeError:
                if an unexpected message type is received.
        """
        response = await self.receive(timeout)
        if response.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
            return response.data
        else:
            raise TypeError(f"Expected TEXT or BINARY message on websocket but received {response.type}")

    async def receive(self, timeout: typing.Optional[float] = None) -> aiohttp.WSMessage:
        response = await super().receive(timeout)
        if response.type == aiohttp.WSMsgType.CLOSE:
            await self.close()

            try:
                reason = opcodes.GatewayClosure(self.close_code).name
            except ValueError:
                reason = _NO_REASON

            raise WebSocketClosure(self.close_code, reason)

        return response


__all__ = ("WebSocketClosure", "WebSocketClientSession", "WebSocketClientResponse")
