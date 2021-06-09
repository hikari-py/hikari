# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Provides an interface for Interaction REST server API implementations to follow."""
from __future__ import annotations

__all__: typing.Sequence[str] = ["ListenerT", "Response", "InteractionServer"]

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari.api import special_endpoints
    from hikari.interactions import bases as interaction_bases

    InteractionT = typing.TypeVar("InteractionT", bound=interaction_bases.PartialInteraction, covariant=True)
    ResponseT = typing.TypeVar("ResponseT", bound=special_endpoints.BaseInteractionResponseBuilder, covariant=True)


ListenerT = typing.Callable[["InteractionT"], typing.Awaitable["ResponseT"]]
"""Type hint of a Interaction server's listener callback.

This should be an async callback which takes in one positional argument which
subclases `hikari.interactions.bases.PartialInteraction` and may return an
instance of the relevant `hikari.api.special_endpoints.BaseInteractionResponseBuilder`
subclass for the provided interaction type which will instruct the server on how
to respond.

!!! note
    For the standard implementations of
    `hikari.api.special_endpoints.BaseInteractionResponseBuilder` see
    `hikari.impl.special_endpoints`.
"""


class Response(typing.Protocol):
    """Protocol of the data returned by `InteractionServer.on_interaction`.

    This is used to instruct lower-level REST server logic on how it should
    respond.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def headers(self) -> typing.Optional[typing.Mapping[str, str]]:
        """Headers that should be added to the response if applicable.

        Returns
        -------
        typing.Optional[typing.Mapping[builtins.str, builtins.str]]
            A mapping of string header names to string header values that should
            be included in the response if applicable else `builtins.None`.
        """
        raise NotImplementedError

    @property
    def payload(self) -> typing.Optional[bytes]:
        """Payload to provide in the response.

        !!! note
            If this is not `builtins.None` then an appropriate `"Content-Type"`
            header should be declared in `Response.headers`

        Returns
        -------
        typing.Optional[builtins.bytes]
            The bytes payload to respond with if applicable else `builtins.None`.
        """
        raise NotImplementedError

    @property
    def status_code(self) -> int:
        """Status code that should be used to respond.

        Returns
        -------
        builtins.int
            The response code to use for the response. This should be a valid
            HTTP status code, for more information see
            https://developer.mozilla.org/en-US/docs/Web/HTTP/Status.
        """
        raise NotImplementedError


class InteractionServer(abc.ABC):
    """Interface for an implementation of a Interactions compatible REST server."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def on_interaction(self, body: bytes, signature: bytes, timestamp: bytes) -> Response:
        """Handle an interaction received from Discord as a REST server.

        Parameters
        ----------
        body : builtins.bytes
            The interaction payload.
        signature : builtins.bytes
            Value of the `"X-Signature-Ed25519"` header used to verify the body.
        timestamp : builtins.bytes
            Value of the `"X-Signature-Timestamp"` header used to verify the body.

        Returns
        -------
        Response
            Instructions on how the REST server calling this should respond to
            the interaction request.
        """

    # @typing.overload
    # def get_listener(
    #     self, interaction_type: typing.Type[commands.CommandInteraction], /
    # ) -> typing.Optional[ListenerT[commands.CommandInteraction, special_endpoints.InteractionResponseBuilder]]:
    #     raise NotImplementedError

    @abc.abstractmethod
    def get_listener(
        self, interaction_type: typing.Type[interaction_bases.PartialInteraction], /
    ) -> typing.Optional[
        ListenerT[interaction_bases.PartialInteraction, special_endpoints.BaseInteractionResponseBuilder]
    ]:
        raise NotImplementedError

    # @typing.overload
    # def set_listener(
    #     self,
    #     interaction_type: typing.Type[commands.CommandInteraction],
    #     listener: typing.Optional[
    #         MainListenerT[commands.CommandInteraction, special_endpoints.InteractionResponseBuilder]
    #     ],
    #     /,
    #     *,
    #     replace: bool = False,
    # ) -> None:
    #     raise NotImplementedError

    @abc.abstractmethod
    def set_listener(
        self,
        interaction_type: typing.Type[InteractionT],
        listener: typing.Optional[
            ListenerT[interaction_bases.PartialInteraction, special_endpoints.BaseInteractionResponseBuilder]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None:
        """Set the listener callback for this interaction server.

        Parameters
        ----------
        interaction_type : typing.Type[InteractionT]
            The type of interaction this listener should be registered for.
        listener : typing.Optional[MainListenerT[InteractionT]]
            The asynchronous listener callback to set or `builtins.None` to
            unset the previous listener.

        Other Parameters
        ----------------
        replace : builtins.bool
            Whether this call should replace the previously set listener or not.
            This call will raise a `builtins.ValueError` if set to `builtins.False`
            when a listener is already set.

        Raises
        ------
        builtins.TypeError
            If `replace` is `builtins.False` when a listener is already set.
        """
