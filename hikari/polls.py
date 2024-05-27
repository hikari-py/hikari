# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2024-present PythonTryHard, MPlatypus
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
"""Polls and poll-related objects."""  # TODO: Improve this docstring

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "PollMedia",
    "PollAnswer",
    "PollResult",
    "PollAnswerCount",
    "PollLayoutType",
    "PartialPoll",
    "PollCreate",
    "PollObject",
)

import typing

import attrs

from hikari.emojis import Emoji
from hikari.internal import attrs_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime


def _ensure_optional_emoji(emoji: typing.Union[str, Emoji, None])  -> typing.Optional[emojis.Emoji]:
    """Ensure the object is a [hikari.emojis.Emoji][]."""
    if emoji is not None:
        return Emoji.parse(emoji) if isinstance(emoji, str) else emoji
    return None


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class PollMedia:
    """Common object backing a poll's questions and answers."""

    text: typing.Optional[str] = attrs.field(default=None, repr=True)
    """The text of the element, or [`None`][] if not present."""

    emoji: typing.Optional[Emoji] = attrs.field(default=None, repr=True)
    """The emoji of the element, or [`None`][] if not present."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class PollAnswer:
    """Represents an answer to a poll."""

    answer_id: int = attrs.field(repr=True)
    """The ID that labels this answer."""  # Is this user-settable?

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

    answer_id: int = attrs.field(repr=True)
    """The ID of the answer."""

    count: int = attrs.field(repr=True)
    """The number of votes for this answer."""

    me_voted: bool = attrs.field(repr=True)
    """Whether the current user voted for this answer."""


class PollLayoutType(int, enums.Enum):
    """Layout of a poll."""

    DEFAULT = 1
    """The default layout of a poll."""


class PartialPoll:
    """Base class for all poll objects."""

    __slots__: typing.Sequence[str] = ("_question", "_answers", "_allow_multiselect", "_layout_type", "_counter")

    def __init__(self, question: str, allow_multiselect: bool, layout_type: typing.Union[int, PollLayoutType]):
        self._question = PollMedia(text=question)  # Only text is supported for question
        self._allow_multiselect = allow_multiselect
        self._layout_type = layout_type

        # Answer is required, but we want users to user add_answer() instead of
        # providing at initialization.
        #
        # Considering that answer ID can be arbitrary, `list`-based approaches
        # like that of hikari.embeds.Embed._fields, while feasible to implement,
        # would decrease long-term maintainability. I'm opting to use a `dict`
        # here to simplify the implementation with some performance trade-off
        # due to hashmap overhead.
        self._answers: typing.MutableMapping[int, PollAnswer] = {}

    @property
    def question(self) -> PollMedia:
        """Returns the question of the poll."""
        return self._question

    @question.setter
    def question(self, value: str) -> None:
        self._question = PollMedia(text=value)

    @property
    def allow_multiselect(self) -> bool:
        """Returns whether the poll allows multiple answers."""
        return self._allow_multiselect

    @allow_multiselect.setter
    def allow_multiselect(self, value: bool) -> None:
        self._allow_multiselect = value

    @property
    def layout_type(self) -> PollLayoutType:
        """Returns the layout type of the poll."""
        return PollLayoutType(self._layout_type)

    @layout_type.setter
    def layout_type(self, value: typing.Union[int, PollLayoutType]) -> None:
        self._layout_type = value

    @property
    def answers(self) -> typing.MutableMapping[int, PollAnswer]:
        """Returns the answers of the poll.

        !!! note
            Use [`hikari.polls.Poll.add_answer`][] to add a new answer,
            [`hikari.polls.Poll.edit_answer`][] to edit an existing answer, or
            [`hikari.polls.Poll.remove_answer`][] to remove a answer.
        """
        return self._answers


class PollCreate(PartialPoll):
    """Used to create a poll."""  # TODO: Improve this docstring

    __slots__: typing.Sequence[str] = ("_duration",)

    def __init__(
        self,
        question: str,
        duration: int,
        allow_multiselect: bool,
        layout_type: typing.Union[int, PollLayoutType] = PollLayoutType.DEFAULT,
    ):

        super().__init__(question=question, allow_multiselect=allow_multiselect, layout_type=layout_type)
        self._duration = duration

    @property
    def duration(self) -> int:
        """Returns the duration of the poll."""
        return self._duration

    @duration.setter
    def duration(self, value: int) -> None:
        self._duration = value

    def add_answer(self, answer_id: int, text: str, emoji: typing.Optional[Emoji]) -> PartialPoll:
        """
        Add an answer to the poll.

        Parameters
        ----------
        answer_id
            The ID of the answer to add.
        text
            The text of the answer to add.
        emoji
            The emoji associated with the answer.

        Returns
        -------
        PartialPoll
            This poll. Allows for call chaining.

        Raises
        ------
        KeyError
            If the answer ID already exists in the poll.
        """
        # Raise an exception when user tries to add an answer with an already
        # existing ID. While this is against the "spirit" of hikari, we want
        # add_answer to only "add" answers, not "edit" them. That job is for
        # edit_answer.g
        if answer_id in self._answers:
            raise KeyError(f"Answer ID {answer_id} already exists in the poll.")

        new_answer = PollAnswer(
            answer_id=answer_id, poll_media=PollMedia(text=text, emoji=_ensure_optional_emoji(emoji))
        )
        self._answers.update({answer_id: new_answer})

        return self

    def edit_answer(self, answer_id: int, text: str, emoji: typing.Optional[typing.Union[str, Emoji]]) -> PartialPoll:
        """
        Edit an answer in the poll.

        Parameters
        ----------
        answer_id
            The ID of the answer to edit.
        text
            The new text of the answer.
        emoji
            The new emoji associated with the answer.

        Returns
        -------
        PartialPoll
            This poll. Allows for call chaining.

        Raises
        ------
        KeyError
            Raised when the answer ID is not found in the poll.
        """
        answer = self._answers.get(answer_id, None)
        if answer is None:
            raise KeyError(f"Answer ID {answer_id} not found in the poll.")

        new_poll_media = PollMedia(text=text, emoji=_ensure_optional_emoji(emoji))
        answer.poll_media = new_poll_media

        return self

    def remove_answer(self, answer_id: int) -> PartialPoll:
        """
        Remove an answer from the poll.

        Parameters
        ----------
        answer_id
            The ID of the answer to remove.

        Returns
        -------
        PartialPoll
            This poll. Allows for call chaining.

        Raises
        ------
        KeyError
            Raised when the answer ID is not found in the poll.
        """
        if answer_id not in self._answers:
            raise KeyError(f"Answer ID {answer_id} not found in the poll.")

        del self._answers[answer_id]

        return self


class PollObject(PartialPoll):
    """Represents an existing poll."""

    __slots__: typing.Sequence[str] = ("_expiry", "_results")

    def __init__(
        self,
        question: str,
        answers: typing.MutableMapping[int, PollAnswer],
        allow_multiselect: bool,
        expiry: datetime.datetime,
        results: typing.Optional[PollResult],
        layout_type: typing.Union[int, PollLayoutType] = PollLayoutType.DEFAULT,
    ):
        super().__init__(question=question, allow_multiselect=allow_multiselect, layout_type=layout_type)
        self._answers = answers
        self._expiry = expiry
        self._results = results

    @property
    def expiry(self) -> datetime.datetime:
        """Returns whether the poll has expired."""
        return self._expiry

    @property
    def results(self) -> typing.Optional[PollResult]:
        """Returns the result of the poll.

        !!! note
            According to Discord, their backend does not always return `results`,
            this is meant to be interpreted as "unknown result" rather than "no
            result". Please refer to the
            [official documentation](https://discord.com/developers/docs/resources/poll#poll-results-object)
            for more information.
        """
        return self._results
