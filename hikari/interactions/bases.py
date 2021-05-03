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
    "ResponseType",
    "InteractionType",
    "PartialInteraction",
]

import typing

import attr

from hikari import snowflakes
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import traits


@typing.final
class InteractionType(int, enums.Enum):
    """The type of an interaction."""

    # PING isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.
    APPLICATION_COMMAND = 2
    """An interaction triggered by a user calling an application command."""


# TODO: is this command specific or not; the docs leave a ton up to the imagination
@typing.final
class ResponseType(int, enums.Enum):
    """The type of an interaction response."""

    # PONG isn't here as it should be handled as internal detail of the REST
    # server rather than as a part of the public interface.

    # Type 2 and 3 aren't included as they were deprecated/removed by Discord.
    SOURCED_RESPONSE = 4
    """An immediate response to an interaction."""

    DEFERRED_SOURCED_RESPONSE = 5
    """Acknowledge an interaction with the intention to edit in a response later.

    The user will see a loading state when this type is used until this
    interaction expires or a response is edited in over REST.
    """


@attr_extensions.with_copy
@attr.s(eq=True, hash=True, init=True, kw_only=True, slots=True, weakref_slot=False)
class PartialInteraction(snowflakes.Unique):
    """The base model for all interaction models."""

    app: traits.RESTAware = attr.ib(repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.ib(eq=True, hash=True, repr=True)
    # <<inherited docstring from Unique>>.

    application_id: snowflakes.Snowflake = attr.ib(eq=False, hash=False, repr=False)
    """ID of the application this interaction belongs to."""

    type: typing.Union[InteractionType, int] = attr.ib(eq=False, hash=False, repr=True)
    """The type of interaction this is."""

    token: str = attr.ib(eq=False, hash=False, repr=False)
    """The interaction's token."""

    version: int = attr.ib(eq=False, hash=False, repr=True)
    """Version of the interaction system this interaction is under."""
