# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Events that are bound to the lifetime of an application.

These are types of hooks that can be invoked on startup or shutdown, which can
be used to initialize other resources, fetch information, and perform checks.
"""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StartingEvent", "StartedEvent", "StoppingEvent", "StoppedEvent"]

# noinspection PyUnresolvedReferences
import typing

import attr

from hikari.events import base_events

if typing.TYPE_CHECKING:
    from hikari.api import event_consumer


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class StartingEvent(base_events.Event):
    """Event that is triggered before the application connects to discord.

    This will only fire once per `app.run`/`app.start`, so is suitable for
    opening database connections and other resources that need to be
    initialized within a coroutine function.

    !!! warning
        The application will not proceed to connect to Discord until all event
        handlers for this event have completed/terminated. This prevents the
        risk of race conditions occurring (e.g. allowing message events
        to try to access a database that has not yet connected fully).

    If you want to do something _after_ the application has initialized, you
    should consider using `StartedEvent` instead.

    See Also
    --------
    `StartedEvent`
    `StoppingEvent`
    `StoppedEvent`
    """

    app: event_consumer.IEventConsumerApp = attr.ib()
    # <<inherited docstring from Event>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class StartedEvent(base_events.Event):
    """Event that is triggered after the application has started.

    This will only fire once per `app.run`/`app.start`, so is suitable for
    opening database connections and other resources that need to be
    initialized within a coroutine function.

    If you want to do something _before_ the application connects, you should
    consider using `StartingEvent` instead.

    See Also
    --------
    `StartingEvent`
    `StoppingEvent`
    `StoppedEvent`
    """

    app: event_consumer.IEventConsumerApp = attr.ib()
    # <<inherited docstring from Event>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class StoppingEvent(base_events.Event):
    """Event that is triggered as soon as the application is requested to close.

    This will fire before the connection is physically disconnected.

    This will only fire once per `app.close`, so is suitable for
    closing database connections and other resources that need to be
    closed within a coroutine function.

    !!! warning
        The application will not proceed to disconnect from Discord until all
        event handlers for this event have completed/terminated. This
        prevents the risk of race conditions occurring from code that relies
        on a connection still being available to complete.

    If you want to do something _after_ the disconnection has occurred, you
    should consider using `StoppedEvent` instead.

    See Also
    --------
    `StartingEvent`
    `StartedEvent`
    `StoppedEvent`
    """

    app: event_consumer.IEventConsumerApp = attr.ib()
    # <<inherited docstring from Event>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class StoppedEvent(base_events.Event):
    """Event that is triggered once the application has disconnected.

    This will only fire once per `app.close`, so is suitable for
    closing database connections and other resources that need to be
    closed within a coroutine function.

    !!! warning
        The application will not proceed to leave the `app.run` call until all
        event handlers for this event have completed/terminated. This
        prevents the risk of race conditions occurring where a script may
        terminate the process before a callback can occur.

    If you want to do something when the application is preparing to shut down,
    but _before_ any connection to discord is closed, you should consider using
    `StoppingEvent` instead.

    See Also
    --------
    `StartingEvent`
    `StartedEvent`
    `StoppingEvent`
    """

    app: event_consumer.IEventConsumerApp = attr.ib()
    # <<inherited docstring from Event>>.
