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
# SOFTWARE.

import mock
import pytest

from hikari import emojis
from hikari import guilds
from hikari.events import reaction_events
from tests.hikari import hikari_test_helpers


class TestReactionAddEvent:
    def test_is_for_emoji_when_custom_emoji_matches(self):
        event = hikari_test_helpers.mock_class_namespace(reaction_events.ReactionAddEvent, emoji_id=333333)()

        assert event.is_for_emoji(emojis.CustomEmoji(id=333333, name=None, is_animated=True))

    def test_is_for_emoji_when_unicode_emoji_matches(self):
        event = hikari_test_helpers.mock_class_namespace(reaction_events.ReactionAddEvent, emoji_name="🌲")()

        assert event.is_for_emoji(emojis.UnicodeEmoji("🌲"))

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hi", emojis.CustomEmoji(name=None, id=54123, is_animated=False)),
            (123321, None, emojis.UnicodeEmoji("no u")),
        ],
    )
    def test_is_for_emoji_when_wrong_emoji_type(self, emoji_id, emoji_name, emoji):
        event = hikari_test_helpers.mock_class_namespace(
            reaction_events.ReactionAddEvent, emoji_id=emoji_id, emoji_name=emoji_name
        )()

        assert event.is_for_emoji(emoji) is False

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hi", emojis.UnicodeEmoji("bye")),
            (123321, None, emojis.CustomEmoji(id=123312123, name=None, is_animated=False)),
        ],
    )
    def test_is_for_emoji_when_emoji_miss_match(self, emoji_id, emoji_name, emoji):
        event = hikari_test_helpers.mock_class_namespace(
            reaction_events.ReactionAddEvent, emoji_id=emoji_id, emoji_name=emoji_name
        )()

        assert event.is_for_emoji(emoji) is False


class TestReactionDeleteEvent:
    def test_is_for_emoji_when_custom_emoji_matches(self):
        event = hikari_test_helpers.mock_class_namespace(reaction_events.ReactionDeleteEvent, emoji_id=333)()

        assert event.is_for_emoji(emojis.CustomEmoji(id=333, name=None, is_animated=True))

    def test_is_for_emoji_when_unicode_emoji_matches(self):
        event = hikari_test_helpers.mock_class_namespace(reaction_events.ReactionDeleteEvent, emoji_name="e")()

        assert event.is_for_emoji(emojis.UnicodeEmoji("e"))

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hasdi", emojis.CustomEmoji(name=None, id=3123, is_animated=False)),
            (534123, None, emojis.UnicodeEmoji("nodfgdu")),
        ],
    )
    def test_is_for_emoji_when_wrong_emoji_type(self, emoji_id, emoji_name, emoji):
        event = hikari_test_helpers.mock_class_namespace(
            reaction_events.ReactionDeleteEvent, emoji_id=emoji_id, emoji_name=emoji_name
        )()

        assert event.is_for_emoji(emoji) is False

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hfdasi", emojis.UnicodeEmoji("bgye")),
            (54123, None, emojis.CustomEmoji(id=34123, name=None, is_animated=False)),
        ],
    )
    def test_is_for_emoji_when_emoji_miss_match(self, emoji_id, emoji_name, emoji):
        event = hikari_test_helpers.mock_class_namespace(
            reaction_events.ReactionDeleteEvent, emoji_id=emoji_id, emoji_name=emoji_name
        )()

        assert event.is_for_emoji(emoji) is False


class TestReactionDeleteEmojiEvent:
    def test_is_for_emoji_when_custom_emoji_matches(self):
        event = hikari_test_helpers.mock_class_namespace(reaction_events.ReactionDeleteEmojiEvent, emoji_id=332223333)()

        assert event.is_for_emoji(emojis.CustomEmoji(id=332223333, name=None, is_animated=True))

    def test_is_for_emoji_when_unicode_emoji_matches(self):
        event = hikari_test_helpers.mock_class_namespace(reaction_events.ReactionDeleteEmojiEvent, emoji_name="🌲e")()

        assert event.is_for_emoji(emojis.UnicodeEmoji("🌲e"))

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "heeei", emojis.CustomEmoji(name=None, id=541123, is_animated=False)),
            (1233211, None, emojis.UnicodeEmoji("no eeeu")),
        ],
    )
    def test_is_for_emoji_when_wrong_emoji_type(self, emoji_id, emoji_name, emoji):
        event = hikari_test_helpers.mock_class_namespace(
            reaction_events.ReactionDeleteEmojiEvent, emoji_id=emoji_id, emoji_name=emoji_name
        )()

        assert event.is_for_emoji(emoji) is False

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "dsahi", emojis.UnicodeEmoji("bye321")),
            (12331231, None, emojis.CustomEmoji(id=121233312123, name=None, is_animated=False)),
        ],
    )
    def test_is_for_emoji_when_emoji_miss_match(self, emoji_id, emoji_name, emoji):
        event = hikari_test_helpers.mock_class_namespace(
            reaction_events.ReactionDeleteEmojiEvent, emoji_id=emoji_id, emoji_name=emoji_name
        )()

        assert event.is_for_emoji(emoji) is False


class TestGuildReactionAddEvent:
    @pytest.fixture
    def event(self):
        return reaction_events.GuildReactionAddEvent(
            shard=object(),
            member=mock.MagicMock(guilds.Member),
            channel_id=123,
            message_id=456,
            emoji_name="👌",
            emoji_id=None,
            is_animated=False,
        )

    def test_app_property(self, event):
        assert event.app is event.member.app

    def test_guild_id_property(self, event):
        event.member.guild_id = 123
        assert event.guild_id == 123

    def test_user_id_property(self, event):
        event.member.user.id = 123
        assert event.user_id == 123
