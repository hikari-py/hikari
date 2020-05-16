#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import mock
import pytest

from hikari.models import users, emojis, bases, files
from hikari.components import application
from hikari.internal import urls
from tests.hikari import _helpers


@pytest.fixture()
def mock_components():
    return mock.MagicMock(application.Application)


class TestEmoji:
    @pytest.fixture
    def test_emoji(self):
        class Impl(emojis.Emoji):
            @property
            def url(self):
                return "http://example.com/test"

            @property
            def url_name(self):
                return "test:1234"

            @property
            def mention(self):
                return "<:test:1234>"

            @property
            def filename(self) -> str:
                return "test.png"

        return Impl()

    def test_is_mentionable(self, test_emoji):
        assert test_emoji.is_mentionable

    def test_aiter(self, test_emoji):
        aiter = mock.MagicMock()
        stream = mock.MagicMock(__aiter__=mock.MagicMock(return_value=aiter))
        with mock.patch.object(files, "WebResourceStream", return_value=stream) as new:
            assert test_emoji.__aiter__() is aiter

        new.assert_called_with("test.png", "http://example.com/test")


class TestUnicodeEmoji:
    england = [0x1F3F4, 0xE0067, 0xE0062, 0xE0065, 0xE006E, 0xE0067, 0xE007F]

    def test_deserialize(self, mock_components):
        emoji_obj = emojis.UnicodeEmoji.deserialize({"name": "🤷"}, components=mock_components)

        assert emoji_obj.name == "🤷"

    def test_url_name(self):
        assert emojis.UnicodeEmoji(name="🤷").url_name == "🤷"

    def test_mention(self):
        assert emojis.UnicodeEmoji(name="🤷").mention == "🤷"

    def test_codepoints(self):
        # :england:
        codepoints = self.england.copy()
        e = emojis.UnicodeEmoji(name="".join(map(chr, codepoints)))
        assert e.codepoints == codepoints

    def test_from_codepoints(self):
        # :england:
        codepoints = self.england.copy()
        e = emojis.UnicodeEmoji.from_codepoints(*codepoints)
        assert e.codepoints == codepoints

    def test_from_emoji(self):
        string = "\N{WHITE SMILING FACE}\N{VARIATION SELECTOR-16}"
        assert emojis.UnicodeEmoji.from_emoji(string).codepoints == [0x263A, 0xFE0F]

    @pytest.mark.parametrize(
        ["codepoints", "filename"],
        [
            (england.copy(), "1f3f4-e0067-e0062-e0065-e006e-e0067-e007f.png"),  # england
            ([0x1F38C], "1f38c.png"),  # crossed_flag
            ([0x263A, 0xFE0F], "263a.png"),  # relaxed
            ([0x1F3F3, 0xFE0F, 0x200D, 0x1F308], "1f3f3-fe0f-200d-1f308.png"),  # gay pride (outlier case)
            ([0x1F3F4, 0x200D, 0x2620, 0xFE0F], "1f3f4-200d-2620-fe0f.png"),  # pirate flag
            ([0x1F3F3, 0xFE0F], "1f3f3.png"),  # white flag
            ([0x1F939, 0x1F3FE, 0x200D, 0x2642, 0xFE0F], "1f939-1f3fe-200d-2642-fe0f.png"),  # man-juggling-tone-4
        ],
    )
    def test_filename(self, codepoints, filename):
        char = "".join(map(chr, codepoints))
        assert emojis.UnicodeEmoji(name=char).filename == filename

    @pytest.mark.parametrize(
        ["codepoints", "filename"],
        [
            (england.copy(), "1f3f4-e0067-e0062-e0065-e006e-e0067-e007f.png"),  # england
            ([0x1F38C], "1f38c.png"),  # crossed_flag
            ([0x263A, 0xFE0F], "263a.png"),  # relaxed
            ([0x1F3F3, 0xFE0F, 0x200D, 0x1F308], "1f3f3-fe0f-200d-1f308.png"),  # gay pride (outlier case)
            ([0x1F3F4, 0x200D, 0x2620, 0xFE0F], "1f3f4-200d-2620-fe0f.png"),  # pirate flag
            ([0x1F3F3, 0xFE0F], "1f3f3.png"),  # white flag
            ([0x1F939, 0x1F3FE, 0x200D, 0x2642, 0xFE0F], "1f939-1f3fe-200d-2642-fe0f.png"),  # man-juggling-tone-4
        ],
    )
    def test_url(self, codepoints, filename):
        char = "".join(map(chr, codepoints))
        url = "https://github.com/twitter/twemoji/raw/master/assets/72x72/" + filename
        assert emojis.UnicodeEmoji(name=char).url == url

    def test_unicode_names(self):
        codepoints = [0x1F939, 0x1F3FE, 0x200D, 0x2642, 0xFE0F]
        # https://unicode-table.com/en/
        names = [
            "JUGGLING",
            "EMOJI MODIFIER FITZPATRICK TYPE-5",
            "ZERO WIDTH JOINER",
            "MALE SIGN",
            "VARIATION SELECTOR-16",
        ]

        char = "".join(map(chr, codepoints))
        assert emojis.UnicodeEmoji(name=char).unicode_names == names

    def test_from_unicode_escape(self):
        input_string = r"\U0001f939\U0001f3fe\u200d\u2642\ufe0f"
        codepoints = [0x1F939, 0x1F3FE, 0x200D, 0x2642, 0xFE0F]
        assert emojis.UnicodeEmoji.from_unicode_escape(input_string).codepoints == codepoints

    def test_unicode_escape(self):
        codepoints = [0x1F939, 0x1F3FE, 0x200D, 0x2642, 0xFE0F]
        expected_string = r"\U0001f939\U0001f3fe\u200d\u2642\ufe0f"
        assert emojis.UnicodeEmoji(name="".join(map(chr, codepoints))).unicode_escape == expected_string


