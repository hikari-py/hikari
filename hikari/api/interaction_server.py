# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = ("ListenerT", "Response", "InteractionServer")

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari import files as files_
    from hikari.api import special_endpoints
    from hikari.interactions import base_interactions
    from hikari.interactions import command_interactions
    from hikari.interactions import component_interactions
    from hikari.interactions import modal_interactions

    _InteractionT_co = typing.TypeVar("_InteractionT_co", bound=base_interactions.PartialInteraction, covariant=True)
    _ResponseT_co = typing.TypeVar("_ResponseT_co", bound=special_endpoints.InteractionResponseBuilder, covariant=True)
    _MessageResponseBuilderT = typing.Union[
        special_endpoints.InteractionDeferredBuilder, special_endpoints.InteractionMessageBuilder
    ]
    _ModalOrMessageResponseBuilder = typing.Union[_MessageResponseBuilderT, special_endpoints.InteractionModalBuilder]


ListenerT = typing.Union[
    typing.Callable[["_InteractionT_co"], typing.Awaitable["_ResponseT_co"]],
    typing.Callable[["_InteractionT_co"], typing.AsyncGenerator["_ResponseT_co", None]],
]
"""Type hint of a Interaction server's listener callback.

This should be an async callback which takes in one positional argument which
subclasses [`hikari.interactions.base_interactions.PartialInteraction`][] and may return an
instance of the relevant [`hikari.api.special_endpoints.InteractionResponseBuilder`][]
subclass for the provided interaction type which will instruct the server on how
to respond.

!!! note
    For the standard implementations of
    [`hikari.api.special_endpoints.InteractionResponseBuilder`][] see
    [`hikari.impl.special_endpoints`][].
"""


class Response(typing.Protocol):
    """Protocol of the data returned by [`hikari.api.interaction_server.InteractionServer.on_interaction`][].

    This is used to instruct lower-level REST server logic on how it should
    respond.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def content_type(self) -> typing.Optional[str]:
        """Content type of the response's payload, if applicable."""
        raise NotImplementedError

    @property
    def charset(self) -> typing.Optional[str]:
        """Charset of the response's payload, if applicable."""
        raise NotImplementedError

    @property
    def files(self) -> typing.Sequence[files_.Resource[files_.AsyncReader]]:
        """Up to 10 files that should be included alongside a JSON response."""
        raise NotImplementedError

    @property
    def headers(self) -> typing.Optional[typing.MutableMapping[str, str]]:
        """Headers that should be added to the response if applicable."""
        raise NotImplementedError

    @property
    def payload(self) -> typing.Optional[bytes]:
        """Payload to provide in the response."""
        raise NotImplementedError

    @property
    def status_code(self) -> int:
        """Status code that should be used to respond.

        For more information see <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status>.
        """
        raise NotImplementedError


class InteractionServer(abc.ABC):
    """Interface for an implementation of an interactions compatible REST server."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def on_interaction(self, body: bytes, signature: bytes, timestamp: bytes) -> Response:
        """Handle an interaction received from Discord as a REST server.

        Parameters
        ----------
        body : bytes
            The interaction payload.
        signature : bytes
            Value of the `"X-Signature-Ed25519"` header used to verify the body.
        timestamp : bytes
            Value of the `"X-Signature-Timestamp"` header used to verify the body.

        Returns
        -------
        Response
            Instructions on how the REST server calling this should respond to
            the interaction request.
        """

    @typing.overload
    @abc.abstractmethod
    def get_listener(
        self, interaction_type: typing.Type[command_interactions.CommandInteraction], /
    ) -> typing.Optional[ListenerT[command_interactions.CommandInteraction, _ModalOrMessageResponseBuilder]]: ...

    @typing.overload
    @abc.abstractmethod
    def get_listener(
        self, interaction_type: typing.Type[component_interactions.ComponentInteraction], /
    ) -> typing.Optional[ListenerT[component_interactions.ComponentInteraction, _ModalOrMessageResponseBuilder]]: ...

    @typing.overload
    @abc.abstractmethod
    def get_listener(
        self, interaction_type: typing.Type[command_interactions.AutocompleteInteraction], /
    ) -> typing.Optional[
        ListenerT[command_interactions.AutocompleteInteraction, special_endpoints.InteractionAutocompleteBuilder]
    ]: ...

    @typing.overload
    @abc.abstractmethod
    def get_listener(
        self, interaction_type: typing.Type[modal_interactions.ModalInteraction], /
    ) -> typing.Optional[ListenerT[modal_interactions.ModalInteraction, _MessageResponseBuilderT]]: ...

    @typing.overload
    @abc.abstractmethod
    def get_listener(
        self, interaction_type: typing.Type[_InteractionT_co], /
    ) -> typing.Optional[ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]]: ...

    @abc.abstractmethod
    def get_listener(
        self, interaction_type: typing.Type[_InteractionT_co], /
    ) -> typing.Optional[ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]]:
        """Get the listener registered for an interaction.

        Parameters
        ----------
        interaction_type : typing.Type[hikari.interactions.base_interactions.PartialInteraction]
            Type of the interaction to get the registered listener for.

        Returns
        -------
        typing.Optional[ListenersT[hikari.interactions.base_interactions.PartialInteraction, hikari.api.special_endpoints.InteractionResponseBuilder]
            The callback registered for the provided interaction type if found,
            else [`None`][].
        """  # noqa: E501 - Line too long

    @typing.overload
    @abc.abstractmethod
    def set_listener(
        self,
        interaction_type: typing.Type[command_interactions.CommandInteraction],
        listener: typing.Optional[ListenerT[command_interactions.CommandInteraction, _ModalOrMessageResponseBuilder]],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    @typing.overload
    @abc.abstractmethod
    def set_listener(
        self,
        interaction_type: typing.Type[component_interactions.ComponentInteraction],
        listener: typing.Optional[
            ListenerT[component_interactions.ComponentInteraction, _ModalOrMessageResponseBuilder]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    @typing.overload
    @abc.abstractmethod
    def set_listener(
        self,
        interaction_type: typing.Type[command_interactions.AutocompleteInteraction],
        listener: typing.Optional[
            ListenerT[command_interactions.AutocompleteInteraction, special_endpoints.InteractionAutocompleteBuilder]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    @typing.overload
    @abc.abstractmethod
    def set_listener(
        self,
        interaction_type: typing.Type[modal_interactions.ModalInteraction],
        listener: typing.Optional[ListenerT[modal_interactions.ModalInteraction, _MessageResponseBuilderT]],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    @abc.abstractmethod
    def set_listener(
        self,
        interaction_type: typing.Type[_InteractionT_co],
        listener: typing.Optional[ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]],
        /,
        *,
        replace: bool = False,
    ) -> None:
        """Set the listener callback for this interaction server.

        Parameters
        ----------
        interaction_type : typing.Type[hikari.interactions.base_interactions.PartialInteraction]
            The type of interaction this listener should be registered for.
        listener : typing.Optional[ListenerT[hikari.interactions.base_interactions.PartialInteraction, hikari.api.special_endpoints.InteractionResponseBuilder]]
            The asynchronous listener callback to set or [`None`][] to unset the previous listener.

            An asynchronous listener can be either a normal coroutine or an
            async generator which should yield exactly once. This allows
            sending an initial response to the request, while still
            later executing further logic.

        Other Parameters
        ----------------
        replace : bool
            Whether this call should replace the previously set listener or not.

        Raises
        ------
        TypeError
            If `replace` is [`False`][] when a listener is already set.
        """  # noqa: E501 - Line too long
