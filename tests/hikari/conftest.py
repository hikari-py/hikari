from __future__ import annotations

import datetime

import mock
import pytest

from hikari import channels
from hikari import emojis
from hikari import guilds
from hikari import messages
from hikari import snowflakes
from hikari import stickers
from hikari import traits
from hikari import users


@pytest.fixture
def hikari_app() -> traits.RESTAware:
    return mock.Mock(spec=traits.RESTAware)


@pytest.fixture
def hikari_partial_guild() -> guilds.PartialGuild:
    return guilds.PartialGuild(
        app=mock.Mock(), id=snowflakes.Snowflake(123), icon_hash="partial_guild_icon_hash", name="partial_guild"
    )


@pytest.fixture
def hikari_guild_text_channel() -> channels.GuildTextChannel:
    return channels.GuildTextChannel(
        app=mock.Mock(),
        id=snowflakes.Snowflake(4560),
        name="guild_text_channel_name",
        type=channels.ChannelType.GUILD_TEXT,
        guild_id=mock.Mock(),  # FIXME: Can this be pulled from the actual fixture?
        parent_id=mock.Mock(),  # FIXME: Can this be pulled from the actual fixture?
        position=0,
        is_nsfw=False,
        permission_overwrites={},
        topic=None,
        last_message_id=None,
        rate_limit_per_user=datetime.timedelta(seconds=10),
        last_pin_timestamp=None,
        default_auto_archive_duration=datetime.timedelta(seconds=10),
    )


@pytest.fixture
def hikari_user() -> users.User:
    return users.UserImpl(
        id=snowflakes.Snowflake(789),
        app=mock.Mock(),
        discriminator="0",
        username="user_username",
        global_name="user_global_name",
        avatar_hash="user_avatar_hash",
        banner_hash="user_banner_hash",
        accent_color=None,
        is_bot=False,
        is_system=False,
        flags=users.UserFlag.NONE,
    )


@pytest.fixture
def hikari_message() -> messages.Message:
    return messages.Message(
        id=snowflakes.Snowflake(101),
        app=mock.Mock(),
        channel_id=snowflakes.Snowflake(456),
        guild_id=None,
        author=mock.Mock(),
        member=mock.Mock(),
        content=None,
        timestamp=datetime.datetime.fromtimestamp(6000),
        edited_timestamp=None,
        is_tts=False,
        user_mentions={},
        role_mention_ids=[],
        channel_mentions={},
        mentions_everyone=False,
        attachments=[],
        embeds=[],
        reactions=[],
        is_pinned=False,
        webhook_id=snowflakes.Snowflake(432),
        type=messages.MessageType.DEFAULT,
        activity=None,
        application=None,
        message_reference=None,
        flags=messages.MessageFlag.NONE,
        stickers=[],
        nonce=None,
        referenced_message=None,
        application_id=None,
        components=[],
        thread=None,
        interaction_metadata=None,
    )


@pytest.fixture
def hikari_partial_sticker() -> stickers.PartialSticker:
    return stickers.PartialSticker(
        id=snowflakes.Snowflake(222), name="sticker_name", format_type=stickers.StickerFormatType.PNG
    )


@pytest.fixture
def hikari_guild_sticker() -> stickers.GuildSticker:
    return stickers.GuildSticker(
        id=snowflakes.Snowflake(2220),
        name="guild_sticker_name",
        format_type=stickers.StickerFormatType.PNG,
        description="guild_sticker_description",
        guild_id=snowflakes.Snowflake(123),
        is_available=True,
        tag="guild_sticker_tag",
        user=None,
    )


@pytest.fixture
def hikari_custom_emoji() -> emojis.CustomEmoji:
    return emojis.CustomEmoji(id=snowflakes.Snowflake(444), name="custom_emoji_name", is_animated=False)


@pytest.fixture
def hikari_unicode_emoji() -> emojis.UnicodeEmoji:
    return emojis.UnicodeEmoji("🙂")
