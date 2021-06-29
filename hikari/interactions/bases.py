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
"""Base classes and enums inherited and used throughout the interactions flow."""
from __future__ import annotations

__all__: typing.List[str] = [
    "DEFERRED_RESPONSE_TYPES",
    "DeferredResponseTypesT",
    "InteractionMember",
    "InteractionType",
    "MESSAGE_RESPONSE_TYPES",
    "MessageResponseTypesT",
    "PartialInteraction",
    "ResponseType",
]

import typing

import attr

from hikari import guilds
from hikari import snowflakes
from hikari import webhooks
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import permissions as permissions_
    from hikari import traits


@typing.final
class InteractionType(int, enums.Enum):
    """The type of an interaction."""

    # PING isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.
    APPLICATION_COMMAND = 2
    """An interaction triggered by a user calling an application command."""


@typing.final
class ResponseType(int, enums.Enum):
    """The type of an interaction response."""

    # PONG isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.

    # Type 2 and 3 aren't included as they were deprecated/removed by Discord.
    MESSAGE_CREATE = 4
    """An immediate message response to an interaction."""

    DEFERRED_MESSAGE_CREATE = 5
    """Acknowledge an interaction with the intention to edit in a message response later.

    The user will see a loading state when this type is used until this
    interaction expires or a message response is edited in over REST.
    """


MESSAGE_RESPONSE_TYPES: typing.Final[typing.AbstractSet[MessageResponseTypesT]] = frozenset(
    [ResponseType.MESSAGE_CREATE]
)
"""Set of the response types which are valid for message responses.

This includes the following:

* `ResponseType.MESSAGE_CREATE`
"""

MessageResponseTypesT = typing.Union[typing.Literal[ResponseType.MESSAGE_CREATE], typing.Literal[4]]
"""Type-hint of the response types which are valid for message responses.

The following are valid for this:

* `ResponseType.MESSAGE_CREATE`/`4`
"""

DEFERRED_RESPONSE_TYPES: typing.Final[typing.AbstractSet[DeferredResponseTypesT]] = frozenset(
    [ResponseType.DEFERRED_MESSAGE_CREATE]
)
"""Set of the response types which are valid for deferred messages responses.

This includes the following:

* `ResponseType.DEFERRED_MESSAGE_CREATE`
"""

DeferredResponseTypesT = typing.Union[typing.Literal[ResponseType.DEFERRED_MESSAGE_CREATE], typing.Literal[5]]
"""Type-hint of the response types which are valid for deferred messages responses.

The following are valid for this:

* `ResponseType.DEFERRED_MESSAGE_CREATE`/`5`
"""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialInteraction(snowflakes.Unique, webhooks.ExecutableWebhook):
    """The base model for all interaction models."""

    app: traits.RESTAware = attr.field(repr=False, eq=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attr.field(eq=False, repr=False)
    """ID of the application this interaction belongs to."""

    type: typing.Union[InteractionType, int] = attr.field(eq=False, repr=True)
    """The type of interaction this is."""

    token: str = attr.field(eq=False, repr=False)
    """The interaction's token."""

    version: int = attr.field(eq=False, repr=True)
    """Version of the interaction system this interaction is under."""

    @property
    def webhook_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ExecutableWebhook>>.
        return self.application_id


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class InteractionMember(guilds.Member):
    """Model of the member who triggered an interaction.

    Unlike `hikari.guilds.Member`, this object comes with an extra
    `InteractionMember.permissions` field.
    """

    permissions: permissions_.Permissions = attr.field(eq=False, hash=False, repr=False)
    """Permissions the member has in the current channel."""
