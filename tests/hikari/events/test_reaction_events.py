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

import typing

import mock
import pytest

from hikari import emojis
from hikari import guilds
from hikari import snowflakes
from hikari import traits
from hikari.api import shard as shard_api
from hikari.events import reaction_events


class TestReactionAddEvent:
    class MockReactionAddEvent(reaction_events.ReactionAddEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._channel_id = snowflakes.Snowflake(123)
            self._message_id = snowflakes.Snowflake(456)
            self._user_id = snowflakes.Snowflake(789)
            self._emoji_name = "reaction_add_emoji"
            self._emoji_id = snowflakes.Snowflake(112)
            self._is_animated = False

        @property
        def app(self) -> traits.RESTAware:
            return self._shard

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def channel_id(self) -> snowflakes.Snowflake:
            return self._channel_id

        @property
        def message_id(self) -> snowflakes.Snowflake:
            return self._message_id

        @property
        def user_id(self) -> snowflakes.Snowflake:
            return self._user_id

        @property
        def emoji_name(self) -> typing.Union[emojis.UnicodeEmoji, str, None]:
            return self._emoji_name

        @property
        def emoji_id(self) -> typing.Optional[snowflakes.Snowflake]:
            return self._emoji_id

        @property
        def is_animated(self) -> bool:
            return self._is_animated

    @pytest.fixture
    def reaction_add_event(self, hikari_app: traits.RESTAware) -> reaction_events.ReactionAddEvent:
        return TestReactionAddEvent.MockReactionAddEvent(hikari_app)

    def test_is_for_emoji_when_custom_emoji_matches(self, reaction_add_event: reaction_events.ReactionAddEvent):
        assert reaction_add_event.is_for_emoji(
            emojis.CustomEmoji(id=snowflakes.Snowflake(112), name="reaction_add_emoji", is_animated=False)
        )

    def test_is_for_emoji_when_unicode_emoji_matches(self, reaction_add_event: reaction_events.ReactionAddEvent):
        with mock.patch.object(reaction_add_event, "_emoji_name", "🌲"):
            assert reaction_add_event.is_for_emoji(emojis.UnicodeEmoji("🌲"))

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hi", emojis.CustomEmoji(name="hi", id=snowflakes.Snowflake(54123), is_animated=False)),
            (123321, None, emojis.UnicodeEmoji("no u")),
        ],
    )
    def test_is_for_emoji_when_wrong_emoji_type(
        self,
        reaction_add_event: reaction_events.ReactionAddEvent,
        emoji_id: typing.Optional[int],
        emoji_name: typing.Optional[str],
        emoji: emojis.Emoji,
    ):
        with (
            mock.patch.object(reaction_add_event, "_emoji_id", emoji_id),
            mock.patch.object(reaction_add_event, "_emoji_name", emoji_name),
        ):
            assert reaction_add_event.is_for_emoji(emoji) is False

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hi", emojis.UnicodeEmoji("bye")),
            (123321, "test", emojis.CustomEmoji(id=snowflakes.Snowflake(123312123), name="test", is_animated=False)),
        ],
    )
    def test_is_for_emoji_when_emoji_miss_match(
        self,
        reaction_add_event: reaction_events.ReactionAddEvent,
        emoji_id: typing.Optional[int],
        emoji_name: typing.Optional[str],
        emoji: emojis.Emoji,
    ):
        with (
            mock.patch.object(reaction_add_event, "_emoji_id", emoji_id),
            mock.patch.object(reaction_add_event, "_emoji_name", emoji_name),
        ):
            assert reaction_add_event.is_for_emoji(emoji) is False


