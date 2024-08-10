# -*- coding: utf-8 -*-
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
# SOFTWARE.\

from hikari import polls


class TestPollBuilder:
    def test_add_answer(self):
        poll = polls.PollBuilder("question", 1, False)

        poll.add_answer("beanos", None)

        assert len(list(poll.answers)) == 1

        assert list(poll.answers)[0] == polls.PollAnswer(
            answer_id=-1, poll_media=polls.PollMedia(text="beanos", emoji=None)
        )

    def test_edit_answer(self):
        poll = polls.PollBuilder("question", 1, False)

        poll.add_answer("beanos", None)

        assert len(list(poll.answers)) == 1

        assert list(poll.answers)[0] == polls.PollAnswer(
            answer_id=-1, poll_media=polls.PollMedia(text="beanos", emoji=None)
        )

        poll.edit_answer(0, emoji="🫘")

        assert list(poll.answers)[0] == polls.PollAnswer(
            answer_id=-1, poll_media=polls.PollMedia(text="beanos", emoji="🫘")
        )

    def test_remove_answer(self):
        poll = polls.PollBuilder("question", 1, False)

        poll.add_answer("beanos", None)

        assert len(list(poll.answers)) == 1

        assert list(poll.answers)[0] == polls.PollAnswer(
            answer_id=-1, poll_media=polls.PollMedia(text="beanos", emoji=None)
        )

        poll.remove_answer(0)

        assert len(list(poll.answers)) == 0
