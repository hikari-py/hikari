# -*- coding: utf-8 -*-
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
import mock
import pytest

from hikari import snowflakes
from hikari.interactions import bases
from hikari.interactions import components


@pytest.fixture()
def mock_app():
    return mock.Mock()


class TestActionRowComponent:
    def test_getitem_operator_with_index(self):
        mock_component = object()
        row = components.ActionRowComponent(type=1, components=[object(), mock_component, object()])

        assert row[1] is mock_component

    def test_getitem_operator_with_slice(self):
        mock_component_1 = object()
        mock_component_2 = object()
        row = components.ActionRowComponent(type=1, components=[object(), mock_component_1, object(), mock_component_2])

        assert row[1:4:2] == [mock_component_1, mock_component_2]

    def test_iter_operator(self):
        mock_component_1 = object()
        mock_component_2 = object()
        row = components.ActionRowComponent(type=1, components=[mock_component_1, mock_component_2])

        assert list(row) == [mock_component_1, mock_component_2]

    def test_len_operator(self):
        row = components.ActionRowComponent(type=1, components=[object(), object()])

        assert len(row) == 2


class TestComponentInteraction:
    @pytest.fixture()
    def mock_component_interaction(self, mock_app):
        return components.ComponentInteraction(
            app=mock_app,
            id=snowflakes.Snowflake(2312312),
            type=bases.InteractionType.APPLICATION_COMMAND,
            channel_id=snowflakes.Snowflake(3123123),
            guild_id=snowflakes.Snowflake(5412231),
            member=object(),
            user=object(),
            token="httptptptptptptptp",
            version=1,
            application_id=snowflakes.Snowflake(43123),
            component_type=2,
            custom_id="OKOKOK",
            message=object(),
            message_id=123321,
            message_flags=3234123,
        )

    def test_build_response(self, mock_component_interaction, mock_app):
        response = mock_component_interaction.build_response(4)

        assert response is mock_app.rest.interaction_message_builder.return_value
        mock_app.rest.interaction_message_builder.assert_called_once_with(4)

    def test_build_response_with_invalid_type(self, mock_component_interaction):
        with pytest.raises(ValueError, match="Invalid type passed for an immediate response"):
            mock_component_interaction.build_response(999)

    def test_build_deferred_response(self, mock_component_interaction, mock_app):
        response = mock_component_interaction.build_deferred_response(5)

        assert response is mock_app.rest.interaction_deferred_builder.return_value
        mock_app.rest.interaction_deferred_builder.assert_called_once_with(5)

    def test_build_deferred_response_with_invalid_type(self, mock_component_interaction):
        with pytest.raises(ValueError, match="Invalid type passed for a deferred response"):
            mock_component_interaction.build_deferred_response(33333)
