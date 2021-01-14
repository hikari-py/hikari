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
"""Events that fire when Interactions are modified."""
from __future__ import annotations

__slots__: typing.Sequence[str] = ["InteractionCreateEvent"]

import typing

import attr

from hikari.events import base_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import interactions
    from hikari import traits
    from hikari.api import shard as gateway_shard


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class InteractionCreateEvent(base_events.Event):
    """Event fired when an interaction is created."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: typing.Optional[gateway_shard.GatewayShard] = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """Shard that received this event.

    Returns
    -------
    typing.Optional[hikari.api.shard.GatewayShard]
        The shard that triggered the event. Will be `builtins.None` for events
        triggered by a REST server.
    """

    interaction: interactions.PartialInteraction = attr.ib(eq=True, hash=True, repr=True)
    """Interaction that this event is related to.

    Returns
    -------
    hikari.interactions.PartialInteraction
        Object of the interaction that this event is related to.
    """