class TestCustomEmoji:
    def test_deserialize(self, mock_components):
        emoji_obj = emojis.CustomEmoji.deserialize(
            {"id": "1234", "name": "test", "animated": True}, components=mock_components
        )

        assert emoji_obj.id == 1234
        assert emoji_obj.name == "test"
        assert emoji_obj.is_animated is True

    def test_url_name(self):
        name = emojis.CustomEmoji(is_animated=True, id=bases.Snowflake("650573534627758100"), name="nyaa").url_name
        assert name == "nyaa:650573534627758100"

    @pytest.mark.parametrize(["animated", "extension"], [(True, ".gif"), (False, ".png")])
    def test_filename(self, animated, extension):
        emoji = emojis.CustomEmoji(is_animated=animated, id=bases.Snowflake(9876543210), name="Foo")
        assert emoji.filename == f"9876543210{extension}"

    @pytest.mark.parametrize(["animated", "is_mentionable"], [(True, True), (False, True), (None, False)])
    def test_is_mentionable(self, animated, is_mentionable):
        emoji = emojis.CustomEmoji(is_animated=animated, id=bases.Snowflake(123), name="Foo")
        assert emoji.is_mentionable is is_mentionable

    @pytest.mark.parametrize(["animated", "format_"], [(True, "gif"), (False, "png")])
    def test_url(self, animated, format_):
        emoji = emojis.CustomEmoji(is_animated=animated, id=bases.Snowflake(98765), name="Foo")
        mock_result = mock.MagicMock(spec_set=str)
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_result) as generate_cdn_url:
            assert emoji.url is mock_result

        generate_cdn_url.assert_called_once_with("emojis", "98765", format_=format_, size=None)


class TestKnownCustomEmoji:
    def test_deserialize(self, mock_components):
        mock_user = mock.MagicMock(users.User)

        test_user_payload = {"id": "123456", "username": "hikari", "discriminator": "0000", "avatar": None}
        with _helpers.patch_marshal_attr(
            emojis.KnownCustomEmoji, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            emoji_obj = emojis.KnownCustomEmoji.deserialize(
                {
                    "id": "12345",
                    "name": "testing",
                    "animated": False,
                    "available": True,
                    "roles": ["123", "456"],
                    "user": test_user_payload,
                    "require_colons": True,
                    "managed": False,
                },
                components=mock_components,
            )
            patched_user_deserializer.assert_called_once_with(test_user_payload, components=mock_components)

        assert emoji_obj.id == 12345
        assert emoji_obj.name == "testing"
        assert emoji_obj.is_animated is False
        assert emoji_obj.role_ids == {123, 456}
        assert emoji_obj.user == mock_user
        assert emoji_obj.is_colons_required is True
        assert emoji_obj.is_managed is False
        assert emoji_obj.is_available is True

    @pytest.fixture()
    def mock_guild_emoji_obj(self):
        return emojis.KnownCustomEmoji(
            is_animated=False,
            is_available=True,
            id=650573534627758100,
            name="nyaa",
            role_ids=[],
            is_colons_required=True,
            is_managed=False,
            user=mock.MagicMock(users.User),
        )

    def test_mention_when_animated(self, mock_guild_emoji_obj):
        mock_guild_emoji_obj.is_animated = True
        assert mock_guild_emoji_obj.mention == "<a:nyaa:650573534627758100>"

    def test_mention_when_not_animated(self, mock_guild_emoji_obj):
        mock_guild_emoji_obj.is_animated = False
        assert mock_guild_emoji_obj.mention == "<:nyaa:650573534627758100>"


@pytest.mark.parametrize(
    ["payload", "expected_type"],
    [({"name": "🤷"}, emojis.UnicodeEmoji), ({"id": "1234", "name": "test"}, emojis.CustomEmoji)],
)
def test_deserialize_reaction_emoji_returns_expected_type(payload, expected_type):
    assert isinstance(emojis.deserialize_reaction_emoji(payload), expected_type)


def test_deserialize_reaction_emoji_passes_kwargs(mock_components):
    emoji_obj = emojis.deserialize_reaction_emoji({"id": "1234", "name": "test"}, components=mock_components)
    assert emoji_obj._components is mock_components
