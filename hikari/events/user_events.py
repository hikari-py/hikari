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
"""Events fired when the account user is updated."""
from __future__ import annotations

__all__: typing.List[str] = ["OwnUserUpdateEvent"]

import typing

import attr

from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import traits
    from hikari import users
    from hikari.api import shard as gateway_shard


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class OwnUserUpdateEvent(shard_events.ShardEvent):
    """Event fired when the account user is updated."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    old_user: typing.Optional[users.OwnUser] = attr.field()
    """The old application user.

    This will be `builtins.None` if the user missing from the cache.
    """

    user: users.OwnUser = attr.field()
    """This application user.

    Returns
    -------
    hikari.users.OwnUser
        This application user.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.user.app