class TestReactionDeleteEvent:
    class MockReactionDeleteEvent(reaction_events.ReactionDeleteEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._channel_id = snowflakes.Snowflake(123)
            self._message_id = snowflakes.Snowflake(456)
            self._user_id = snowflakes.Snowflake(789)
            self._emoji_name = "reaction_delete_emoji"
            self._emoji_id = snowflakes.Snowflake(112)

        @property
        def app(self) -> traits.RESTAware:
            return self._shard

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def channel_id(self) -> snowflakes.Snowflake:
            return self._channel_id

        @property
        def message_id(self) -> snowflakes.Snowflake:
            return self._message_id

        @property
        def user_id(self) -> snowflakes.Snowflake:
            return self._user_id

        @property
        def emoji_name(self) -> typing.Union[emojis.UnicodeEmoji, str, None]:
            return self._emoji_name

        @property
        def emoji_id(self) -> typing.Optional[snowflakes.Snowflake]:
            return self._emoji_id

    @pytest.fixture
    def reaction_delete_event(self, hikari_app: traits.RESTAware) -> reaction_events.ReactionDeleteEvent:
        return TestReactionDeleteEvent.MockReactionDeleteEvent(hikari_app)

    def test_is_for_emoji_when_custom_emoji_matches(self, reaction_delete_event: reaction_events.ReactionDeleteEvent):
        assert reaction_delete_event.is_for_emoji(
            emojis.CustomEmoji(id=snowflakes.Snowflake(112), name="reaction_delete_emoji", is_animated=True)
        )

    def test_is_for_emoji_when_unicode_emoji_matches(self, reaction_delete_event: reaction_events.ReactionDeleteEvent):
        with mock.patch.object(reaction_delete_event, "_emoji_name", "e"):
            assert reaction_delete_event.is_for_emoji(emojis.UnicodeEmoji("e"))

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hasdi", emojis.CustomEmoji(name="hasdi", id=snowflakes.Snowflake(3123), is_animated=False)),
            (534123, None, emojis.UnicodeEmoji("nodfgdu")),
        ],
    )
    def test_is_for_emoji_when_wrong_emoji_type(
        self,
        reaction_delete_event: reaction_events.ReactionDeleteEvent,
        emoji_id: typing.Optional[int],
        emoji_name: typing.Optional[str],
        emoji: emojis.Emoji,
    ):
        with (
            mock.patch.object(reaction_delete_event, "_emoji_id", emoji_id),
            mock.patch.object(reaction_delete_event, "_emoji_name", emoji_name),
        ):
            assert reaction_delete_event.is_for_emoji(emoji) is False

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "hfdasi", emojis.UnicodeEmoji("bgye")),
            (54123, "test", emojis.CustomEmoji(id=snowflakes.Snowflake(34123), name="test", is_animated=False)),
        ],
    )
    def test_is_for_emoji_when_emoji_miss_match(
        self,
        reaction_delete_event: reaction_events.ReactionDeleteEvent,
        emoji_id: typing.Optional[int],
        emoji_name: typing.Optional[str],
        emoji: emojis.Emoji,
    ):
        with (
            mock.patch.object(reaction_delete_event, "_emoji_id", emoji_id),
            mock.patch.object(reaction_delete_event, "_emoji_name", emoji_name),
        ):
            assert reaction_delete_event.is_for_emoji(emoji) is False


