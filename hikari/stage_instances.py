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
"""Application and entities that are used to describe Stage instances on Discord."""
from __future__ import annotations

__all__: typing.List[str] = [
    "StagePrivacyLevel",
    "StageInstance",
]

import typing

import attr

from hikari import snowflakes
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import traits


@typing.final
class StagePrivacyLevel(int, enums.Enum):
    """The privacy level of a Stage instance."""

    PUBLIC = 1
    """The Stage instance is visible publicly."""

    GUILD = 2
    """The Stage instance is only visible to the guild members"""


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class StageInstance:
    """Represents a Stage instance."""

    id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the Stage instance."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    channel_id: snowflakes.Snowflake = attr.field(hash=True, repr=False)
    """The channel ID of the Stage instance."""

    guild_id: snowflakes.Snowflake = attr.field(hash=True, repr=False)
    """The guild ID of the Stage instance."""

    topic: str = attr.field(eq=False, hash=False, repr=False)
    """The topic of the Stage instance."""

    privacy_level: typing.Union[StagePrivacyLevel, int] = attr.field(eq=False, hash=False, repr=False)
    """The privacy level of the Stage instance."""

    discoverable_disabled: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether or not Stage discovery is disabled."""
