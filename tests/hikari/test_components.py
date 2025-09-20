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
from __future__ import annotations

from hikari import components


class TestActionRowComponent:
    def test_getitem_operator_with_index(self):
        mock_component = object()
        row = components.ActionRowComponent(type=1, id=5855932, components=[object(), mock_component, object()])

        assert row[1] is mock_component

    def test_getitem_operator_with_slice(self):
        mock_component_1 = object()
        mock_component_2 = object()
        row = components.ActionRowComponent(
            type=1, id=5855932, components=[object(), mock_component_1, object(), mock_component_2]
        )

        assert row[1:4:2] == [mock_component_1, mock_component_2]

    def test_iter_operator(self):
        mock_component_1 = object()
        mock_component_2 = object()
        row = components.ActionRowComponent(type=1, id=5855932, components=[mock_component_1, mock_component_2])

        assert list(row) == [mock_component_1, mock_component_2]

    def test_len_operator(self):
        row = components.ActionRowComponent(type=1, id=5855932, components=[object(), object()])

        assert len(row) == 2