class TestReactionDeleteEmojiEvent:
    class MockReactionDeleteEmojiEvent(reaction_events.ReactionDeleteEmojiEvent):
        def __init__(self, app: traits.RESTAware):
            self._app = app
            self._shard = mock.Mock()
            self._channel_id = snowflakes.Snowflake(123)
            self._message_id = snowflakes.Snowflake(456)
            self._emoji_name = "reaction_delete_emoji_emoji"
            self._emoji_id = snowflakes.Snowflake(112)

        @property
        def app(self) -> traits.RESTAware:
            return self._shard

        @property
        def shard(self) -> shard_api.GatewayShard:
            return self._shard

        @property
        def channel_id(self) -> snowflakes.Snowflake:
            return self._channel_id

        @property
        def message_id(self) -> snowflakes.Snowflake:
            return self._message_id

        @property
        def emoji_name(self) -> typing.Union[emojis.UnicodeEmoji, str, None]:
            return self._emoji_name

        @property
        def emoji_id(self) -> typing.Optional[snowflakes.Snowflake]:
            return self._emoji_id

    @pytest.fixture
    def reaction_delete_emoji_event(self, hikari_app: traits.RESTAware) -> reaction_events.ReactionDeleteEmojiEvent:
        return TestReactionDeleteEmojiEvent.MockReactionDeleteEmojiEvent(hikari_app)

    def test_is_for_emoji_when_custom_emoji_matches(
        self, reaction_delete_emoji_event: reaction_events.ReactionDeleteEmojiEvent
    ):
        assert reaction_delete_emoji_event.is_for_emoji(
            emojis.CustomEmoji(id=snowflakes.Snowflake(112), name="reaction_delete_emoji_emoji", is_animated=True)
        )

    def test_is_for_emoji_when_unicode_emoji_matches(
        self, reaction_delete_emoji_event: reaction_events.ReactionDeleteEmojiEvent
    ):
        with mock.patch.object(reaction_delete_emoji_event, "_emoji_name", "🌲e"):
            assert reaction_delete_emoji_event.is_for_emoji(emojis.UnicodeEmoji("🌲e"))

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "heeei", emojis.CustomEmoji(name="heeei", id=snowflakes.Snowflake(541123), is_animated=False)),
            (1233211, None, emojis.UnicodeEmoji("no eeeu")),
        ],
    )
    def test_is_for_emoji_when_wrong_emoji_type(
        self,
        reaction_delete_emoji_event: reaction_events.ReactionDeleteEmojiEvent,
        emoji_id: typing.Optional[int],
        emoji_name: typing.Optional[str],
        emoji: emojis.Emoji,
    ):
        with (
            mock.patch.object(reaction_delete_emoji_event, "_emoji_id", emoji_id),
            mock.patch.object(reaction_delete_emoji_event, "_emoji_name", emoji_name),
        ):
            assert reaction_delete_emoji_event.is_for_emoji(emoji) is False

    @pytest.mark.parametrize(
        ("emoji_id", "emoji_name", "emoji"),
        [
            (None, "dsahi", emojis.UnicodeEmoji("bye321")),
            (
                12331231,
                "sadfasd",
                emojis.CustomEmoji(id=snowflakes.Snowflake(121233312123), name="sdf", is_animated=False),
            ),
        ],
    )
    def test_is_for_emoji_when_emoji_miss_match(
        self,
        reaction_delete_emoji_event: reaction_events.ReactionDeleteEmojiEvent,
        emoji_id: typing.Optional[int],
        emoji_name: typing.Optional[str],
        emoji: emojis.Emoji,
    ):
        with (
            mock.patch.object(reaction_delete_emoji_event, "_emoji_id", emoji_id),
            mock.patch.object(reaction_delete_emoji_event, "_emoji_name", emoji_name),
        ):
            assert reaction_delete_emoji_event.is_for_emoji(emoji) is False


class TestGuildReactionAddEvent:
    @pytest.fixture
    def guild_reaction_add_event(self) -> reaction_events.GuildReactionAddEvent:
        return reaction_events.GuildReactionAddEvent(
            shard=mock.Mock(),
            member=mock.MagicMock(guilds.Member),
            channel_id=snowflakes.Snowflake(123),
            message_id=snowflakes.Snowflake(456),
            emoji_name="👌",
            emoji_id=None,
            is_animated=False,
        )

    def test_app_property(self, guild_reaction_add_event: reaction_events.GuildReactionAddEvent):
        assert guild_reaction_add_event.app is guild_reaction_add_event.member.app

    def test_guild_id_property(self, guild_reaction_add_event: reaction_events.GuildReactionAddEvent):
        guild_reaction_add_event.member.guild_id = snowflakes.Snowflake(123)
        assert guild_reaction_add_event.guild_id == 123

    def test_user_id_property(self, guild_reaction_add_event: reaction_events.GuildReactionAddEvent):
        with mock.patch.object(guild_reaction_add_event.member.user, "id", 123):
            assert guild_reaction_add_event.user_id == 123
