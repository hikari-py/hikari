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
"""Interface providing functionality to dispatch an event object."""
from __future__ import annotations

__all__ = ["IEventDispatcher"]

import abc
import typing

from hikari import component
from hikari.utilities import unset

if typing.TYPE_CHECKING:
    from hikari.events import base
    from hikari.utilities import aio

    _EventT = typing.TypeVar("_EventT", bound=base.HikariEvent, covariant=True)
    _PredicateT = typing.Callable[[_EventT], typing.Union[bool, typing.Coroutine[None, typing.Any, bool]]]


class IEventDispatcher(component.IComponent, abc.ABC):
    """Provides the interface for components wishing to implement dispatching.

    This is a consumer of a `hikari.events.bases.HikariEvent` object, and is
    expected to invoke one or more corresponding event listeners where
    appropriate.
    """

    __slots__ = ()

    @abc.abstractmethod
    def dispatch(self, event: base.HikariEvent) -> aio.Future[typing.Any]:
        """Dispatch an event.

        Parameters
        ----------
        event : hikari.events.base.HikariEvent
            The event to dispatch.

        Returns
        -------
        asyncio.Future
            A future that can be optionally awaited. If awaited, the future
            will complete once all corresponding event listeners have been
            invoked. If not awaited, this will schedule the dispatch of the
            events in the background for later.
        """

    @abc.abstractmethod
    def subscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> None:
        """Subscribe a given callback to a given event type.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
            The event type to listen for. This will also listen for any
            subclasses of the given type.
        callback :
            Either a function or a coroutine function to invoke. This should
            consume an instance of the given event, or an instance of a valid
            subclass if one exists. Any result is discarded.
        """

    @abc.abstractmethod
    def unsubscribe(
        self,
        event_type: typing.Type[_EventT],
        callback: typing.Callable[[_EventT], typing.Union[typing.Coroutine[None, typing.Any, None], None]],
    ) -> None:
        """Unsubscribe a given callback from a given event type, if present.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base.HikariEvent]
            The event type to unsubscribe from. This must be the same exact
            type as was originally subscribed with to be removed correctly.
        callback :
            The callback to unsubscribe.
        """

    @abc.abstractmethod
    def listen(self, event_type: typing.Union[unset.Unset, typing.Type[_EventT]]) -> None:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        event_type : hikari.utilities.unset.Unset OR typing.Type[hikari.events.bases.HikariEvent]
            The event type to subscribe to. The implementation may allow this
            to be unset. If this is the case, the event type will be inferred
            instead from the type hints on the function signature.

        Returns
        -------
        typing.Callable
            A decorator for a function or coroutine function that passes it
            to `subscribe` before returning the function reference.
        """

    @abc.abstractmethod
    async def wait_for(
        self, event_type: typing.Type[_EventT], predicate: _PredicateT, timeout: typing.Union[float, int, None],
    ) -> _EventT:
        """Wait for a given event to occur once, then return the event.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.bases.HikariEvent]
            The event type to listen for. This will listen for subclasses of
            this type additionally.
        predicate :
            A function or coroutine taking the event as the single parameter.
            This should return `True` if the event is one you want to return,
            or `False` if the event should not be returned.
        timeout : float OR int OR None
            The amount of time to wait before raising an `asyncio.TimeoutError`
            and giving up instead. This is measured in seconds. If `None`, then
            no timeout will be waited for (no timeout can result in "leaking" of
            coroutines that never complete if called in an uncontrolled way,
            so is not recommended).

        Returns
        -------
        hikari.events.bases.HikariEvent
            The event that was provided.

        Raises
        ------
        asyncio.TimeoutError
            If the timeout is not `None` and is reached before an event is
            received that the predicate returns `True` for.
        """
