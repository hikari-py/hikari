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

from hikari import interactions
from hikari.impl import special_endpoints
from tests.hikari import hikari_test_helpers


class TestTypingIndicator:
    @pytest.fixture()
    def typing_indicator(self):
        return hikari_test_helpers.mock_class_namespace(special_endpoints.TypingIndicator, init_=False)

    def test___enter__(self, typing_indicator):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            typing_indicator().__enter__()

    def test___exit__(self, typing_indicator):
        try:
            typing_indicator().__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)


class TestCommandResponseBuilder:
    def test_type_property(self):
        builder = special_endpoints.CommandResponseBuilder(1)

        assert builder.type == 1

    def test_add_embed(self):
        mock_embed = object()
        builder = special_endpoints.CommandResponseBuilder(1)

        assert builder.embeds == []

        builder.add_embed(mock_embed)

        assert builder.embeds == [mock_embed]

    def test_build_without_data(self):
        builder = special_endpoints.CommandResponseBuilder(interactions.ResponseType.DEFERRED_SOURCED_RESPONSE)

        assert builder.build(object()) == {"type": interactions.ResponseType.DEFERRED_SOURCED_RESPONSE, "data": {}}

    def test_build_without_data_for_message_response_type(self):
        builder = special_endpoints.CommandResponseBuilder(interactions.ResponseType.SOURCED_RESPONSE)

        with pytest.raises(ValueError, match="Cannot build an empty response for SOURCED_RESPONSE responses."):
            builder.build(object())

    def test_build_with_data(self):
        mock_entity_factory = mock.Mock()
        builder = special_endpoints.CommandResponseBuilder(interactions.ResponseType.SOURCED_RESPONSE)
        mock_embed = object()
        builder.add_embed(mock_embed)
        builder.content = "a content"
        builder.flags = 2323
        builder.is_tts = True
        builder.mentions_everyone = False
        builder.user_mentions = [123]
        builder.role_mentions = [54234]

        result = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_embed.assert_called_once_with(mock_embed)
        assert result == {
            "type": interactions.ResponseType.SOURCED_RESPONSE,
            "data": {
                "content": "a content",
                "embeds": [mock_entity_factory.serialize_embed.return_value],
                "flags": 2323,
                "tts": True,
                "allowed_mentions": {"parse": [], "users": ["123"], "roles": ["54234"]},
            },
        }

    def test_build_with_data_for_deferred_response_type(self):
        builder = special_endpoints.CommandResponseBuilder(interactions.ResponseType.DEFERRED_SOURCED_RESPONSE)
        builder.add_embed(object())

        with pytest.raises(ValueError, match="Cannot include data for DEFERRED_SOURCED_RESPONSE responses."):
            builder.build(mock.Mock())


class TestCommandBuilder:
    def test_description_property(self):
        builder = special_endpoints.CommandBuilder("ok", "NO")

        assert builder.description == "NO"

    def test_name_property(self):
        builder = special_endpoints.CommandBuilder("NOOOOO", "OKKKK")

        assert builder.name == "NOOOOO"

    def test_add_option(self):
        builder = special_endpoints.CommandBuilder("OKSKDKSDK", "inmjfdsmjiooikjsa")
        mock_option = object()

        assert builder.options == []

        builder.add_option(mock_option)

        assert builder.options == [mock_option]

    def test_build_with_optional_data(self):
        mock_entity_factory = mock.Mock()
        mock_option = object()
        builder = special_endpoints.CommandBuilder("we are number", "one").add_option(mock_option)
        builder.id = 3412312

        result = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_command_option.assert_called_once_with(mock_option)
        assert result == {
            "name": "we are number",
            "description": "one",
            "options": [mock_entity_factory.serialize_command_option.return_value],
            "id": "3412312",
        }

    def test_build_without_optional_data(self):
        builder = special_endpoints.CommandBuilder("we are numberr", "oner")

        result = builder.build(object())

        assert result == {"name": "we are numberr", "description": "oner", "options": []}
