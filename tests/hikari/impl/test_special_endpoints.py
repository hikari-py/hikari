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

from hikari import commands
from hikari import emojis
from hikari import messages
from hikari import snowflakes
from hikari import undefined
from hikari.impl import special_endpoints
from hikari.interactions import base_interactions
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

    def test_set_content_casts_to_str(self):
        mock_thing = mock.Mock(__str__=mock.Mock(return_value="meow nya"))
        builder = special_endpoints.InteractionMessageBuilder(4).set_content(mock_thing)

        assert builder.content == "meow nya"

    def test_components_property(self):
        mock_component = object()
        builder = special_endpoints.InteractionMessageBuilder(4)

        assert builder.components == []

        builder.add_component(mock_component)

        assert builder.components == [mock_component]

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
        mock_component = mock.Mock()
        mock_serialized_embed = object()
        mock_entity_factory.serialize_embed.return_value = (mock_serialized_embed, [])
        builder = (
            special_endpoints.InteractionMessageBuilder(base_interactions.ResponseType.MESSAGE_CREATE)
            .add_embed(mock_embed)
            .add_component(mock_component)
            .set_content("a content")
            .set_flags(2323)
            .set_tts(True)
            .set_mentions_everyone(False)
            .set_user_mentions([123])
            .set_role_mentions([54234])
        )

        result = builder.build(mock_entity_factory)

        mock_entity_factory.serialize_embed.assert_called_once_with(mock_embed)
        mock_component.build.assert_called_once_with()
        assert result == {
            "type": base_interactions.ResponseType.MESSAGE_CREATE,
            "data": {
                "content": "a content",
                "components": [mock_component.build.return_value],
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

    def test_type_property(self):
        builder = special_endpoints.CommandBuilder("OKSKDKSDK", "inmjfdsmjiooikjsa").set_type(2)

        assert builder.type == commands.CommandType.USER

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
            "type": 1,
            "default_permission": False,
            "options": [mock_entity_factory.serialize_command_option.return_value],
            "id": "3412312",
        }

    def test_build_without_optional_data(self):
        builder = special_endpoints.CommandBuilder("we are numberr", "oner")

        result = builder.build(mock.Mock())

        assert result == {"name": "we are numberr", "description": "oner", "type": 1, "options": []}


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


class Test_ButtonBuilder:
    @pytest.fixture()
    def button(self):
        return special_endpoints._ButtonBuilder(
            container=mock.Mock(),
            style=messages.ButtonStyle.DANGER,
            custom_id="sfdasdasd",
            url="hi there",
            emoji=543123,
            emoji_id="56554456",
            emoji_name="hi there",
            label="a lebel",
            is_disabled=True,
        )

    def test_style_property(self, button):
        assert button.style is messages.ButtonStyle.DANGER

    def test_emoji_property(self, button):
        assert button.emoji == 543123

    @pytest.mark.parametrize("emoji", ["unicode", emojis.UnicodeEmoji("unicode")])
    def test_set_emoji_with_unicode_emoji(self, button, emoji):
        result = button.set_emoji(emoji)

        assert result is button
        assert button._emoji == emoji
        assert button._emoji_id is undefined.UNDEFINED
        assert button._emoji_name == "unicode"

    @pytest.mark.parametrize("emoji", [emojis.CustomEmoji(name="ok", id=34123123, is_animated=False), 34123123])
    def test_set_emoji_with_custom_emoji(self, button, emoji):
        result = button.set_emoji(emoji)

        assert result is button
        assert button._emoji == emoji
        assert button._emoji_id == "34123123"
        assert button._emoji_name is undefined.UNDEFINED

    def test_set_emoji_with_undefined(self, button):
        result = button.set_emoji(undefined.UNDEFINED)

        assert result is button
        assert button._emoji_id is undefined.UNDEFINED
        assert button._emoji_name is undefined.UNDEFINED
        assert button._emoji is undefined.UNDEFINED

    def test_set_label(self, button):
        assert button.set_label("hi hi") is button
        assert button.label == "hi hi"

    def test_set_is_disabled(self, button):
        assert button.set_is_disabled(False)
        assert button.is_disabled is False

    def test_build(self):
        result = special_endpoints._ButtonBuilder(
            container=object(),
            style=messages.ButtonStyle.DANGER,
            url=undefined.UNDEFINED,
            emoji_id=undefined.UNDEFINED,
            emoji_name="emoji_name",
            label="no u",
            custom_id="ooga booga",
            is_disabled=True,
        ).build()

        assert result == {
            "type": messages.ComponentType.BUTTON,
            "style": messages.ButtonStyle.DANGER,
            "emoji": {"name": "emoji_name"},
            "label": "no u",
            "custom_id": "ooga booga",
            "disabled": True,
        }

    def test_build_without_optional_fields(self):
        result = special_endpoints._ButtonBuilder(
            container=object(),
            style=messages.ButtonStyle.LINK,
            url="OK",
            emoji_id="123321",
            emoji_name=undefined.UNDEFINED,
            label=undefined.UNDEFINED,
            custom_id=undefined.UNDEFINED,
            is_disabled=False,
        ).build()

        assert result == {
            "type": messages.ComponentType.BUTTON,
            "style": messages.ButtonStyle.LINK,
            "emoji": {"id": "123321"},
            "disabled": False,
            "url": "OK",
        }

    def test_add_to_container(self):
        mock_container = mock.Mock()
        button = special_endpoints._ButtonBuilder(
            container=mock_container,
            style=messages.ButtonStyle.DANGER,
            url=undefined.UNDEFINED,
            emoji_id=undefined.UNDEFINED,
            emoji_name="emoji_name",
            label="no u",
            custom_id="ooga booga",
            is_disabled=True,
        )

        assert button.add_to_container() is mock_container

        mock_container.add_component.assert_called_once_with(button)


class TestLinkButtonBuilder:
    def test_url_property(self):
        button = special_endpoints.LinkButtonBuilder(
            container=object(),
            style=messages.ButtonStyle.DANGER,
            url="hihihihi",
            emoji_id=undefined.UNDEFINED,
            emoji_name="emoji_name",
            label="no u",
            custom_id="ooga booga",
            is_disabled=True,
        )

        assert button.url == "hihihihi"


class TestInteractiveButtonBuilder:
    def test_custom_id_property(self):
        button = special_endpoints.InteractiveButtonBuilder(
            container=object(),
            style=messages.ButtonStyle.DANGER,
            url="hihihihi",
            emoji_id=undefined.UNDEFINED,
            emoji_name="emoji_name",
            label="no u",
            custom_id="ooga booga",
            is_disabled=True,
        )

        assert button.custom_id == "ooga booga"


class Test_SelectOptionBuilder:
    @pytest.fixture()
    def option(self):
        return special_endpoints._SelectOptionBuilder(menu=mock.Mock(), label="ok", value="ok2")

    def test_label_property(self, option):
        assert option.label == "ok"

    def test_value_property(self, option):
        assert option.value == "ok2"

    def test_emoji_property(self, option):
        option._emoji = 123321
        assert option.emoji == 123321

    def test_set_description(self, option):
        assert option.set_description("a desk") is option
        assert option.description == "a desk"

    @pytest.mark.parametrize("emoji", ["unicode", emojis.UnicodeEmoji("unicode")])
    def test_set_emoji_with_unicode_emoji(self, option, emoji):
        result = option.set_emoji(emoji)

        assert result is option
        assert option._emoji == emoji
        assert option._emoji_id is undefined.UNDEFINED
        assert option._emoji_name == "unicode"

    @pytest.mark.parametrize("emoji", [emojis.CustomEmoji(name="ok", id=34123123, is_animated=False), 34123123])
    def test_set_emoji_with_custom_emoji(self, option, emoji):
        result = option.set_emoji(emoji)

        assert result is option
        assert option._emoji == emoji
        assert option._emoji_id == "34123123"
        assert option._emoji_name is undefined.UNDEFINED

    def test_set_emoji_with_undefined(self, option):
        result = option.set_emoji(undefined.UNDEFINED)

        assert result is option
        assert option._emoji_id is undefined.UNDEFINED
        assert option._emoji_name is undefined.UNDEFINED
        assert option._emoji is undefined.UNDEFINED

    def test_set_is_default(self, option):
        assert option.set_is_default(True) is option
        assert option.is_default is True

    def test_add_to_menu(self, option):
        assert option.add_to_menu() is option._menu
        option._menu.add_raw_option.assert_called_once_with(option)

    def test_build_with_custom_emoji(self, option):
        result = (
            special_endpoints._SelectOptionBuilder(label="ok", value="ok2", menu=object())
            .set_is_default(True)
            .set_emoji(123312)
            .set_description("very")
            .build()
        )

        assert result == {
            "label": "ok",
            "value": "ok2",
            "default": True,
            "emoji": {"id": "123312"},
            "description": "very",
        }

    def test_build_with_unicode_emoji(self, option):
        result = (
            special_endpoints._SelectOptionBuilder(label="ok", value="ok2", menu=object())
            .set_is_default(True)
            .set_emoji("hi")
            .set_description("very")
            .build()
        )

        assert result == {
            "label": "ok",
            "value": "ok2",
            "default": True,
            "emoji": {"name": "hi"},
            "description": "very",
        }

    def test_build_partial(self, option):
        result = special_endpoints._SelectOptionBuilder(label="ok", value="ok2", menu=object()).build()

        assert result == {"label": "ok", "value": "ok2", "default": False}


class TestSelectMenuBuilder:
    @pytest.fixture()
    def menu(self):
        return special_endpoints.SelectMenuBuilder(container=mock.Mock(), custom_id="o2o2o2")

    def test_custom_id_property(self, menu):
        assert menu.custom_id == "o2o2o2"

    def test_add_add_option(self, menu):
        option = menu.add_option("ok", "no u")
        option.add_to_menu()
        assert menu.options == [option]

    def test_add_raw_option(self, menu):
        mock_option = object()
        menu.add_raw_option(mock_option)
        assert menu.options == [mock_option]

    def test_set_is_disabled(self, menu):
        assert menu.set_is_disabled(True) is menu
        assert menu.is_disabled is True

    def test_set_placeholder(self, menu):
        assert menu.set_placeholder("place") is menu
        assert menu.placeholder == "place"

    def test_set_min_values(self, menu):
        assert menu.set_min_values(1) is menu
        assert menu.min_values == 1

    def test_set_max_values(self, menu):
        assert menu.set_max_values(25) is menu
        assert menu.max_values == 25

    def test_add_to_container(self, menu):
        assert menu.add_to_container() is menu._container
        menu._container.add_component.assert_called_once_with(menu)

    def test_build(self):
        result = special_endpoints.SelectMenuBuilder(container=object(), custom_id="o2o2o2").build()

        assert result == {
            "type": messages.ComponentType.SELECT_MENU,
            "custom_id": "o2o2o2",
            "options": [],
            "disabled": False,
            "min_values": 0,
            "max_values": 1,
        }

    def test_build_partial(self):
        result = (
            special_endpoints.SelectMenuBuilder(container=object(), custom_id="o2o2o2")
            .set_placeholder("hi")
            .set_min_values(22)
            .set_max_values(53)
            .set_is_disabled(True)
            .add_raw_option(mock.Mock(build=mock.Mock(return_value={"hi": "OK"})))
            .build()
        )

        assert result == {
            "type": messages.ComponentType.SELECT_MENU,
            "custom_id": "o2o2o2",
            "options": [{"hi": "OK"}],
            "placeholder": "hi",
            "min_values": 22,
            "max_values": 53,
            "disabled": True,
        }


class TestActionRowBuilder:
    def test_components_property(self):
        mock_component = object()
        row = special_endpoints.ActionRowBuilder().add_component(mock_component)
        assert row.components == [mock_component]

    def test_add_button_for_interactive(self):
        row = special_endpoints.ActionRowBuilder()
        button = row.add_button(messages.ButtonStyle.DANGER, "go home")

        button.add_to_container()

        assert row.components == [button]

    def test_add_button_for_link(self):
        row = special_endpoints.ActionRowBuilder()
        button = row.add_button(messages.ButtonStyle.LINK, "go home")

        button.add_to_container()

        assert row.components == [button]

    def test_add_select_menu(self):
        row = special_endpoints.ActionRowBuilder()
        menu = row.add_select_menu("hihihi")

        menu.add_to_container()

        assert row.components == [menu]

    def test_build(self):
        mock_component_1 = mock.Mock()
        mock_component_2 = mock.Mock()

        row = special_endpoints.ActionRowBuilder()
        row._components = [mock_component_1, mock_component_2]

        result = row.build()

        assert result == {
            "type": messages.ComponentType.ACTION_ROW,
            "components": [mock_component_1.build.return_value, mock_component_2.build.return_value],
        }
        mock_component_1.build.assert_called_once_with()
        mock_component_2.build.assert_called_once_with()
