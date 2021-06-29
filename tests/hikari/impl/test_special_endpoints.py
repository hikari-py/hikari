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

from hikari import emojis
from hikari import snowflakes
from hikari import undefined
from hikari.impl import special_endpoints
from hikari.interactions import base_interactions
from hikari.interactions import components
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


class TestInteractionDeferredBuilder:
    def test_type_property(self):
        builder = special_endpoints.InteractionDeferredBuilder(5)

        assert builder.type == 5

    def test_set_flags(self):
        builder = special_endpoints.InteractionDeferredBuilder(5).set_flags(32)

        assert builder.flags == 32

    def test_build(self):
        builder = special_endpoints.InteractionDeferredBuilder(base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE)

        assert builder.build(object()) == {"type": base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE}

    def test_build_with_flags(self):
        builder = special_endpoints.InteractionDeferredBuilder(
            base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE
        ).set_flags(64)

        assert builder.build(object()) == {
            "type": base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE,
            "data": {"flags": 64},
        }


class TestInteractionMessageBuilder:
    def test_type_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4)

        assert builder.type == 4

    def test_content_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_content("ayayayaya")

        assert builder.content == "ayayayaya"

    def test_embeds_property(self):
        mock_embed = object()
        builder = special_endpoints.InteractionMessageBuilder(4)

        assert builder.embeds == []

        builder.add_embed(mock_embed)

        assert builder.embeds == [mock_embed]

    def test_flags_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_flags(95995)

        assert builder.flags == 95995

    def test_is_tts_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_tts(False)

        assert builder.is_tts is False

    def test_mentions_everyone_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_mentions_everyone([123, 453])

        assert builder.mentions_everyone == [123, 453]

    def test_role_mentions_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_role_mentions([999])

        assert builder.role_mentions == [999]

    def test_user_mentions_property(self):
        builder = special_endpoints.InteractionMessageBuilder(4).set_user_mentions([33333, 44444])

        assert builder.user_mentions == [33333, 44444]

    def test_build(self):
        mock_entity_factory = mock.Mock()
        mock_embed = object()
        mock_serialized_embed = object()
        mock_entity_factory.serialize_embed.return_value = (mock_serialized_embed, [])
        builder = (
            special_endpoints.InteractionMessageBuilder(base_interactions.ResponseType.MESSAGE_CREATE)
            .add_embed(mock_embed)
            .set_content("a content")
            .set_flags(2323)
            .set_tts(True)
            .set_mentions_everyone(False)
            .set_user_mentions([123])
            .set_role_mentions([54234])
        )

        result = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_embed.assert_called_once_with(mock_embed)
        assert result == {
            "type": base_interactions.ResponseType.MESSAGE_CREATE,
            "data": {
                "content": "a content",
                "embeds": [mock_serialized_embed],
                "flags": 2323,
                "tts": True,
                "allowed_mentions": {"parse": [], "users": ["123"], "roles": ["54234"]},
            },
        }

    def test_build_handles_attachments(self):
        mock_entity_factory = mock.Mock()
        mock_entity_factory.serialize_embed.return_value = (object(), [object()])
        builder = special_endpoints.InteractionMessageBuilder(base_interactions.ResponseType.MESSAGE_CREATE).add_embed(
            object()
        )

        with pytest.raises(
            ValueError, match="Cannot send an embed with attachments in a slash command's initial response"
        ):
            builder.build(mock_entity_factory)


class TestCommandBuilder:
    def test_description_property(self):
        builder = special_endpoints.CommandBuilder("ok", "NO")

        assert builder.description == "NO"

    def test_name_property(self):
        builder = special_endpoints.CommandBuilder("NOOOOO", "OKKKK")

        assert builder.name == "NOOOOO"

    def test_options_property(self):
        builder = special_endpoints.CommandBuilder("OKSKDKSDK", "inmjfdsmjiooikjsa")
        mock_option = object()

        assert builder.options == []

        builder.add_option(mock_option)

        assert builder.options == [mock_option]

    def test_id_property(self):
        builder = special_endpoints.CommandBuilder("OKSKDKSDK", "inmjfdsmjiooikjsa").set_id(3212123)

        assert builder.id == 3212123

    def test_default_permission(self):
        builder = special_endpoints.CommandBuilder("oksksksk", "kfdkodfokfd").set_default_permission(True)

        assert builder.default_permission is True

    def test_build_with_optional_data(self):
        mock_entity_factory = mock.Mock()
        mock_option = object()
        builder = (
            special_endpoints.CommandBuilder("we are number", "one")
            .add_option(mock_option)
            .set_id(3412312)
            .set_default_permission(False)
        )

        result = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_command_option.assert_called_once_with(mock_option)
        assert result == {
            "name": "we are number",
            "description": "one",
            "default_permission": False,
            "options": [mock_entity_factory.serialize_command_option.return_value],
            "id": "3412312",
        }

    def test_build_without_optional_data(self):
        builder = special_endpoints.CommandBuilder("we are numberr", "oner")

        result = builder.build(mock.Mock())

        assert result == {"name": "we are numberr", "description": "oner", "options": []}


