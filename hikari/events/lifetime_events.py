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
"""Events that are bound to the lifetime of an application.

These are types of hooks that can be invoked on startup or shutdown, which can
be used to initialize other resources, fetch information, and perform checks.
"""

from __future__ import annotations

__all__: typing.List[str] = ["StartingEvent", "StartedEvent", "StoppingEvent", "StoppedEvent"]

import typing

import attr

from hikari.events import base_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import traits


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class StartingEvent(base_events.Event):
    """Event that is triggered before the application connects to discord.

    This will only fire once per `bot.run` / `bot.start`, so is suitable for
    opening database connections and other resources that need to be
    initialized within a coroutine function.

    !!! warning
        The application will not proceed to connect to Discord until all event
        handlers for this event have completed/terminated. This prevents the
        risk of race conditions occurring (e.g. allowing message events
        to try to access a database that has not yet connected fully).

    If you want to do something _after_ the application has initialized, you
    should consider using `StartedEvent` instead.
    """

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class StartedEvent(base_events.Event):
    """Event that is triggered after the application has started.

    This will only fire once per `bot.run` / `bot.start`, so is suitable for
    opening database connections and other resources that need to be
    initialized within a coroutine function.

    If you want to do something _before_ the application connects, you should
    consider using `StartingEvent` instead.
    """

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class StoppingEvent(base_events.Event):
    """Event that is triggered as soon as the application is requested to close.

    This will fire before the connection is physically disconnected.

    This will only fire once per `bot.close`, so is suitable for
    closing database connections and other resources that need to be
    closed within a coroutine function.

    !!! warning
        The application will not proceed to disconnect from Discord until all
        event handlers for this event have completed/terminated. This
        prevents the risk of race conditions occurring from code that relies
        on a connection still being available to complete.

    If you want to do something _after_ the disconnection has occurred, you
    should consider using `StoppedEvent` instead.
    """

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class StoppedEvent(base_events.Event):
    """Event that is triggered once the application has disconnected.

    This will only fire once per `bot.close`, so is suitable for
    closing database connections and other resources that need to be
    closed within a coroutine function.

    !!! warning
        The application will not proceed to leave the `bot.run` call until all
        event handlers for this event have completed/terminated. This
        prevents the risk of race conditions occurring where a script may
        terminate the process before a callback can occur.

    If you want to do something when the application is preparing to shut down,
    but _before_ any connection to discord is closed, you should consider using
    `StoppingEvent` instead.
    """

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.
