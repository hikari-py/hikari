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
"""Entities that are used to describe polls on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("Poll", "PollAnswer", "PollAnswerCount", "PollLayoutType", "PollMedia", "PollResult")

import typing

import attrs

from hikari.internal import attrs_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime

    from hikari import emojis


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class PollMedia:
    """Common object backing a poll's questions and answers."""

    text: str | None = attrs.field(default=None, repr=True)
    """The text of the element, or [`None`][] if not present."""

    emoji: emojis.Emoji | None = attrs.field(default=None, repr=True)
    """The emoji of the element, or [`None`][] if not present."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class PollAnswer:
    """Represents an answer to a poll."""

    answer_id: int = attrs.field(repr=True)
    """The ID that labels this answer."""

    poll_media: PollMedia = attrs.field(repr=True)
    """The [media][hikari.polls.PollMedia] associated with this answer."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class PollResult:
    """Represents a poll result."""

    is_finalized: bool = attrs.field(repr=True)
    """Whether the poll is finalized and the votes are precisely counted."""

    answer_counts: typing.Sequence[PollAnswerCount] = attrs.field(repr=True)
    """The counts for each answer."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class PollAnswerCount:
    """Represents the count of a poll answer."""

    id: int = attrs.field(repr=True)
    """The ID of the answer."""

    count: int = attrs.field(repr=True)
    """The number of votes for this answer."""

    me_voted: bool = attrs.field(repr=True)
    """Whether the current user voted for this answer."""


class PollLayoutType(int, enums.Enum):
    """Layout of a poll."""

    DEFAULT = 1
    """The default layout of a poll."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, repr=True, weakref_slot=False)
class Poll:
    """Represents an existing poll."""

    question: PollMedia = attrs.field(repr=True)
    """The question of the poll."""

    answers: typing.Sequence[PollAnswer] = attrs.field(repr=True)
    """The answers attached to the poll."""

    expiry: datetime.datetime | None = attrs.field(repr=True)
    """The expiry time for the poll."""

    allow_multiselect: bool = attrs.field(repr=True)
    """Whether a user can select multiple answers."""

    layout_type: PollLayoutType = attrs.field(repr=True)
    """The type of layout the poll uses."""

    results: PollResult | None = attrs.field(repr=True)
    """The results of the poll."""