class Test_ButtonBuilder:
    def test_build(self):
        result = special_endpoints._ButtonBuilder(
            style=components.ButtonStyle.DANGER,
            url=undefined.UNDEFINED,
            emoji_id=undefined.UNDEFINED,
            emoji_name="emoji_name",
            label="no u",
            custom_id="ooga booga",
            is_disabled=True,
        ).build()

        assert result == {
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.DANGER,
            "emoji": {"name": "emoji_name"},
            "label": "no u",
            "custom_id": "ooga booga",
            "disabled": True,
        }

    def test_build_without_optional_fields(self):
        result = special_endpoints._ButtonBuilder(
            style=components.ButtonStyle.LINK,
            url="OK",
            emoji_id="123321",
            emoji_name=undefined.UNDEFINED,
            label=undefined.UNDEFINED,
            custom_id=undefined.UNDEFINED,
            is_disabled=False,
        ).build()

        assert result == {
            "type": components.ComponentType.BUTTON,
            "style": components.ButtonStyle.LINK,
            "emoji": {"id": "123321"},
            "disabled": False,
            "url": "OK",
        }

    def test_validation_when_url_not_provided_for_link(self):
        with pytest.raises(ValueError, match="url must be specified for a LINK style button"):
            special_endpoints._ButtonBuilder(
                emoji_id=undefined.UNDEFINED,
                emoji_name=undefined.UNDEFINED,
                style=components.ButtonStyle.LINK,
                url=undefined.UNDEFINED,
                label=undefined.UNDEFINED,
                custom_id=undefined.UNDEFINED,
                is_disabled=False,
            )

    def test_validation_when_custom_id_provided_for_link(self):
        with pytest.raises(ValueError, match="custom_id cannot be specified for a LINK style button"):
            special_endpoints._ButtonBuilder(
                emoji_id=undefined.UNDEFINED,
                emoji_name=undefined.UNDEFINED,
                style=components.ButtonStyle.LINK,
                url="hi",
                label=undefined.UNDEFINED,
                custom_id="an ID",
                is_disabled=False,
            )

    def test_validation_when_url_provided_for_not_link(self):
        with pytest.raises(ValueError, match="url cannot be specified for a non-LINK style button"):
            special_endpoints._ButtonBuilder(
                emoji_id=undefined.UNDEFINED,
                emoji_name=undefined.UNDEFINED,
                style=components.ButtonStyle.DANGER,
                url="hi",
                label=undefined.UNDEFINED,
                custom_id="an ID",
                is_disabled=False,
            )

    def test_validation_when_custom_id_not_provided_for_not_link(self):
        with pytest.raises(ValueError, match="custom_id must be specified for a non-LINK style button"):
            special_endpoints._ButtonBuilder(
                emoji_id=undefined.UNDEFINED,
                emoji_name=undefined.UNDEFINED,
                style=components.ButtonStyle.DANGER,
                url=undefined.UNDEFINED,
                label=undefined.UNDEFINED,
                custom_id=undefined.UNDEFINED,
                is_disabled=False,
            )

    def test_validation_when_both_emoji_id_and_emoji_name(self):
        with pytest.raises(ValueError, match="Only one of emoji_id or emoji_name may be provided"):
            special_endpoints._ButtonBuilder(
                emoji_id=123,
                emoji_name="hi",
                style=components.ButtonStyle.DANGER,
                url=undefined.UNDEFINED,
                label=undefined.UNDEFINED,
                custom_id="hi",
                is_disabled=False,
            )


@pytest.mark.parametrize("emoji", ["UNICORN", emojis.UnicodeEmoji("UNICORN")])
def test__build_emoji_with_unicode_emoji(emoji):
    result = special_endpoints._build_emoji(emoji)

    assert result == (undefined.UNDEFINED, "UNICORN")


@pytest.mark.parametrize(
    "emoji", [snowflakes.Snowflake(54123123), 54123123, emojis.CustomEmoji(id=54123123, name=None, is_animated=None)]
)
def test__build_emoji_with_custom_emoji(emoji):
    result = special_endpoints._build_emoji(emoji)

    assert result == ("54123123", undefined.UNDEFINED)


def test__build_emoji_when_undefined():
    assert special_endpoints._build_emoji(undefined.UNDEFINED) == (undefined.UNDEFINED, undefined.UNDEFINED)


class TestActionRowBuilder:
    def test_add_button(self):
        builder = special_endpoints.ActionRowBuilder().add_button(
            style=components.ButtonStyle.DANGER,
            label="ok",
            emoji=emojis.UnicodeEmoji("gat"),
            custom_id="go home",
            disabled=True,
        )

        result = builder._components[0]
        assert isinstance(result, special_endpoints._ButtonBuilder)
        assert result._emoji_id is undefined.UNDEFINED
        assert result._emoji_name == "gat"
        assert result._style is components.ButtonStyle.DANGER
        assert result._label == "ok"
        assert result._custom_id == "go home"
        assert result._is_disabled is True
        assert result._url is undefined.UNDEFINED

    def test_add_button_for_other_fields(self):
        builder = special_endpoints.ActionRowBuilder().add_button(style=components.ButtonStyle.LINK, url="ggg")

        result = builder._components[0]
        assert isinstance(result, special_endpoints._ButtonBuilder)
        assert result._emoji_id is undefined.UNDEFINED
        assert result._emoji_name is undefined.UNDEFINED
        assert result._style is components.ButtonStyle.LINK
        assert result._label is undefined.UNDEFINED
        assert result._custom_id is undefined.UNDEFINED
        assert result._is_disabled is False
        assert result._url == "ggg"

    def test_build(self):
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()

        row = special_endpoints.ActionRowBuilder()
        row._components = [mock_component_1, mock_component_2]

        result = row.build()

        assert result == {
            "type": components.ComponentType.ACTION_ROW,
            "components": [mock_component_1.build.return_value, mock_component_2.build.return_value],
        }
        mock_component_1.build.assert_called_once_with()
        mock_component_2.build.assert_called_once_with()
