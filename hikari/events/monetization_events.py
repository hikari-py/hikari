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
"""Events fired for monetization related changes."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "EntitlementEvent",
    "EntitlementCreateEvent",
    "EntitlementUpdateEvent",
    "EntitlementDeleteEvent",
)

import typing

import attrs

from hikari.events import shard_events
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import monetization
    from hikari import traits
    from hikari.api import shard as gateway_shard


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class EntitlementEvent(shard_events.ShardEvent):
    """Base class related to entitlement change events."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    entitlement: monetization.Entitlement = attrs.field()
    """The entitlement that changed."""


class EntitlementCreateEvent(EntitlementEvent):
    """Event fired when an entitlement is created."""

    __slots__: typing.Sequence[str] = ()


class EntitlementUpdateEvent(EntitlementEvent):
    """Event fired when an entitlement is updated."""

    __slots__: typing.Sequence[str] = ()


class EntitlementDeleteEvent(EntitlementEvent):
    """Event fired when an entitlement is deleted.

    Entitlements are not deleted when they expire, so this event is only
    fired when a refund is issued by Discord or Discord removes the
    entitlement from a user via internal tooling.
    """

    __slots__: typing.Sequence[str] = ()
