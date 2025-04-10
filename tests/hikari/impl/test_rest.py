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

import asyncio
import concurrent.futures
import contextlib
import datetime
import http
import re
import typing

import aiohttp
import mock
import pytest

from hikari import applications
from hikari import audit_logs
from hikari import channels
from hikari import colors
from hikari import commands
from hikari import embeds
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import guilds
from hikari import interactions
from hikari import invites
from hikari import iterators
from hikari import locales
from hikari import messages
from hikari import permissions
from hikari import scheduled_events
from hikari import sessions
from hikari import snowflakes
from hikari import stage_instances
from hikari import stickers
from hikari import undefined
from hikari import urls
from hikari import users
from hikari import voices
from hikari import webhooks
from hikari.api import cache
from hikari.api import rest as rest_api
from hikari.impl import config
from hikari.impl import entity_factory
from hikari.impl import rate_limits
from hikari.impl import rest
from hikari.impl import special_endpoints
from hikari.internal import data_binding
from hikari.internal import mentions
from hikari.internal import net
from hikari.internal import routes
from hikari.internal import time
from tests.hikari import hikari_test_helpers

#################
# _RESTProvider #
#################


class TestRestProvider:
    @pytest.fixture
    def rest_client(self) -> rest.RESTClientImpl:
        return mock.Mock()

    @pytest.fixture
    def executor(self) -> concurrent.futures.Executor:
        return mock.Mock()

    @pytest.fixture
    def entity_factory(self) -> entity_factory.EntityFactoryImpl:
        return mock.Mock()

    @pytest.fixture
    def rest_provider(
        self,
        rest_client: rest.RESTClientImpl,
        executor: concurrent.futures.Executor,
        entity_factory: entity_factory.EntityFactoryImpl,
    ):
        provider = rest._RESTProvider(executor)

        provider.update(rest_client, entity_factory)

        return provider

    def test_rest_property(self, rest_provider: rest._RESTProvider, rest_client: StubRestClient):
        assert rest_provider.rest == rest_client

    def test_http_settings_property(self, rest_provider: rest._RESTProvider, rest_client: StubRestClient):
        assert rest_provider.http_settings == rest_client.http_settings

    def test_proxy_settings_property(self, rest_provider: rest._RESTProvider, rest_client: StubRestClient):
        assert rest_provider.proxy_settings == rest_client.proxy_settings

    def test_entity_factory_property(
        self, rest_provider: rest._RESTProvider, entity_factory: entity_factory.EntityFactoryImpl
    ):
        assert rest_provider.entity_factory == entity_factory

    def test_executor_property(self, rest_provider: rest._RESTProvider, executor: concurrent.futures.Executor):
        assert rest_provider.executor == executor


#############################
# ClientCredentialsStrategy #
#############################


class TestClientCredentialsStrategy:
    @pytest.fixture
    def mock_token(self) -> applications.PartialOAuth2Token:
        return mock.Mock(
            applications.PartialOAuth2Token,
            expires_in=datetime.timedelta(weeks=1),
            token_type=applications.TokenType.BEARER,
            access_token="okokok.fofofo.ddd",
        )

    def test_client_id_property(self, mock_application: applications.Application):
        token = rest.ClientCredentialsStrategy(client=mock_application, client_secret="123123123")

        assert token.client_id == 111

    def test_scopes_property(self):
        scopes = [applications.OAuth2Scope.BOT, applications.OAuth2Scope.APPLICATIONS_ENTITLEMENTS]
        token = rest.ClientCredentialsStrategy(client=123, client_secret="123123123", scopes=scopes)

        assert token.scopes == ("bot", "applications.entitlements")

    def test_token_type_property(self):
        token = rest.ClientCredentialsStrategy(client=123, client_secret="123123123", scopes=[])

        assert token.token_type is applications.TokenType.BEARER

    @pytest.mark.asyncio
    async def test_acquire_on_new_instance(self, mock_token: applications.PartialOAuth2Token):
        mock_rest = mock.Mock(authorize_client_credentials_token=mock.AsyncMock(return_value=mock_token))

        result = await rest.ClientCredentialsStrategy(client=54123123, client_secret="123123123").acquire(mock_rest)

        assert result == "Bearer okokok.fofofo.ddd"

        mock_rest.authorize_client_credentials_token.assert_awaited_once_with(
            client=54123123, client_secret="123123123", scopes=("applications.commands.update", "identify")
        )

    @pytest.mark.asyncio
    async def test_acquire_handles_out_of_date_token(self, mock_token: applications.PartialOAuth2Token):
        mock_old_token = mock.Mock(
            applications.PartialOAuth2Token,
            expires_in=datetime.timedelta(weeks=1),
            token_type=applications.TokenType.BEARER,
            access_token="okokok.fofdsasdasdofo.ddd",
        )
        mock_rest = mock.Mock(authorize_client_credentials_token=mock.AsyncMock(return_value=mock_token))
        strategy = rest.ClientCredentialsStrategy(client=3412321, client_secret="54123123")
        token = await strategy.acquire(
            mock.Mock(authorize_client_credentials_token=mock.AsyncMock(return_value=mock_old_token))
        )

        with mock.patch.object(time, "monotonic", return_value=99999999999):
            new_token = await strategy.acquire(mock_rest)

        mock_rest.authorize_client_credentials_token.assert_awaited_once_with(
            client=3412321, client_secret="54123123", scopes=("applications.commands.update", "identify")
        )
        assert new_token != token
        assert new_token == "Bearer okokok.fofofo.ddd"

    @pytest.mark.asyncio
    async def test_acquire_handles_token_being_set_before_lock_is_acquired(
        self, mock_token: applications.PartialOAuth2Token
    ):
        lock = asyncio.Lock()
        mock_rest = mock.Mock(authorize_client_credentials_token=mock.AsyncMock(side_effect=[mock_token]))

        with mock.patch.object(asyncio, "Lock", return_value=lock):
            strategy = rest.ClientCredentialsStrategy(client=6512312, client_secret="453123123")

        async with lock:
            tokens_gather = asyncio.gather(
                strategy.acquire(mock_rest), strategy.acquire(mock_rest), strategy.acquire(mock_rest)
            )

        results = await tokens_gather

        mock_rest.authorize_client_credentials_token.assert_awaited_once_with(
            client=6512312, client_secret="453123123", scopes=("applications.commands.update", "identify")
        )
        assert results == ["Bearer okokok.fofofo.ddd", "Bearer okokok.fofofo.ddd", "Bearer okokok.fofofo.ddd"]

    @pytest.mark.asyncio
    async def test_acquire_after_invalidation(self, mock_token: applications.PartialOAuth2Token):
        mock_old_token = mock.Mock(
            applications.PartialOAuth2Token,
            expires_in=datetime.timedelta(weeks=1),
            token_type=applications.TokenType.BEARER,
            access_token="okokok.fofdsasdasdofo.ddd",
        )
        mock_rest = mock.Mock(authorize_client_credentials_token=mock.AsyncMock(return_value=mock_token))
        strategy = rest.ClientCredentialsStrategy(client=123, client_secret="123456")
        token = await strategy.acquire(
            mock.Mock(authorize_client_credentials_token=mock.AsyncMock(return_value=mock_old_token))
        )

        strategy.invalidate(token)
        new_token = await strategy.acquire(mock_rest)

        mock_rest.authorize_client_credentials_token.assert_awaited_once_with(
            client=123, client_secret="123456", scopes=("applications.commands.update", "identify")
        )
        assert new_token != token
        assert new_token == "Bearer okokok.fofofo.ddd"

    @pytest.mark.asyncio
    async def test_acquire_uses_newly_cached_token_after_acquiring_lock(self):
        class MockLock:
            def __init__(self, strategy: rest.ClientCredentialsStrategy):
                self._strategy = strategy

            async def __aenter__(self):
                self._strategy._token = "abc.abc.abc"
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return

        mock_rest = mock.AsyncMock()
        strategy = rest.ClientCredentialsStrategy(client=65123, client_secret="12354")
        strategy._lock = MockLock(strategy)
        strategy._token = None
        strategy._expire_at = time.monotonic() + 500

        result = await strategy.acquire(mock_rest)

        assert result == "abc.abc.abc"

        mock_rest.authorize_client_credentials_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_caches_client_http_response_error(self):
        mock_rest = mock.AsyncMock()
        error = errors.ClientHTTPResponseError(
            url="okokok", status=42, headers={}, raw_body=b"ok", message="OK", code=34123
        )
        mock_rest.authorize_client_credentials_token.side_effect = error
        strategy = rest.ClientCredentialsStrategy(client=65123, client_secret="12354")

        with pytest.raises(errors.ClientHTTPResponseError):
            await strategy.acquire(mock_rest)

        with pytest.raises(errors.ClientHTTPResponseError):
            await strategy.acquire(mock_rest)

        mock_rest.authorize_client_credentials_token.assert_awaited_once_with(
            client=65123, client_secret="12354", scopes=("applications.commands.update", "identify")
        )

    def test_invalidate_when_token_is_not_stored_token(self):
        strategy = rest.ClientCredentialsStrategy(client=65123, client_secret="12354")
        strategy._expire_at = 10.0
        strategy._token = "token"

        strategy.invalidate("tokena")

        assert strategy._expire_at == 10.0
        assert strategy._token == "token"

    def test_invalidate_when_no_token_specified(self):
        strategy = rest.ClientCredentialsStrategy(client=65123, client_secret="12354")
        strategy._expire_at = 10.0
        strategy._token = "token"

        strategy.invalidate(None)

        assert strategy._expire_at == 0.0
        assert strategy._token is None

    def test_invalidate_when_token_is_stored_token(self):
        strategy = rest.ClientCredentialsStrategy(client=65123, client_secret="12354")
        strategy._expire_at = 10.0
        strategy._token = "token"

        strategy.invalidate("token")

        assert strategy._expire_at == 0.0
        assert strategy._token is None


###########
# RESTApp #
###########


class TestRESTApp:
    @pytest.fixture
    def rest_app(self) -> rest.RESTApp:
        return hikari_test_helpers.mock_class_namespace(rest.RESTApp, slots_=False)(
            executor=None,
            http_settings=mock.Mock(spec_set=config.HTTPSettings),
            max_rate_limit=float("inf"),
            max_retries=0,
            proxy_settings=mock.Mock(spec_set=config.ProxySettings),
            url="https://some.url",
        )

    def test_executor_property(self, rest_app: rest.RESTApp):
        mock_executor = mock.Mock()
        rest_app._executor = mock_executor
        assert rest_app.executor is mock_executor

    def test_http_settings_property(self, rest_app: rest.RESTApp):
        mock_http_settings = mock.Mock()
        rest_app._http_settings = mock_http_settings
        assert rest_app.http_settings is mock_http_settings

    def test_proxy_settings(self, rest_app: rest.RESTApp):
        mock_proxy_settings = mock.Mock()
        rest_app._proxy_settings = mock_proxy_settings
        assert rest_app.proxy_settings is mock_proxy_settings

    def test_acquire(self, rest_app: rest.RESTApp):
        rest_app._client_session = mock.Mock()
        rest_app._bucket_manager = mock.Mock()

        with (
            mock.patch.object(entity_factory, "EntityFactoryImpl") as mock_entity_factory,
            mock.patch.object(rest, "RESTClientImpl") as mock_client,
        ):
            rest_app.acquire(token="token", token_type="Type")

        mock_client.assert_called_once_with(
            cache=None,
            entity_factory=mock_entity_factory.return_value,
            executor=rest_app._executor,
            http_settings=rest_app._http_settings,
            max_retries=0,
            proxy_settings=rest_app._proxy_settings,
            dumps=rest_app._dumps,
            loads=rest_app._loads,
            token="token",
            token_type="Type",
            rest_url=rest_app._url,
            bucket_manager=rest_app._bucket_manager,
            bucket_manager_owner=False,
            client_session=rest_app._client_session,
            client_session_owner=False,
        )

        rest_provider = mock_entity_factory.call_args_list[0][0][0]
        assert rest_provider.entity_factory is mock_entity_factory.return_value
        assert rest_provider.rest is mock_client.return_value
        assert rest_provider.executor is rest_app._executor

    def test_acquire_defaults_to_bearer_for_a_string_token(self, rest_app: rest.RESTApp):
        rest_app._client_session = mock.Mock()
        rest_app._bucket_manager = mock.Mock()

        with (
            mock.patch.object(entity_factory, "EntityFactoryImpl") as mock_entity_factory,
            mock.patch.object(rest, "RESTClientImpl") as mock_client,
        ):
            rest_app.acquire(token="token")

        mock_client.assert_called_once_with(
            cache=None,
            entity_factory=mock_entity_factory.return_value,
            executor=rest_app._executor,
            http_settings=rest_app._http_settings,
            max_retries=0,
            proxy_settings=rest_app._proxy_settings,
            dumps=rest_app._dumps,
            loads=rest_app._loads,
            token="token",
            token_type=applications.TokenType.BEARER,
            rest_url=rest_app._url,
            bucket_manager=rest_app._bucket_manager,
            bucket_manager_owner=False,
            client_session=rest_app._client_session,
            client_session_owner=False,
        )

        rest_provider = mock_entity_factory.call_args_list[0][0][0]
        assert rest_provider.entity_factory is mock_entity_factory.return_value
        assert rest_provider.rest is mock_client.return_value
        assert rest_provider.executor is rest_app._executor


##################
# RESTClientImpl #
##################


@pytest.fixture(scope="module")
def rest_client_class() -> typing.Type[rest.RESTClientImpl]:
    return hikari_test_helpers.mock_class_namespace(rest.RESTClientImpl, slots_=False)


@pytest.fixture
def mock_cache() -> cache.MutableCache:
    return mock.Mock()


@pytest.fixture
def rest_client(
    rest_client_class: typing.Type[rest.RESTClientImpl], mock_cache: cache.MutableCache
) -> rest.RESTClientImpl:
    obj = rest_client_class(
        cache=mock_cache,
        http_settings=mock.Mock(spec=config.HTTPSettings),
        max_rate_limit=float("inf"),
        proxy_settings=mock.Mock(spec=config.ProxySettings),
        token="some_token",
        token_type="tYpe",
        max_retries=0,
        rest_url="https://some.where/api/v3",
        executor=mock.Mock(),
        entity_factory=mock.Mock(),
        bucket_manager=mock.Mock(
            acquire_bucket=mock.Mock(return_value=hikari_test_helpers.AsyncContextManagerMock()),
            acquire_authentication=mock.AsyncMock(),
        ),
        client_session=mock.Mock(request=mock.AsyncMock()),
    )
    obj._close_event = mock.Mock()
    return obj


class MockStream:
    def __init__(self, data: str):
        self.open = False
        self.data = data

    async def data_uri(self):
        if not self.open:
            raise RuntimeError("Tried to read off a closed stream")

        return self.data

    async def __aenter__(self):
        self.open = True
        return self

    async def __aexit__(self, exc_type: type[Exception], exc: Exception, exc_tb: typing.Any) -> None:
        self.open = False


class MockFileResource(files.Resource[typing.Any]):
    @property
    def filename(self) -> str:
        return ""

    @property
    def url(self) -> str:
        return ""

    def __init__(self, stream_data: str):
        self._stream = MockStream(data=stream_data)

    def stream(self, executor: concurrent.futures.Executor):
        return self._stream


@pytest.fixture
def file_resource_patch() -> typing.Generator[files.Resource[typing.Any], typing.Any, None]:
    resource = MockFileResource("some data")
    with mock.patch.object(files, "ensure_resource", return_value=resource):
        yield resource


# There is a naming scheme to everything.
# Partial objects have a unique identifier. guild=123, channel=456, user=789 and message=101
# Sub objects, use their Type to identify them further. For example, a guild stage channel would be 45613
# Objects that do not have partial, go in increments of a plural of 3 numbers.
# for example, applications start at 111, the next item would be 222 and so on.


@pytest.fixture
def mock_partial_guild() -> guilds.PartialGuild:
    return guilds.PartialGuild(
        app=mock.Mock(), id=snowflakes.Snowflake(123), icon_hash="partial_guild_icon_hash", name="partial_guild"
    )


def make_guild_text_channel(id: int) -> channels.GuildTextChannel:
    return channels.GuildTextChannel(
        app=mock.Mock(),
        id=snowflakes.Snowflake(id),
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
def mock_guild_text_channel() -> channels.GuildTextChannel:
    return make_guild_text_channel(4560)


@pytest.fixture
def mock_dm_channel() -> channels.DMChannel:
    return channels.DMChannel(
        app=mock.Mock(),
        id=snowflakes.Snowflake(4561),
        name="dm_channel_name",
        type=channels.ChannelType.DM,
        last_message_id=None,
        recipient=mock.Mock(),
    )


@pytest.fixture
def mock_guild_voice_channel(
    mock_guild_category: channels.GuildCategory, mock_partial_guild: guilds.PartialGuild
) -> channels.GuildVoiceChannel:
    return channels.GuildVoiceChannel(
        app=mock.Mock(),
        id=snowflakes.Snowflake(4562),
        name="guild_voice_channel_name",
        type=channels.ChannelType.GUILD_VOICE,
        guild_id=mock_partial_guild.id,
        parent_id=mock_guild_category.id,
        position=0,
        is_nsfw=False,
        permission_overwrites={},
        bitrate=1,
        region=None,
        user_limit=0,
        video_quality_mode=0,
        last_message_id=None,
    )


@pytest.fixture
def mock_guild_category(mock_partial_guild: guilds.PartialGuild) -> channels.GuildCategory:
    return channels.GuildCategory(
        app=mock.Mock(),
        id=snowflakes.Snowflake(4564),
        name="guild_category_name",
        type=channels.ChannelType.GUILD_CATEGORY,
        guild_id=mock_partial_guild.id,
        parent_id=None,
        position=0,
        is_nsfw=False,
        permission_overwrites={},
    )


@pytest.fixture
def mock_guild_news_channel(
    mock_partial_guild: guilds.PartialGuild, mock_guild_category: channels.GuildCategory
) -> channels.GuildNewsChannel:
    return channels.GuildNewsChannel(
        app=mock.Mock(),
        id=snowflakes.Snowflake(4565),
        name="guild_news_channel_name",
        type=channels.ChannelType.GUILD_NEWS,
        guild_id=mock_partial_guild.id,
        parent_id=mock_guild_category.id,
        position=1,
        is_nsfw=False,
        permission_overwrites={},
        topic="guild_news_channel_topic",
        last_message_id=None,
        last_pin_timestamp=datetime.datetime.fromtimestamp(1),
        default_auto_archive_duration=datetime.timedelta(1),
    )


@pytest.fixture
def mock_guild_public_thread_channel(
    mock_partial_guild: guilds.PartialGuild, mock_guild_text_channel: channels.GuildTextChannel, mock_user: users.User
) -> channels.GuildThreadChannel:
    return channels.GuildThreadChannel(
        app=mock.Mock(),
        id=snowflakes.Snowflake(45611),
        name="guild_public_thread_channel_name",
        type=channels.ChannelType.GUILD_PUBLIC_THREAD,
        guild_id=mock_partial_guild.id,
        parent_id=mock_guild_text_channel.id,
        last_message_id=None,
        last_pin_timestamp=datetime.datetime.fromtimestamp(1),
        rate_limit_per_user=datetime.timedelta(1),
        approximate_message_count=1,
        approximate_member_count=1,
        is_archived=False,
        auto_archive_duration=datetime.timedelta(1),
        archive_timestamp=datetime.datetime.fromtimestamp(10),
        is_locked=True,
        member=None,
        owner_id=mock_user.id,
        thread_created_at=None,
    )


@pytest.fixture
def mock_guild_stage_channel(
    mock_partial_guild: guilds.PartialGuild, mock_guild_category: channels.GuildCategory, mock_user: users.User
) -> channels.GuildStageChannel:
    return channels.GuildStageChannel(
        app=mock.Mock(),
        id=snowflakes.Snowflake(45613),
        name="guild_news_channel_name",
        type=channels.ChannelType.GUILD_STAGE,
        guild_id=mock_partial_guild.id,
        parent_id=mock_guild_category.id,
        position=1,
        is_nsfw=False,
        permission_overwrites={},
        last_message_id=None,
        bitrate=1,
        region=None,
        user_limit=1,
        video_quality_mode=channels.VideoQualityMode.FULL,
    )


def make_user(id: int) -> users.User:
    return users.UserImpl(
        id=snowflakes.Snowflake(id),
        app=mock.Mock(),
        discriminator="0",
        username="user_username",
        global_name="user_global_name",
        avatar_hash="user_avatar_hash",
        banner_hash="user_banner_hash",
        avatar_decoration=None,
        accent_color=None,
        is_bot=False,
        is_system=False,
        flags=users.UserFlag.NONE,
    )


@pytest.fixture
def mock_user() -> users.User:
    return make_user(789)


def make_mock_message(id: int) -> messages.Message:
    return messages.Message(
        id=snowflakes.Snowflake(id),
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
def mock_message() -> messages.Message:
    return make_mock_message(101)


def make_partial_webhook(id: int) -> webhooks.PartialWebhook:
    return webhooks.PartialWebhook(
        app=mock.Mock(),
        id=snowflakes.Snowflake(id),
        type=webhooks.WebhookType.APPLICATION,
        name="partial_webhook_name",
        avatar_hash="partial_webhook_avatar_hash",
        application_id=None,
    )


@pytest.fixture
def mock_partial_webhook() -> webhooks.PartialWebhook:
    return make_partial_webhook(112)


@pytest.fixture
def mock_application() -> applications.Application:
    return applications.Application(
        id=snowflakes.Snowflake(111),
        name="application_name",
        description="application_description",
        icon_hash="application_icon_hash",
        app=mock.Mock(),
        is_bot_public=False,
        is_bot_code_grant_required=False,
        owner=mock.Mock(),
        rpc_origins=None,
        flags=applications.ApplicationFlags.EMBEDDED,
        public_key=b"application_key",
        team=None,
        cover_image_hash="application_cover_image_hash",
        terms_of_service_url=None,
        privacy_policy_url=None,
        role_connections_verification_url=None,
        custom_install_url=None,
        tags=[],
        install_parameters=None,
        approximate_guild_count=0,
        integration_types_config={},
    )


@pytest.fixture
def mock_partial_sticker() -> stickers.PartialSticker:
    return stickers.PartialSticker(
        id=snowflakes.Snowflake(222), name="sticker_name", format_type=stickers.StickerFormatType.PNG
    )


def make_invite_with_metadata(code: str) -> invites.InviteWithMetadata:
    return invites.InviteWithMetadata(
        app=mock.Mock(),
        code=code,
        guild=None,
        guild_id=None,
        channel_id=snowflakes.Snowflake(456),
        inviter=None,
        channel=None,
        target_type=invites.TargetType.STREAM,
        target_user=None,
        target_application=None,
        approximate_active_member_count=None,
        approximate_member_count=None,
        expires_at=None,
        uses=1,
        max_uses=None,
        max_age=None,
        is_temporary=False,
        created_at=datetime.datetime.fromtimestamp(0),
    )


@pytest.fixture
def mock_invite_with_metadata() -> invites.InviteWithMetadata:
    return make_invite_with_metadata("invite_with_metadata_name")


def make_partial_role(id: int) -> guilds.PartialRole:
    return guilds.PartialRole(app=mock.Mock(), id=snowflakes.Snowflake(id), name="partial_role_name")


@pytest.fixture
def mock_partial_role() -> guilds.PartialRole:
    return make_partial_role(333)


def make_custom_emoji(id: int) -> emojis.CustomEmoji:
    return emojis.CustomEmoji(id=snowflakes.Snowflake(id), name="custom_emoji_name", is_animated=False)


@pytest.fixture
def mock_custom_emoji() -> emojis.CustomEmoji:
    return make_custom_emoji(4440)


def make_unicode_emoji(emoji: str) -> emojis.UnicodeEmoji:
    return emojis.UnicodeEmoji(emoji)


@pytest.fixture
def mock_unicode_emoji() -> emojis.UnicodeEmoji:
    return make_unicode_emoji("🙂")


def make_permission_overwrite(id: int) -> channels.PermissionOverwrite:
    return channels.PermissionOverwrite(id=snowflakes.Snowflake(id), type=channels.PermissionOverwriteType.MEMBER)


@pytest.fixture
def mock_permission_overwrite() -> channels.PermissionOverwrite:
    return make_permission_overwrite(555)


@pytest.fixture
def mock_partial_command(mock_application: applications.Application) -> commands.PartialCommand:
    return commands.PartialCommand(
        app=mock.Mock(),
        id=snowflakes.Snowflake(666),
        type=commands.CommandType.SLASH,
        application_id=mock_application.id,
        name="partial_command_name",
        default_member_permissions=permissions.Permissions.NONE,
        is_nsfw=False,
        guild_id=None,
        version=snowflakes.Snowflake(1),
        name_localizations={},
        integration_types=[],
        context_types=[],
    )


@pytest.fixture
def mock_partial_interaction(mock_application: applications.Application) -> interactions.PartialInteraction:
    return interactions.PartialInteraction(
        app=mock.Mock(),
        id=snowflakes.Snowflake(777),
        application_id=mock_application.id,
        type=interactions.InteractionType.APPLICATION_COMMAND,
        token="partial_interaction_token",
        version=1,
        context=applications.ApplicationContextType.GUILD,
        authorizing_integration_owners={},
    )


@pytest.fixture
def mock_scheduled_event(mock_partial_guild: guilds.PartialGuild) -> scheduled_events.ScheduledEvent:
    return scheduled_events.ScheduledEvent(
        app=mock.Mock(),
        id=snowflakes.Snowflake(888),
        guild_id=mock_partial_guild.id,
        name="scheduled_event_name",
        description="scheduled_event_description",
        start_time=datetime.datetime.fromtimestamp(1),
        end_time=None,
        privacy_level=scheduled_events.EventPrivacyLevel.GUILD_ONLY,
        status=scheduled_events.ScheduledEventStatus.ACTIVE,
        entity_type=scheduled_events.ScheduledEventType.VOICE,
        creator=None,
        user_count=None,
        image_hash="scheduled_event_image_hash",
    )


class TestStringifyHttpMessage:
    def test_when_body_is_str(self, rest_client: rest.RESTClientImpl):
        headers = {"HEADER1": "value1", "HEADER2": "value2", "Authorization": "this will never see the light of day"}

        returned = rest._stringify_http_message(headers, None)

        assert returned == "    HEADER1: value1\n    HEADER2: value2\n    Authorization: **REDACTED TOKEN**"

    def test_when_body_is_not_None(self, rest_client: rest.RESTClientImpl):
        headers = {"HEADER1": "value1", "HEADER2": "value2", "Authorization": "this will never see the light of day"}

        returned = rest._stringify_http_message(headers, bytes("hello :)", "ascii"))

        assert returned == (
            f"    HEADER1: value1\n    HEADER2: value2\n    Authorization: **REDACTED TOKEN**\n\n    hello :)"
        )


class TestTransformEmojiToUrlFormat:
    @pytest.mark.parametrize(
        ("emoji", "expected_return"),
        [
            (emojis.CustomEmoji(id=snowflakes.Snowflake(123), name="rooYay", is_animated=False), "rooYay:123"),
            ("\N{OK HAND SIGN}", "\N{OK HAND SIGN}"),
            (emojis.UnicodeEmoji("\N{OK HAND SIGN}"), "\N{OK HAND SIGN}"),
        ],
    )
    def test_expected(self, emoji: emojis.Emoji, expected_return: str):
        assert rest._transform_emoji_to_url_format(emoji, undefined.UNDEFINED) == expected_return

    def test_with_id(self):
        assert rest._transform_emoji_to_url_format("rooYay", 123) == "rooYay:123"

    @pytest.mark.parametrize(
        "emoji",
        [
            emojis.CustomEmoji(id=snowflakes.Snowflake(123), name="rooYay", is_animated=False),
            emojis.UnicodeEmoji("\N{OK HAND SIGN}"),
        ],
    )
    def test_when_id_passed_with_emoji_object(self, emoji: emojis.Emoji):
        with pytest.raises(ValueError, match="emoji_id shouldn't be passed when an Emoji object is passed for emoji"):
            rest._transform_emoji_to_url_format(emoji, 123)


class TestRESTClientImpl:
    def test__init__when_max_retries_over_5(self):
        with pytest.raises(ValueError, match="'max_retries' must be below or equal to 5"):
            rest.RESTClientImpl(
                max_retries=10,
                cache=None,
                http_settings=mock.Mock(),
                max_rate_limit=float("inf"),
                proxy_settings=mock.Mock(),
                token=mock.Mock(rest_api.TokenStrategy),
                token_type="ooga booga",
                rest_url=None,
                executor=None,
                entity_factory=mock.Mock(),
            )

    def test__init__when_token_strategy_passed_with_token_type(self):
        with pytest.raises(ValueError, match="Token type should be handled by the token strategy"):
            rest.RESTClientImpl(
                cache=None,
                http_settings=mock.Mock(),
                max_rate_limit=float("inf"),
                proxy_settings=mock.Mock(),
                token=mock.Mock(rest_api.TokenStrategy),
                token_type="ooga booga",
                rest_url=None,
                executor=None,
                entity_factory=mock.Mock(),
            )

    def test__init__when_token_strategy_passed(self):
        mock_strategy = mock.Mock(rest_api.TokenStrategy)
        obj = rest.RESTClientImpl(
            cache=None,
            http_settings=mock.Mock(),
            max_rate_limit=float("inf"),
            proxy_settings=mock.Mock(),
            token=mock_strategy,
            token_type=None,
            rest_url=None,
            executor=None,
            entity_factory=mock.Mock(),
        )

        assert obj._token is mock_strategy
        assert obj._token_type is mock_strategy.token_type

    def test__init__when_token_is_None_sets_token_to_None(self):
        obj = rest.RESTClientImpl(
            cache=None,
            http_settings=mock.Mock(),
            max_rate_limit=float("inf"),
            proxy_settings=mock.Mock(),
            token=None,
            token_type=None,
            rest_url=None,
            executor=None,
            entity_factory=mock.Mock(),
        )
        assert obj._token is None
        assert obj._token_type is None

    def test__init__when_token_and_token_type_is_not_None_generates_token_with_type(self):
        obj = rest.RESTClientImpl(
            cache=None,
            http_settings=mock.Mock(),
            max_rate_limit=float("inf"),
            proxy_settings=mock.Mock(),
            token="some_token",
            token_type="tYpe",
            rest_url=None,
            executor=None,
            entity_factory=mock.Mock(),
        )
        assert obj._token == "Type some_token"
        assert obj._token_type == "Type"

    def test__init__when_token_provided_as_string_without_type(self):
        with pytest.raises(ValueError, match="Token type required when a str is passed for `token`"):
            rest.RESTClientImpl(
                cache=None,
                http_settings=mock.Mock(),
                max_rate_limit=float("inf"),
                proxy_settings=mock.Mock(),
                token="some_token",
                token_type=None,
                rest_url=None,
                executor=None,
                entity_factory=mock.Mock(),
            )

    def test__init__when_rest_url_is_None_generates_url_using_default_url(self):
        obj = rest.RESTClientImpl(
            cache=None,
            http_settings=mock.Mock(),
            max_rate_limit=float("inf"),
            proxy_settings=mock.Mock(),
            token=None,
            token_type=None,
            rest_url=None,
            executor=None,
            entity_factory=mock.Mock(),
        )
        assert obj._rest_url == urls.REST_API_URL

    def test__init__when_rest_url_is_not_None_generates_url_using_given_url(self):
        obj = rest.RESTClientImpl(
            cache=None,
            http_settings=mock.Mock(),
            max_rate_limit=float("inf"),
            proxy_settings=mock.Mock(),
            token=None,
            token_type=None,
            rest_url="https://some.where/api/v2",
            executor=None,
            entity_factory=mock.Mock(),
        )
        assert obj._rest_url == "https://some.where/api/v2"

    def test___enter__(self, rest_client: rest.RESTClientImpl):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            rest_client.__enter__()

    def test___exit__(self, rest_client: rest.RESTClientImpl):
        try:
            rest_client.__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)

    @pytest.mark.parametrize(("attributes", "expected_result"), [(None, False), (mock.Mock(), True)])
    def test_is_alive_property(
        self, rest_client: rest.RESTClientImpl, attributes: object | None, expected_result: bool
    ):
        with mock.patch.object(rest_client, "_close_event", attributes):
            assert rest_client.is_alive is expected_result

    def test_entity_factory_property(self, rest_client: rest.RESTClientImpl):
        assert rest_client.entity_factory is rest_client._entity_factory

    def test_http_settings_property(self, rest_client: rest.RESTClientImpl):
        mock_http_settings = mock.Mock()

        with mock.patch.object(rest_client, "_http_settings", mock_http_settings):
            assert rest_client.http_settings is mock_http_settings

    def test_proxy_settings_property(self, rest_client: rest.RESTClientImpl):
        mock_proxy_settings = mock.Mock()

        with mock.patch.object(rest_client, "_proxy_settings", mock_proxy_settings):
            assert rest_client.proxy_settings is mock_proxy_settings

    def test_token_type_property(self, rest_client: rest.RESTClientImpl):
        mock_type = mock.Mock()

        with mock.patch.object(rest_client, "_token_type", mock_type):
            assert rest_client.token_type is mock_type

    @pytest.mark.parametrize("client_session_owner", [True, False])
    @pytest.mark.parametrize("bucket_manager_owner", [True, False])
    @pytest.mark.asyncio
    async def test_close(
        self, rest_client: rest.RESTClientImpl, client_session_owner: bool, bucket_manager_owner: bool
    ):
        rest_client._close_event = mock_close_event = mock.Mock()
        rest_client._client_session_owner = client_session_owner
        rest_client._bucket_manager_owner = bucket_manager_owner

        with (
            mock.patch.object(rest_client._client_session, "close", mock.AsyncMock()) as patched__client_session_close,
            mock.patch.object(rest_client, "_bucket_manager") as patched__bucket_manager,
            mock.patch.object(patched__bucket_manager, "close", mock.AsyncMock()) as patched__bucket_manager_close,
        ):
            await rest_client.close()

        mock_close_event.set.assert_called_once_with()
        assert rest_client._close_event is None

        if client_session_owner:
            patched__client_session_close.assert_awaited_once_with()
            assert rest_client._client_session is None
        else:
            patched__client_session_close.assert_not_called()
            assert rest_client._client_session is not None

        if bucket_manager_owner:
            patched__bucket_manager_close.assert_awaited_once_with()
        else:
            patched__bucket_manager.assert_not_called()

    @pytest.mark.parametrize("client_session_owner", [True, False])
    @pytest.mark.parametrize("bucket_manager_owner", [True, False])
    @pytest.mark.asyncio  # Function needs to be executed in a running loop
    async def test_start(
        self, rest_client: rest.RESTClientImpl, client_session_owner: bool, bucket_manager_owner: bool
    ):
        rest_client._client_session = None
        rest_client._close_event = None
        rest_client._bucket_manager = mock.Mock()
        rest_client._client_session_owner = client_session_owner
        rest_client._bucket_manager_owner = bucket_manager_owner

        with (
            mock.patch.object(net, "create_client_session") as create_client_session,
            mock.patch.object(net, "create_tcp_connector") as create_tcp_connector,
            mock.patch.object(asyncio, "Event") as event,
        ):
            rest_client.start()

        assert rest_client._close_event is event.return_value

        if client_session_owner:
            create_tcp_connector.assert_called_once_with(rest_client._http_settings)
            create_client_session.assert_called_once_with(
                connector=create_tcp_connector.return_value,
                connector_owner=True,
                http_settings=rest_client._http_settings,
                raise_for_status=False,
                trust_env=rest_client._proxy_settings.trust_env,
            )
            assert rest_client._client_session is create_client_session.return_value
        else:
            assert rest_client._client_session is None

        if bucket_manager_owner:
            rest_client._bucket_manager.start.assert_called_once_with()
        else:
            rest_client._bucket_manager.start.assert_not_called()

    def test_start_when_active(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(rest_client, "_close_event"), pytest.raises(errors.ComponentStateConflictError):
            rest_client.start()

    #######################
    # Non-async endpoints #
    #######################

    def test_trigger_typing(self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "TypingIndicator", return_value=stub_iterator) as typing_indicator:
            assert rest_client.trigger_typing(mock_guild_text_channel) == stub_iterator

            typing_indicator.assert_called_once_with(
                request_call=rest_client._request,
                channel=mock_guild_text_channel,
                rest_close_event=rest_client._close_event,
            )

    @pytest.mark.parametrize(
        "before",
        [
            datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc),
            make_user(735757641938108416),
        ],
    )
    def test_fetch_messages_with_before(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        before: datetime.datetime | users.User,
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(mock_guild_text_channel, before=before) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=mock_guild_text_channel,
                direction="before",
                first_id="735757641938108416",
            )

    @pytest.mark.parametrize(
        "after",
        [
            datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc),
            make_user(735757641938108416),
        ],
    )
    def test_fetch_messages_with_after(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        after: datetime.datetime | users.User,
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(mock_guild_text_channel, after=after) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=mock_guild_text_channel,
                direction="after",
                first_id="735757641938108416",
            )

    @pytest.mark.parametrize(
        "around",
        [
            datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc),
            make_user(735757641938108416),
        ],
    )
    def test_fetch_messages_with_around(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        around: datetime.datetime | users.User,
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(mock_guild_text_channel, around=around) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=mock_guild_text_channel,
                direction="around",
                first_id="735757641938108416",
            )

    def test_fetch_messages_with_default(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(mock_guild_text_channel) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=mock_guild_text_channel,
                direction="before",
                first_id=undefined.UNDEFINED,
            )

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"before": 1234, "after": 1234},
            {"after": 1234, "around": 1234},
            {"before": 1234, "around": 1234},
            {"before": 1234, "after": 1234, "around": 1234},
        ],
    )
    def test_fetch_messages_when_more_than_one_kwarg_passed(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        kwargs: dict[str, int],
    ):
        with pytest.raises(TypeError):
            rest_client.fetch_messages(mock_guild_text_channel, **kwargs)

    def test_fetch_reactions_for_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "ReactorIterator", return_value=stub_iterator) as iterator:
            with mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"):
                assert (
                    rest_client.fetch_reactions_for_emoji(mock_guild_text_channel, mock_message, "<:rooYay:123>")
                    == stub_iterator
                )

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=mock_guild_text_channel,
                message=mock_message,
                emoji="rooYay:123",
            )

    def test_fetch_my_guilds_when_start_at_is_undefined(self, rest_client: rest.RESTClientImpl):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "OwnGuildIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_my_guilds() == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                newest_first=False,
                first_id="0",
            )

    def test_fetch_my_guilds_when_start_at_is_datetime(self, rest_client: rest.RESTClientImpl):
        stub_iterator = mock.Mock()
        datetime_obj = datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc)

        with mock.patch.object(special_endpoints, "OwnGuildIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_my_guilds(start_at=datetime_obj) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                newest_first=False,
                first_id="735757641938108416",
            )

    def test_fetch_my_guilds_when_start_at_is_else(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "OwnGuildIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_my_guilds(newest_first=True, start_at=mock_partial_guild) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                newest_first=True,
                first_id="123",
            )

    def test_guild_builder(self, rest_client: rest.RESTClientImpl):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "GuildBuilder", return_value=stub_iterator) as iterator:
            assert rest_client.guild_builder("hikari") == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                executor=rest_client._executor,
                request_call=rest_client._request,
                name="hikari",
            )

    def test_fetch_audit_log_when_before_is_undefined(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "AuditLogIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_audit_log(mock_partial_guild) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                guild=mock_partial_guild,
                before=undefined.UNDEFINED,
                user=undefined.UNDEFINED,
                action_type=undefined.UNDEFINED,
            )

    def test_fetch_audit_log_when_before_datetime(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        stub_iterator = mock.Mock()
        datetime_obj = datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc)

        with mock.patch.object(special_endpoints, "AuditLogIterator", return_value=stub_iterator) as iterator:
            returned = rest_client.fetch_audit_log(
                mock_partial_guild,
                user=mock_user,
                before=datetime_obj,
                event_type=audit_logs.AuditLogEventType.GUILD_UPDATE,
            )
            assert returned is stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                guild=mock_partial_guild,
                before="735757641938108416",
                user=mock_user,
                action_type=audit_logs.AuditLogEventType.GUILD_UPDATE,
            )

    def test_fetch_audit_log_when_before_is_else(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "AuditLogIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_audit_log(mock_partial_guild, before=mock_user) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                guild=mock_partial_guild,
                before="789",
                user=undefined.UNDEFINED,
                action_type=undefined.UNDEFINED,
            )

    def test_fetch_public_archived_threads(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        mock_datetime = time.utc_datetime()
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_public_archived_threads(mock_guild_text_channel, before=mock_datetime)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client._deserialize_public_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PUBLIC_ARCHIVED_THREADS.compile(channel=4560),
            before=mock_datetime.isoformat(),
            before_is_timestamp=True,
        )

    def test_fetch_public_archived_threads_when_before_not_specified(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_public_archived_threads(mock_guild_text_channel)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client._deserialize_public_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PUBLIC_ARCHIVED_THREADS.compile(channel=4560),
            before=undefined.UNDEFINED,
            before_is_timestamp=True,
        )

    def test_fetch_private_archived_threads(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        mock_datetime = time.utc_datetime()
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_private_archived_threads(mock_guild_text_channel, before=mock_datetime)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PRIVATE_ARCHIVED_THREADS.compile(channel=4560),
            before=mock_datetime.isoformat(),
            before_is_timestamp=True,
        )

    def test_fetch_private_archived_threads_when_before_not_specified(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_private_archived_threads(mock_guild_text_channel)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PRIVATE_ARCHIVED_THREADS.compile(channel=4560),
            before=undefined.UNDEFINED,
            before_is_timestamp=True,
        )

    @pytest.mark.parametrize(
        "before", [datetime.datetime(2022, 2, 28, 10, 58, 30, 987193, tzinfo=datetime.timezone.utc), 947809989634818048]
    )
    def test_fetch_joined_private_archived_threads(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        before: typing.Union[datetime.datetime, snowflakes.Snowflake],
    ):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_joined_private_archived_threads(mock_guild_text_channel, before=before)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_JOINED_PRIVATE_ARCHIVED_THREADS.compile(channel=4560),
            before="947809989634818048",
            before_is_timestamp=False,
        )

    def test_fetch_joined_private_archived_threads_when_before_not_specified(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_joined_private_archived_threads(mock_guild_text_channel)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_JOINED_PRIVATE_ARCHIVED_THREADS.compile(channel=4560),
            before=undefined.UNDEFINED,
            before_is_timestamp=False,
        )

    def test_fetch_members(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MemberIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_members(mock_partial_guild) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory, request_call=rest_client._request, guild=mock_partial_guild
            )

    def test_kick_member(self, rest_client: rest.RESTClientImpl):
        mock_kick_user = mock.Mock()
        rest_client.kick_user = mock_kick_user

        result = rest_client.kick_member(123, 5423, reason="oewkwkwk")

        assert result is mock_kick_user.return_value
        mock_kick_user.assert_called_once_with(123, 5423, reason="oewkwkwk")

    def test_ban_member(self, rest_client: rest.RESTClientImpl):
        mock_ban_user = mock.Mock()
        rest_client.ban_user = mock_ban_user

        result = rest_client.ban_member(43123, 54123, delete_message_seconds=518400, reason="wowowowo")

        assert result is mock_ban_user.return_value
        mock_ban_user.assert_called_once_with(43123, 54123, delete_message_seconds=518400, reason="wowowowo")

    def test_unban_member(self, rest_client: rest.RESTClientImpl):
        mock_unban_user = mock.Mock()
        rest_client.unban_user = mock_unban_user

        reason = rest_client.unban_member(123, 321, reason="ayaya")

        assert reason is mock_unban_user.return_value
        mock_unban_user.assert_called_once_with(123, 321, reason="ayaya")

    def test_fetch_bans(self, rest_client: rest.RESTClientImpl, mock_user: users.User):
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(123, newest_first=True, start_at=mock_user)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, 123, newest_first=True, first_id="789"
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_bans_when_datetime_for_start_at(self, rest_client: rest.RESTClientImpl):
        start_at = datetime.datetime(2022, 3, 6, 12, 1, 58, 415625, tzinfo=datetime.timezone.utc)
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(9000, newest_first=True, start_at=start_at)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, 9000, newest_first=True, first_id="950000286338908160"
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_bans_when_start_at_undefined(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(8844)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory,
            rest_client._request,
            8844,
            newest_first=False,
            first_id=str(snowflakes.Snowflake.min()),
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_bans_when_start_at_undefined_and_newest_first(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(3848, newest_first=True)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory,
            rest_client._request,
            3848,
            newest_first=True,
            first_id=str(snowflakes.Snowflake.max()),
        )
        assert iterator is iterator_cls.return_value

    def test_slash_command_builder(self, rest_client: rest.RESTClientImpl):
        result = rest_client.slash_command_builder("a name", "a description")
        assert isinstance(result, special_endpoints.SlashCommandBuilder)

    def test_context_menu_command_command_builder(self, rest_client: rest.RESTClientImpl):
        result = rest_client.context_menu_command_builder(3, "a name")
        assert isinstance(result, special_endpoints.ContextMenuCommandBuilder)
        assert result.type == commands.CommandType.MESSAGE

    def test_build_message_action_row(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "MessageActionRowBuilder") as action_row_builder:
            assert rest_client.build_message_action_row() is action_row_builder.return_value

        action_row_builder.assert_called_once_with()

    def test_build_modal_action_row(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "ModalActionRowBuilder") as action_row_builder:
            assert rest_client.build_modal_action_row() is action_row_builder.return_value

        action_row_builder.assert_called_once_with()

    def test__build_message_payload_with_undefined_args(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(
            mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1}
        ) as generate_allowed_mentions:
            body, form = rest_client._build_message_payload()

        assert body == {"allowed_mentions": {"allowed_mentions": 1}}
        assert form is None

        generate_allowed_mentions.assert_called_once_with(
            undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED
        )

    @pytest.mark.parametrize("args", [("embeds", "components", "attachments"), ("embed", "component", "attachment")])
    def test__build_message_payload_with_None_args(self, rest_client: rest.RESTClientImpl, args: tuple[str, str, str]):
        kwargs: dict[str, typing.Any] = {}
        for arg in args:
            kwargs[arg] = None

        with mock.patch.object(
            mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1}
        ) as generate_allowed_mentions:
            body, form = rest_client._build_message_payload(**kwargs)

        assert body == {"embeds": [], "components": [], "attachments": [], "allowed_mentions": {"allowed_mentions": 1}}
        assert form is None

        generate_allowed_mentions.assert_called_once_with(
            undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED
        )

    def test__build_message_payload_with_edit_and_all_mentions_undefined(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(mentions, "generate_allowed_mentions") as generate_allowed_mentions:
            body, form = rest_client._build_message_payload(edit=True)

        assert body == {}
        assert form is None

        generate_allowed_mentions.assert_not_called()

    def test__build_message_payload_embed_content_syntactic_sugar(self, rest_client: rest.RESTClientImpl):
        embed = mock.Mock(embeds.Embed)

        with (
            mock.patch.object(
                rest_client.entity_factory, "serialize_embed", return_value=({"embed": 1}, [])
            ) as patched_serialize_embed,
            mock.patch.object(
                mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1}
            ) as generate_allowed_mentions,
        ):
            body, form = rest_client._build_message_payload(content=embed)

        # Returned
        assert body == {"embeds": [{"embed": 1}], "allowed_mentions": {"allowed_mentions": 1}}
        assert form is None

        # Embeds
        patched_serialize_embed.assert_called_once_with(embed)

        # Generate allowed mentions
        generate_allowed_mentions.assert_called_once_with(
            undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED
        )

    def test__build_message_payload_attachment_content_syntactic_sugar(self, rest_client: rest.RESTClientImpl):
        attachment = mock.Mock(files.Resource)
        resource_attachment = mock.Mock(filename="attachment.png")

        with (
            mock.patch.object(files, "ensure_resource", return_value=resource_attachment) as ensure_resource,
            mock.patch.object(
                mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1}
            ) as generate_allowed_mentions,
            mock.patch.object(data_binding, "URLEncodedFormBuilder") as url_encoded_form,
        ):
            body, form = rest_client._build_message_payload(content=attachment)

        # Returned
        assert body == {
            "allowed_mentions": {"allowed_mentions": 1},
            "attachments": [{"id": 0, "filename": "attachment.png"}],
        }
        assert form is url_encoded_form.return_value

        # Attachments
        ensure_resource.assert_called_once_with(attachment)

        # Generate allowed mentions
        generate_allowed_mentions.assert_called_once_with(
            undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED
        )

        # Form builder
        url_encoded_form.assert_called_once_with()
        url_encoded_form.return_value.add_resource.assert_called_once_with("files[0]", resource_attachment)

    def test__build_message_payload_with_singular_args(
        self, rest_client: rest.RESTClientImpl, mock_partial_sticker: stickers.PartialSticker
    ):
        attachment = mock.Mock()
        resource_attachment1 = mock.Mock(filename="attachment.png")
        resource_attachment2 = mock.Mock(filename="attachment2.png")
        component = mock.Mock(build=mock.Mock(return_value={"component": 1}))
        embed = mock.Mock()
        embed_attachment = mock.Mock()
        mentions_everyone = mock.Mock()
        mentions_reply = mock.Mock()
        user_mentions = mock.Mock()
        role_mentions = mock.Mock()

        with (
            mock.patch.object(
                rest_client.entity_factory, "serialize_embed", return_value=({"embed": 1}, [embed_attachment])
            ) as patched_serialize_embed,
            mock.patch.object(
                files, "ensure_resource", side_effect=[resource_attachment1, resource_attachment2]
            ) as ensure_resource,
            mock.patch.object(
                mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1}
            ) as generate_allowed_mentions,
            mock.patch.object(data_binding, "URLEncodedFormBuilder") as url_encoded_form,
        ):
            body, form = rest_client._build_message_payload(
                content=987654321,
                attachment=attachment,
                component=component,
                embed=embed,
                sticker=mock_partial_sticker,
                flags=120,
                tts=True,
                mentions_everyone=mentions_everyone,
                mentions_reply=mentions_reply,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )

        # Returned
        assert body == {
            "content": "987654321",
            "tts": True,
            "flags": 120,
            "sticker_ids": ["222"],
            "embeds": [{"embed": 1}],
            "components": [{"component": 1}],
            "attachments": [{"id": 0, "filename": "attachment.png"}, {"id": 1, "filename": "attachment2.png"}],
            "allowed_mentions": {"allowed_mentions": 1},
        }
        assert form is url_encoded_form.return_value

        # Attachments
        assert ensure_resource.call_count == 2
        ensure_resource.assert_has_calls([mock.call(attachment), mock.call(embed_attachment)])

        # Embeds
        patched_serialize_embed.assert_called_once_with(embed)

        # Components
        component.build.assert_called_once_with()

        # Generate allowed mentions
        generate_allowed_mentions.assert_called_once_with(
            mentions_everyone, mentions_reply, user_mentions, role_mentions
        )

        # Form builder
        url_encoded_form.assert_called_once_with()
        assert url_encoded_form.return_value.add_resource.call_count == 2
        url_encoded_form.return_value.add_resource.assert_has_calls(
            [mock.call("files[0]", resource_attachment1), mock.call("files[1]", resource_attachment2)]
        )

    def test__build_message_payload_with_plural_args(
        self, rest_client: rest.RESTClientImpl, mock_partial_sticker: stickers.PartialSticker
    ):
        attachment1 = mock.Mock()
        attachment2 = mock.Mock(messages.Attachment, id=123, filename="attachment123.png")
        resource_attachment1 = mock.Mock(filename="attachment.png")
        resource_attachment2 = mock.Mock(filename="attachment2.png")
        resource_attachment3 = mock.Mock(filename="attachment3.png")
        resource_attachment4 = mock.Mock(filename="attachment4.png")
        resource_attachment5 = mock.Mock(filename="attachment5.png")
        resource_attachment6 = mock.Mock(filename="attachment6.png")
        component1 = mock.Mock(build=mock.Mock(return_value={"component": 1}))
        component2 = mock.Mock(build=mock.Mock(return_value={"component": 2}))
        embed1 = mock.Mock()
        embed2 = mock.Mock()
        embed_attachment1 = mock.Mock()
        embed_attachment2 = mock.Mock()
        embed_attachment3 = mock.Mock()
        embed_attachment4 = mock.Mock()
        mentions_everyone = mock.Mock()
        mentions_reply = mock.Mock()
        user_mentions = mock.Mock()
        role_mentions = mock.Mock()

        serialize_embed_side_effect = [
            ({"embed": 1}, [embed_attachment1, embed_attachment2]),
            ({"embed": 2}, [embed_attachment3, embed_attachment4]),
        ]

        with (
            mock.patch.object(
                rest_client.entity_factory, "serialize_embed", side_effect=serialize_embed_side_effect
            ) as patched_serialize_embed,
            mock.patch.object(
                files,
                "ensure_resource",
                side_effect=[
                    resource_attachment1,
                    resource_attachment2,
                    resource_attachment3,
                    resource_attachment4,
                    resource_attachment5,
                    resource_attachment6,
                ],
            ) as ensure_resource,
            mock.patch.object(
                mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1}
            ) as generate_allowed_mentions,
            mock.patch.object(data_binding, "URLEncodedFormBuilder") as url_encoded_form,
        ):
            body, form = rest_client._build_message_payload(
                content=987654321,
                attachments=[attachment1, attachment2],
                components=[component1, component2],
                embeds=[embed1, embed2],
                stickers=[54612123, mock_partial_sticker],
                flags=120,
                tts=True,
                mentions_everyone=mentions_everyone,
                mentions_reply=mentions_reply,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )

        # Returned
        assert body == {
            "content": "987654321",
            "tts": True,
            "flags": 120,
            "embeds": [{"embed": 1}, {"embed": 2}],
            "components": [{"component": 1}, {"component": 2}],
            "sticker_ids": ["54612123", "222"],
            "attachments": [
                {"id": 0, "filename": "attachment.png"},
                {"id": 1, "filename": "attachment2.png"},
                {"id": 2, "filename": "attachment3.png"},
                {"id": 3, "filename": "attachment4.png"},
                {"id": 4, "filename": "attachment5.png"},
                {"id": 5, "filename": "attachment6.png"},
            ],
            "allowed_mentions": {"allowed_mentions": 1},
        }
        assert form is url_encoded_form.return_value

        # Attachments
        assert ensure_resource.call_count == 6
        ensure_resource.assert_has_calls(
            [
                mock.call(attachment1),
                mock.call(attachment2),
                mock.call(embed_attachment1),
                mock.call(embed_attachment2),
                mock.call(embed_attachment3),
                mock.call(embed_attachment4),
            ]
        )

        # Embeds
        assert patched_serialize_embed.call_count == 2
        patched_serialize_embed.assert_has_calls([mock.call(embed1), mock.call(embed2)])

        # Components
        component1.build.assert_called_once_with()
        component2.build.assert_called_once_with()

        # Generate allowed mentions
        generate_allowed_mentions.assert_called_once_with(
            mentions_everyone, mentions_reply, user_mentions, role_mentions
        )

        # Form builder
        url_encoded_form.assert_called_once_with()
        assert url_encoded_form.return_value.add_resource.call_count == 6
        url_encoded_form.return_value.add_resource.assert_has_calls(
            [
                mock.call("files[0]", resource_attachment1),
                mock.call("files[1]", resource_attachment2),
                mock.call("files[2]", resource_attachment3),
                mock.call("files[3]", resource_attachment4),
                mock.call("files[4]", resource_attachment5),
                mock.call("files[5]", resource_attachment6),
            ]
        )

    def test__build_message_payload_with_edit_and_attachment_object_passed(self, rest_client: rest.RESTClientImpl):
        attachment1 = mock.Mock()
        attachment2 = mock.Mock(messages.Attachment, id=123, filename="attachment123.png")
        resource_attachment1 = mock.Mock(filename="attachment.png")
        resource_attachment2 = mock.Mock(filename="attachment2.png")
        resource_attachment3 = mock.Mock(filename="attachment3.png")
        resource_attachment4 = mock.Mock(filename="attachment4.png")
        resource_attachment5 = mock.Mock(filename="attachment5.png")
        component1 = mock.Mock(build=mock.Mock(return_value={"component": 1}))
        component2 = mock.Mock(build=mock.Mock(return_value={"component": 2}))
        embed1 = mock.Mock()
        embed2 = mock.Mock()
        embed_attachment1 = mock.Mock()
        embed_attachment2 = mock.Mock()
        embed_attachment3 = mock.Mock()
        embed_attachment4 = mock.Mock()

        serialize_embed_side_effect = [
            ({"embed": 1}, [embed_attachment1, embed_attachment2]),
            ({"embed": 2}, [embed_attachment3, embed_attachment4]),
        ]

        with (
            mock.patch.object(rest_client.entity_factory, "serialize_embed", side_effect=serialize_embed_side_effect),
            mock.patch.object(
                files,
                "ensure_resource",
                side_effect=[
                    resource_attachment1,
                    resource_attachment2,
                    resource_attachment3,
                    resource_attachment4,
                    resource_attachment5,
                ],
            ) as ensure_resource,
            mock.patch.object(data_binding, "URLEncodedFormBuilder") as url_encoded_form,
        ):
            body, form = rest_client._build_message_payload(
                content=987654321,
                attachments=[attachment1, attachment2],
                components=[component1, component2],
                embeds=[embed1, embed2],
                flags=120,
                tts=True,
                mentions_everyone=undefined.UNDEFINED,
                mentions_reply=undefined.UNDEFINED,
                user_mentions=undefined.UNDEFINED,
                role_mentions=undefined.UNDEFINED,
                edit=True,
            )

        # Returned
        assert body == {
            "content": "987654321",
            "tts": True,
            "flags": 120,
            "embeds": [{"embed": 1}, {"embed": 2}],
            "components": [{"component": 1}, {"component": 2}],
            "attachments": [
                {"id": 0, "filename": "attachment.png"},
                {"id": 123, "filename": "attachment123.png"},
                {"id": 1, "filename": "attachment2.png"},
                {"id": 2, "filename": "attachment3.png"},
                {"id": 3, "filename": "attachment4.png"},
                {"id": 4, "filename": "attachment5.png"},
            ],
        }
        assert form is url_encoded_form.return_value

        # Attachments
        assert ensure_resource.call_count == 5
        ensure_resource.assert_has_calls(
            [
                mock.call(attachment1),
                mock.call(embed_attachment1),
                mock.call(embed_attachment2),
                mock.call(embed_attachment3),
                mock.call(embed_attachment4),
            ]
        )

        # Form builder
        url_encoded_form.assert_called_once_with()
        assert url_encoded_form.return_value.add_resource.call_count == 5
        url_encoded_form.return_value.add_resource.assert_has_calls(
            [
                mock.call("files[0]", resource_attachment1),
                mock.call("files[1]", resource_attachment2),
                mock.call("files[2]", resource_attachment3),
                mock.call("files[3]", resource_attachment4),
                mock.call("files[4]", resource_attachment5),
            ]
        )

    @pytest.mark.parametrize(
        ("singular_arg", "plural_arg"),
        [("attachment", "attachments"), ("component", "components"), ("embed", "embeds"), ("sticker", "stickers")],
    )
    def test__build_message_payload_when_both_single_and_plural_args_passed(
        self, rest_client: rest.RESTClientImpl, singular_arg: str, plural_arg: str
    ):
        with pytest.raises(
            ValueError, match=rf"You may only specify one of '{singular_arg}' or '{plural_arg}', not both"
        ):
            rest_client._build_message_payload(**{singular_arg: mock.Mock(), plural_arg: mock.Mock()})

    def test_interaction_deferred_builder(self, rest_client: rest.RESTClientImpl):
        result = rest_client.interaction_deferred_builder(5)

        assert result.type == 5
        assert isinstance(result, special_endpoints.InteractionDeferredBuilder)

    def test_interaction_autocomplete_builder(self, rest_client: rest.RESTClientImpl):
        result = rest_client.interaction_autocomplete_builder(
            [special_endpoints.AutocompleteChoiceBuilder(name="name", value="value")]
        )

        assert result.choices == [special_endpoints.AutocompleteChoiceBuilder(name="name", value="value")]

    def test_interaction_message_builder(self, rest_client: rest.RESTClientImpl):
        result = rest_client.interaction_message_builder(4)

        assert result.type == 4
        assert isinstance(result, special_endpoints.InteractionMessageBuilder)

    def test_interaction_modal_builder(self, rest_client: rest.RESTClientImpl):
        result = rest_client.interaction_modal_builder("aaaaa", "custom")

        assert result.type == 9
        assert result.title == "aaaaa"
        assert result.custom_id == "custom"

    def test_fetch_scheduled_event_users(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(123, 6666655555, newest_first=True, start_at=mock_user)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, 123, 6666655555, first_id="789", newest_first=True
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_scheduled_event_users_when_datetime_for_start_at(self, rest_client: rest.RESTClientImpl):
        start_at = datetime.datetime(2022, 3, 6, 12, 1, 58, 415625, tzinfo=datetime.timezone.utc)
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(54123, 656324, newest_first=True, start_at=start_at)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory,
            rest_client._request,
            54123,
            656324,
            newest_first=True,
            first_id="950000286338908160",
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_scheduled_event_users_when_start_at_undefined(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(54563245, 123321123)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory,
            rest_client._request,
            54563245,
            123321123,
            newest_first=False,
            first_id=str(snowflakes.Snowflake.min()),
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_scheduled_event_users_when_start_at_undefined_and_newest_first(
        self, rest_client: rest.RESTClientImpl
    ):
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(6423, 65456234, newest_first=True)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory,
            rest_client._request,
            6423,
            65456234,
            newest_first=True,
            first_id=str(snowflakes.Snowflake.max()),
        )
        assert iterator is iterator_cls.return_value


class ExitException(Exception): ...


@pytest.mark.asyncio
class TestRESTClientImplAsync:
    @pytest.fixture
    def exit_exception(self) -> typing.Type[ExitException]:
        return ExitException

    async def test___aenter__and__aexit__(self, rest_client: rest.RESTClientImpl):
        with (
            mock.patch.object(rest_client, "close", new_callable=mock.AsyncMock) as patched_close,
            mock.patch.object(rest_client, "start") as patched_start,
        ):
            async with rest_client as client:
                assert client is rest_client
                patched_start.assert_called_once()
                patched_close.assert_not_called()

            patched_close.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test_perform_request_errors_if_both_json_and_form_builder_passed(self, rest_client: rest.RESTClientImpl):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with pytest.raises(ValueError, match="Can only provide one of 'json' or 'form_builder', not both"):
            await rest_client._perform_request(route, json=mock.Mock(), form_builder=mock.Mock())

    @hikari_test_helpers.timeout()
    async def test_perform_request_builds_json_when_passed(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(data_binding, "JSONPayload") as patched_json_payload,
            mock.patch.object(rest_client, "_token", None),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route, json={"some": "data"})

        patched_json_payload.assert_called_once_with({"some": "data"}, dumps=rest_client._dumps)
        _, kwargs = patched_request.call_args_list[0]
        assert kwargs["data"] is patched_json_payload.return_value

    @hikari_test_helpers.timeout()
    async def test_perform_request_builds_form_when_passed(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_form = mock.AsyncMock()
        mock_stack = mock.AsyncMock()
        mock_stack.__aenter__ = mock_stack

        with (
            mock.patch.object(contextlib, "AsyncExitStack", return_value=mock_stack) as exit_stack,
            mock.patch.object(rest_client, "_token", None),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
        ):
            with pytest.raises(exit_exception):
                await rest_client._perform_request(route, form_builder=mock_form)

        _, kwargs = patched_request.call_args_list[0]
        mock_form.build.assert_awaited_once_with(exit_stack.return_value, executor=rest_client._executor)
        assert kwargs["data"] is mock_form.build.return_value

    @hikari_test_helpers.timeout()
    async def test_perform_request_url_encodes_reason_header(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route, reason="光のenergyが　大地に降りそそぐ")

        _, kwargs = patched_request.call_args_list[0]
        assert kwargs["headers"][rest._X_AUDIT_LOG_REASON_HEADER] == (
            "%E5%85%89%E3%81%AEenergy%E3%81%8C%E3%80%80%E5%A4%"
            "A7%E5%9C%B0%E3%81%AB%E9%99%8D%E3%82%8A%E3%81%9D%E3%81%9D%E3%81%90"
        )

    @hikari_test_helpers.timeout()
    async def test_perform_request_with_strategy_token(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(
                rest_client,
                "_token",
                mock.Mock(rest_api.TokenStrategy, acquire=mock.AsyncMock(return_value="Bearer ok.ok.ok")),
            ),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route)

        _, kwargs = patched_request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"

    @hikari_test_helpers.timeout()
    async def test_perform_request_retries_strategy_once(
        self, rest_client: rest.RESTClientImpl, exit_exception: type[ExitException]
    ):
        class StubResponse:
            status = http.HTTPStatus.UNAUTHORIZED
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value"}

            async def read(self):
                return '{"something": null}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(
                rest_client,
                "_token",
                mock.Mock(
                    rest_api.TokenStrategy,
                    acquire=mock.AsyncMock(side_effect=["Bearer ok.ok.ok", "Bearer ok2.ok2.ok2"]),
                ),
            ),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(
                patched__client_session,
                "request",
                hikari_test_helpers.CopyingAsyncMock(side_effect=[StubResponse(), exit_exception]),
            ) as patched_request,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route)

        _, kwargs = patched_request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"
        _, kwargs = patched_request.call_args_list[1]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok2.ok2.ok2"

    @hikari_test_helpers.timeout()
    async def test_perform_request_raises_after_re_auth_attempt(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        class StubResponse:
            status = http.HTTPStatus.UNAUTHORIZED
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value"}
            real_url = "okokokok"

            async def read(self):
                return '{"something": null}'

            async def json(self):
                return {"something": None}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(
                rest_client,
                "_token",
                mock.Mock(
                    rest_api.TokenStrategy,
                    acquire=mock.AsyncMock(side_effect=["Bearer ok.ok.ok", "Bearer ok2.ok2.ok2"]),
                ),
            ),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(
                patched__client_session,
                "request",
                hikari_test_helpers.CopyingAsyncMock(side_effect=[StubResponse(), StubResponse(), StubResponse()]),
            ) as patched_request,
            pytest.raises(errors.UnauthorizedError),
        ):
            await rest_client._perform_request(route)

        _, kwargs = patched_request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"
        _, kwargs = patched_request.call_args_list[1]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok2.ok2.ok2"

    @hikari_test_helpers.timeout()
    async def test_perform_request_when__token_is_None(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_token", None),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route)

        _, kwargs = patched_request.call_args_list[0]
        assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]

    @hikari_test_helpers.timeout()
    async def test_perform_request_when__token_is_not_None(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_token", "token"),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route)

        _, kwargs = patched_request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "token"

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_no_auth_passed(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_token", "token"),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_bucket_manager") as patched__bucket_manager,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
            mock.patch.object(patched__bucket_manager, "acquire_bucket") as patched_acquire_bucket,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route, auth=None)

        _, kwargs = patched_request.call_args_list[0]
        assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]
        patched_acquire_bucket.assert_called_once_with(route, None)
        # patched_acquire_bucket.return_value.assert_used_once() # FIXME: This is a weird thing because it fails no matter how its fixed. assert_used_once() is also not a function lmao.

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_auth_passed(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_token", "token"),
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_bucket_manager") as patched__bucket_manager,
            mock.patch.object(patched__client_session, "request", side_effect=exit_exception) as patched_request,
            mock.patch.object(patched__bucket_manager, "acquire_bucket") as patched_acquire_bucket,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route, auth="ooga booga")

        _, kwargs = patched_request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "ooga booga"
        patched_acquire_bucket.assert_called_once_with(route, "ooga booga")
        # patched_acquire_bucket.return_value.assert_used_once() # FIXME: This is a weird thing because it fails no matter how its fixed. assert_used_once() is also not a function lmao.

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_is_NO_CONTENT(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_parse_ratelimits", new_callable=mock.AsyncMock, return_value=None),
            mock.patch.object(
                patched__client_session, "request", new_callable=mock.AsyncMock, return_value=StubResponse()
            ),
        ):
            assert (await rest_client._perform_request(route)) is None

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_is_APPLICATION_JSON(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.OK
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value"}

            async def read(self):
                return '{"something": null}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_parse_ratelimits", new_callable=mock.AsyncMock, return_value=None),
            mock.patch.object(
                patched__client_session, "request", new_callable=mock.AsyncMock, return_value=StubResponse()
            ),
        ):
            assert (await rest_client._perform_request(route)) == {"something": None}

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_is_not_JSON(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.IM_USED
            content_type = "text/html"
            reason = "cause why not"
            real_url = "https://some.url"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_parse_ratelimits", new_callable=mock.AsyncMock, return_value=None),
            mock.patch.object(
                patched__client_session, "request", new_callable=mock.AsyncMock, return_value=StubResponse()
            ),
            pytest.raises(errors.HTTPError),
        ):
            await rest_client._perform_request(route)

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_unhandled_status(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        class StubResponse:
            status = http.HTTPStatus.NOT_IMPLEMENTED
            content_type = "text/html"
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_parse_ratelimits", new_callable=mock.AsyncMock, return_value=None),
            mock.patch.object(
                patched__client_session, "request", new_callable=mock.AsyncMock, return_value=StubResponse()
            ),
            mock.patch.object(net, "generate_error_response", return_value=exit_exception),
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route)

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_status_in_retry_codes_will_retry_until_exhausted(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        class StubResponse:
            status = http.HTTPStatus.INTERNAL_SERVER_ERROR

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_parse_ratelimits", new_callable=mock.AsyncMock, return_value=None),
            mock.patch.object(rest_client, "_max_retries", 3),
            mock.patch.object(
                patched__client_session, "request", new_callable=mock.AsyncMock, return_value=StubResponse()
            ) as patched_request,
            mock.patch.object(
                rate_limits,
                "ExponentialBackOff",
                return_value=mock.Mock(__next__=mock.Mock(side_effect=[1, 2, 3, 4, 5])),
            ) as exponential_backoff,
            mock.patch.object(asyncio, "sleep") as asyncio_sleep,
            mock.patch.object(net, "generate_error_response", return_value=exit_exception) as generate_error_response,
            pytest.raises(exit_exception),
        ):
            await rest_client._perform_request(route)

        assert exponential_backoff.return_value.__next__.call_count == 3
        exponential_backoff.assert_called_once_with(maximum=16)
        asyncio_sleep.assert_has_awaits([mock.call(1), mock.call(2), mock.call(3)])
        generate_error_response.assert_called_once_with(patched_request.return_value)

    @hikari_test_helpers.timeout()
    @pytest.mark.parametrize("exception", [asyncio.TimeoutError, aiohttp.ClientConnectionError])
    async def test_perform_request_when_connection_error_will_retry_until_exhausted(
        self, rest_client: rest.RESTClientImpl, exception: typing.Type[ExitException]
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exception))

        with (
            mock.patch.object(rest_client, "_client_session", mock_session),
            mock.patch.object(rest_client, "_parse_ratelimits", new_callable=mock.AsyncMock),
            mock.patch.object(rest_client, "_max_retries", 3),
            mock.patch.object(
                rate_limits,
                "ExponentialBackOff",
                return_value=mock.Mock(__next__=mock.Mock(side_effect=[1, 2, 3, 4, 5])),
            ) as exponential_backoff,
            mock.patch.object(asyncio, "sleep") as asyncio_sleep,
            pytest.raises(errors.HTTPError),
        ):
            await rest_client._perform_request(route)

        assert exponential_backoff.return_value.__next__.call_count == 3
        exponential_backoff.assert_called_once_with(maximum=16)
        asyncio_sleep.assert_has_awaits([mock.call(1), mock.call(2), mock.call(3)])

    @pytest.mark.parametrize("enabled", [True, False])
    @hikari_test_helpers.timeout()
    async def test_perform_request_logger(self, rest_client: rest.RESTClientImpl, enabled: bool):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            headers = {}
            reason = "cause why not"

            async def read(self):
                return None

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest, "_LOGGER", new=mock.Mock(isEnabledFor=mock.Mock(return_value=enabled))) as logger,
            mock.patch.object(rest_client, "_client_session") as patched__client_session,
            mock.patch.object(rest_client, "_parse_ratelimits", new_callable=mock.AsyncMock, return_value=None),
            mock.patch.object(
                patched__client_session, "request", new_callable=mock.AsyncMock, return_value=StubResponse()
            ),
        ):
            await rest_client._perform_request(route)

        if enabled:
            assert logger.log.call_count == 2
        else:
            assert logger.log.call_count == 0

    async def test__parse_ratelimits_when_bucket_provided_updates_rate_limits(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.OK
            headers = {
                rest._X_RATELIMIT_BUCKET_HEADER: "bucket_header",
                rest._X_RATELIMIT_LIMIT_HEADER: "123456789",
                rest._X_RATELIMIT_REMAINING_HEADER: "987654321",
                rest._X_RATELIMIT_RESET_AFTER_HEADER: "12.2",
            }

        response = StubResponse()
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_bucket_manager") as patched__bucket_manager,
            mock.patch.object(patched__bucket_manager, "update_rate_limits") as patched_update_rate_limits,
        ):
            assert await rest_client._parse_ratelimits(route, "auth", response) is None

            patched_update_rate_limits.assert_called_once_with(
                compiled_route=route,
                bucket_header="bucket_header",
                authentication="auth",
                remaining_header=987654321,
                limit_header=123456789,
                reset_after=12.2,
            )

    async def test__parse_ratelimits_when_not_ratelimited(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.OK
            headers = {}

            json = mock.AsyncMock()

        response = StubResponse()
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        await rest_client._parse_ratelimits(route, "auth", response)

        response.json.assert_not_called()

    async def test__parse_ratelimits_when_ratelimited(
        self, rest_client: rest.RESTClientImpl, exit_exception: typing.Type[ExitException]
    ):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}

            async def read(self):
                raise exit_exception

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(exit_exception):
            await rest_client._parse_ratelimits(route, "auth", StubResponse())

    async def test__parse_ratelimits_when_unexpected_content_type(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = "text/html"
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return "this is not json :)"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(errors.HTTPResponseError):
            await rest_client._parse_ratelimits(route, "auth", StubResponse())

    async def test__parse_ratelimits_when_global_ratelimit(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return '{"global": true, "retry_after": "2"}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_bucket_manager") as patched__bucket_manager,
            mock.patch.object(patched__bucket_manager, "throttle") as patched_throttle,
        ):
            assert (await rest_client._parse_ratelimits(route, "auth", StubResponse())) == 0

            patched_throttle.assert_called_once_with(2.0)

    async def test__parse_ratelimits_when_remaining_header_under_or_equal_to_0(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {rest._X_RATELIMIT_REMAINING_HEADER: "0"}
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "2", "global": False}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        assert await rest_client._parse_ratelimits(route, "some auth", StubResponse()) == 0

    async def test__parse_ratelimits_when_retry_after_is_not_too_long(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return '{"retry_after": "0.002"}'

        with (
            mock.patch.object(rest_client, "_bucket_manager") as patched__bucket_manager,
            mock.patch.object(patched__bucket_manager, "max_rate_limit", 10),
        ):
            route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
            assert await rest_client._parse_ratelimits(route, "some auth", StubResponse()) == 0.002

    async def test__parse_ratelimits_when_retry_after_is_too_long(self, rest_client: rest.RESTClientImpl):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return '{"retry_after": "4"}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with (
            mock.patch.object(rest_client, "_bucket_manager") as patched__bucket_manager,
            mock.patch.object(patched__bucket_manager, "max_rate_limit", 3),
            pytest.raises(errors.RateLimitTooLongError),
        ):
            await rest_client._parse_ratelimits(route, "auth", StubResponse())

    #############
    # Endpoints #
    #############

    async def test_fetch_channel(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.GET_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()

        mock_channel = mock.Mock(channels.GuildTextChannel, id=snowflakes.Snowflake(123))

        with (
            mock.patch.object(
                rest_client.entity_factory, "deserialize_channel", return_value=mock_object
            ) as patched_deserialize_channel,
            mock.patch.object(
                rest_client, "_request", mock.AsyncMock(return_value={"payload": "NO"})
            ) as patched__request,
        ):
            assert await rest_client.fetch_channel(mock_channel) == mock_object

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_channel.assert_called_once_with(patched__request.return_value)

    async def test_fetch_channel_with_dm_channel_when_cacheful(
        self, rest_client: rest.RESTClientImpl, mock_cache: cache.MutableCache
    ):
        expected_route = routes.GET_CHANNEL.compile(channel=123)
        mock_object = mock.Mock(spec=channels.DMChannel, type=channels.ChannelType.DM)

        mock_channel = mock.Mock(channels.DMChannel, id=snowflakes.Snowflake(123))

        with (
            mock.patch.object(
                rest_client.entity_factory, "deserialize_channel", return_value=mock_object
            ) as patched_deserialize_channel,
            mock.patch.object(
                rest_client, "_request", mock.AsyncMock(return_value={"payload": "NO"})
            ) as patched__request,
            mock.patch.object(mock_cache, "set_dm_channel_id") as patched_set_dm_channel_id,
        ):
            assert await rest_client.fetch_channel(mock_channel) == mock_object

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_channel.assert_called_once_with(patched__request.return_value)
            patched_set_dm_channel_id.assert_called_once_with(mock_object.recipient.id, mock_object.id)

    async def test_fetch_channel_with_dm_channel_when_cacheless(
        self, rest_client: rest.RESTClientImpl, mock_cache: cache.MutableCache
    ):
        expected_route = routes.GET_CHANNEL.compile(channel=123)
        mock_object = mock.Mock(spec=channels.DMChannel, type=channels.ChannelType.DM)

        mock_channel = mock.Mock(channels.DMChannel, id=snowflakes.Snowflake(123))

        with (
            mock.patch.object(rest_client, "_cache", None),
            mock.patch.object(
                rest_client.entity_factory, "deserialize_channel", return_value=mock_object
            ) as patched_deserialize_channel,
            mock.patch.object(
                rest_client, "_request", mock.AsyncMock(return_value={"payload": "NO"})
            ) as patched__request,
            mock.patch.object(mock_cache, "set_dm_channel_id") as patched_set_dm_channel_id,
        ):
            assert await rest_client.fetch_channel(mock_channel) == mock_object

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_channel.assert_called_once_with(patched__request.return_value)
            patched_set_dm_channel_id.assert_not_called()

    @pytest.mark.parametrize(
        ("emoji", "expected_emoji_id", "expected_emoji_name"),
        [
            (emojis.CustomEmoji(id=snowflakes.Snowflake(989), name="emoji", is_animated=False), 989, None),
            (emojis.UnicodeEmoji("❤️"), None, "❤️"),
            (None, None, None),
        ],
    )
    @pytest.mark.parametrize(
        ("auto_archive_duration", "default_auto_archive_duration"),
        [(12322, 445123), (datetime.timedelta(minutes=12322), datetime.timedelta(minutes=445123)), (12322.0, 445123.1)],
    )
    async def test_edit_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_guild_category: channels.GuildCategory,
        auto_archive_duration: typing.Union[int, datetime.timedelta],
        default_auto_archive_duration: typing.Union[int, float],
        emoji: undefined.UndefinedNoneOr[emojis.Emoji],
        expected_emoji_id: typing.Optional[snowflakes.Snowflake],
        expected_emoji_name: typing.Optional[str],
    ):
        expected_route = routes.PATCH_CHANNEL.compile(channel=4560)
        mock_object = mock.Mock()

        mock_tag = channels.ForumTag(id=snowflakes.Snowflake(0), name="tag", moderated=False, emoji=None)

        with (
            mock.patch.object(rest_client, "_cache", None),
            mock.patch.object(
                rest_client.entity_factory, "deserialize_channel", return_value=mock_object
            ) as patched_deserialize_channel,
            mock.patch.object(
                rest_client.entity_factory,
                "serialize_permission_overwrite",
                return_value={"type": "member", "allow": 1024, "deny": 8192, "id": "1235431"},
            ),
            mock.patch.object(
                rest_client.entity_factory,
                "serialize_forum_tag",
                return_value={"id": 0, "name": "testing", "moderated": True, "emoji_id": None, "emoji_name": None},
            ),
            mock.patch.object(
                rest_client, "_request", mock.AsyncMock(return_value={"payload": "GO"})
            ) as patched__request,
        ):
            expected_json = {
                "name": "new name",
                "position": 1,
                "rtc_region": "ostrich-city",
                "topic": "new topic",
                "nsfw": True,
                "bitrate": 10,
                "video_quality_mode": channels.VideoQualityMode.FULL,
                "user_limit": 100,
                "rate_limit_per_user": 30,
                "parent_id": "4564",
                "permission_overwrites": [{"type": "member", "allow": 1024, "deny": 8192, "id": "1235431"}],
                "default_auto_archive_duration": 445123,
                "default_thread_rate_limit_per_user": 40,
                "default_forum_layout": channels.ForumLayoutType.LIST_VIEW,
                "default_sort_order": channels.ForumSortOrderType.LATEST_ACTIVITY,
                "default_reaction_emoji": {"emoji_id": expected_emoji_id, "emoji_name": expected_emoji_name},
                "available_tags": [
                    {"id": 0, "name": "testing", "moderated": True, "emoji_id": None, "emoji_name": None}
                ],
                "archived": True,
                "locked": False,
                "invitable": True,
                "auto_archive_duration": 12322,
                "flags": channels.ChannelFlag.REQUIRE_TAG,
                "applied_tags": ["0"],
            }

            result = await rest_client.edit_channel(
                mock_guild_text_channel,
                name="new name",
                position=1,
                topic="new topic",
                nsfw=True,
                bitrate=10,
                video_quality_mode=channels.VideoQualityMode.FULL,
                user_limit=100,
                rate_limit_per_user=30,
                permission_overwrites=[
                    channels.PermissionOverwrite(
                        type=channels.PermissionOverwriteType.MEMBER,
                        allow=permissions.Permissions.VIEW_CHANNEL,
                        deny=permissions.Permissions.MANAGE_MESSAGES,
                        id=1235431,
                    )
                ],
                parent_category=mock_guild_category,
                region="ostrich-city",
                reason="some reason :)",
                default_auto_archive_duration=default_auto_archive_duration,
                default_thread_rate_limit_per_user=40,
                default_forum_layout=channels.ForumLayoutType.LIST_VIEW,
                default_sort_order=channels.ForumSortOrderType.LATEST_ACTIVITY,
                available_tags=[channels.ForumTag(name="testing", moderated=True)],
                default_reaction_emoji=emoji,
                archived=True,
                locked=False,
                invitable=True,
                auto_archive_duration=auto_archive_duration,
                flags=channels.ChannelFlag.REQUIRE_TAG,
                applied_tags=[mock_tag],
            )

            assert result == mock_object

            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="some reason :)")
            patched_deserialize_channel.assert_called_once_with(patched__request.return_value)

    async def test_edit_channel_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.PATCH_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()

        mock_channel = mock.Mock(channels.GuildTextChannel, id=snowflakes.Snowflake(123))

        with (
            mock.patch.object(
                rest_client.entity_factory, "deserialize_channel", return_value=mock_object
            ) as patched_deserialize_channel,
            mock.patch.object(
                rest_client, "_request", mock.AsyncMock(return_value={"payload": "no"})
            ) as patched__request,
        ):
            assert await rest_client.edit_channel(mock_channel) == mock_object

            patched__request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)
            patched_deserialize_channel.assert_called_once_with(patched__request.return_value)

    async def test_delete_channel(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.DELETE_CHANNEL.compile(channel=123)

        mock_channel = mock.Mock(channels.GuildTextChannel, id=snowflakes.Snowflake(123))

        with (
            mock.patch.object(rest_client.entity_factory, "deserialize_channel") as patched_deserialize_channel,
            mock.patch.object(
                rest_client, "_request", mock.AsyncMock(return_value={"id": "NNNNN"})
            ) as patched__request,
        ):
            result = await rest_client.delete_channel(mock_channel, reason="Why not :D")

            assert result is patched_deserialize_channel.return_value
            patched_deserialize_channel.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(expected_route, reason="Why not :D")

    async def test_edit_my_voice_state_when_requesting_to_speak(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
    ):
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=123)
        mock_datetime = mock.Mock(isoformat=mock.Mock(return_value="blamblamblam"))

        with (
            mock.patch.object(time, "utc_datetime", return_value=mock_datetime) as patched_utc_datetime,
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
        ):
            result = await rest_client.edit_my_voice_state(
                mock_partial_guild, mock_guild_stage_channel, suppress=True, request_to_speak=True
            )

            patched_utc_datetime.assert_called_once()
            mock_datetime.isoformat.assert_called_once()

        assert result is None
        patched__request.assert_awaited_once_with(
            expected_route, json={"channel_id": "45613", "suppress": True, "request_to_speak_timestamp": "blamblamblam"}
        )

    async def test_edit_my_voice_state_when_revoking_speak_request(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
    ):
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=123)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            result = await rest_client.edit_my_voice_state(
                mock_partial_guild, mock_guild_stage_channel, suppress=True, request_to_speak=False
            )

            assert result is None
            patched__request.assert_awaited_once_with(
                expected_route, json={"channel_id": "45613", "suppress": True, "request_to_speak_timestamp": None}
            )

    async def test_edit_my_voice_state_when_providing_datetime_for_request_to_speak(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
    ):
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=123)
        mock_datetime = mock.Mock(spec=datetime.datetime, isoformat=mock.Mock(return_value="blamblamblam2"))

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            result = await rest_client.edit_my_voice_state(
                mock_partial_guild, mock_guild_stage_channel, suppress=True, request_to_speak=mock_datetime
            )

            assert result is None
            mock_datetime.isoformat.assert_called_once()
            patched__request.assert_awaited_once_with(
                expected_route,
                json={"channel_id": "45613", "suppress": True, "request_to_speak_timestamp": "blamblamblam2"},
            )

    async def test_edit_my_voice_state_without_optional_fields(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
    ):
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=123)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            result = await rest_client.edit_my_voice_state(mock_partial_guild, mock_guild_stage_channel)

            assert result is None
            patched__request.assert_awaited_once_with(expected_route, json={"channel_id": "45613"})

    async def test_edit_voice_state(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
        mock_user: users.User,
    ):
        expected_route = routes.PATCH_GUILD_VOICE_STATE.compile(guild=123, user=789)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            result = await rest_client.edit_voice_state(
                mock_partial_guild, mock_guild_stage_channel, mock_user, suppress=True
            )

            assert result is None
            patched__request.assert_awaited_once_with(expected_route, json={"channel_id": "45613", "suppress": True})

    async def test_edit_voice_state_without_optional_arguments(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
        mock_user: users.User,
    ):
        expected_route = routes.PATCH_GUILD_VOICE_STATE.compile(guild=123, user=789)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            result = await rest_client.edit_voice_state(mock_partial_guild, mock_guild_stage_channel, mock_user)

            assert result is None
            patched__request.assert_awaited_once_with(expected_route, json={"channel_id": "45613"})

    async def test_edit_permission_overwrite(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        expected_route = routes.PUT_CHANNEL_PERMISSIONS.compile(channel=4560, overwrite=2983)

        expected_json = {"type": 1, "allow": 4, "deny": 1}

        target = mock.Mock(users.PartialUser, id=snowflakes.Snowflake(2983))

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.edit_permission_overwrite(
                mock_guild_text_channel,
                target,
                target_type=channels.PermissionOverwriteType.MEMBER,
                allow=permissions.Permissions.BAN_MEMBERS,
                deny=permissions.Permissions.CREATE_INSTANT_INVITE,
                reason="cause why not :)",
            )
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="cause why not :)")

    @pytest.mark.parametrize(
        ("target", "expected_type"),
        [
            (mock.Mock(users.UserImpl, id=34895734), channels.PermissionOverwriteType.MEMBER),
            (mock.Mock(guilds.Role, id=34895734), channels.PermissionOverwriteType.ROLE),
            (
                mock.Mock(channels.PermissionOverwrite, id=34895734, type=channels.PermissionOverwriteType.MEMBER),
                channels.PermissionOverwriteType.MEMBER,
            ),
        ],
    )
    async def test_edit_permission_overwrite_when_target_undefined(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        target: mock.Mock,
        expected_type: channels.PermissionOverwriteType,
    ):
        expected_route = routes.PUT_CHANNEL_PERMISSIONS.compile(channel=4560, overwrite=34895734)

        expected_json = {"type": expected_type}

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.edit_permission_overwrite(mock_guild_text_channel, target)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)

    async def test_edit_permission_overwrite_when_cant_determine_target_type(self, rest_client: rest.RESTClientImpl):
        mock_channel = mock.Mock(channels.GuildStageChannel, id=snowflakes.Snowflake(123))
        mock_target = mock.Mock(id=snowflakes.Snowflake(456))

        with pytest.raises(TypeError):
            await rest_client.edit_permission_overwrite(mock_channel, mock_target)

    async def test_delete_permission_overwrite(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        expected_route = routes.DELETE_CHANNEL_PERMISSIONS.compile(channel=4560, overwrite=23409582)

        mock_target = mock.Mock(users.PartialUser, id=snowflakes.Snowflake(23409582))

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_permission_overwrite(mock_guild_text_channel, mock_target)
            patched__request.assert_awaited_once_with(expected_route)

    async def test_fetch_channel_invites(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        invite1 = make_invite_with_metadata("1111")
        invite2 = make_invite_with_metadata("2222")

        expected_route = routes.GET_CHANNEL_INVITES.compile(channel=4560)

        with (
            mock.patch.object(
                rest_client, "_request", new=mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_invite_with_metadata", side_effect=[invite1, invite2]
            ) as patched_deserialize_invite_with_metadata,
        ):
            assert await rest_client.fetch_channel_invites(mock_guild_text_channel) == [invite1, invite2]
            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_invite_with_metadata.call_count == 2
            patched_deserialize_invite_with_metadata.assert_has_calls(
                [mock.call({"id": "456"}), mock.call({"id": "789"})]
            )

    async def test_create_invite(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_user: users.User,
        mock_application: applications.Application,
    ):
        expected_route = routes.POST_CHANNEL_INVITES.compile(channel=4560)
        expected_json = {
            "max_age": 60,
            "max_uses": 4,
            "temporary": True,
            "unique": True,
            "target_type": invites.TargetType.STREAM,
            "target_user_id": "789",
            "target_application_id": "111",
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"ID": "NOOOOOOOOPOOOOOOOI!"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_invite_with_metadata"
            ) as patched_deserialize_invite_with_metadata,
        ):
            result = await rest_client.create_invite(
                mock_guild_text_channel,
                max_age=datetime.timedelta(minutes=1),
                max_uses=4,
                temporary=True,
                unique=True,
                target_type=invites.TargetType.STREAM,
                target_user=mock_user,
                target_application=mock_application,
                reason="cause why not :)",
            )

            assert result is patched_deserialize_invite_with_metadata.return_value
            patched_deserialize_invite_with_metadata.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="cause why not :)")

    async def test_fetch_pins(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        # FIXME: I probs should have a way to fix this.
        message1 = make_mock_message(456)
        message2 = make_mock_message(789)
        expected_route = routes.GET_CHANNEL_PINS.compile(channel=4560)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_message", side_effect=[message1, message2]
            ) as patched_deserialize_message,
        ):
            assert await rest_client.fetch_pins(mock_guild_text_channel) == [message1, message2]
            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_message.call_count == 2
            patched_deserialize_message.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_pin_message(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.PUT_CHANNEL_PINS.compile(channel=4560, message=101)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.pin_message(mock_guild_text_channel, mock_message)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_unpin_message(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.DELETE_CHANNEL_PIN.compile(channel=4560, message=101)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.unpin_message(mock_guild_text_channel, mock_message)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_fetch_message(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        message_obj = mock.Mock()
        expected_route = routes.GET_CHANNEL_MESSAGE.compile(channel=4560, message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_message", return_value=message_obj
            ) as patched_deserialize_message,
        ):
            assert await rest_client.fetch_message(mock_guild_text_channel, mock_message) is message_obj

        patched__request.assert_awaited_once_with(expected_route)
        patched_deserialize_message.assert_called_once_with({"id": "456"})

    async def test_create_message_when_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_CHANNEL_MESSAGES.compile(channel=4560)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 987654321}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.create_message(
                mock_guild_text_channel,
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                poll=poll_obj,
                sticker=54234,
                stickers=[564123, 431123],
                tts=True,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                reply=mock_message,
                reply_must_exist=False,
                flags=54123,
            )
            assert returned is patched_deserialize_message.return_value

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            sticker=54234,
            stickers=[564123, 431123],
            tts=True,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=54123,
        )
        mock_form.add_field.assert_called_once_with(
            "payload_json",
            b'{"testing":"ensure_in_test","message_reference":{"message_id":"101","fail_if_not_exists":false}}',
            content_type="application/json",
        )
        patched__request.assert_awaited_once_with(expected_route, form_builder=mock_form)
        patched_deserialize_message.assert_called_once_with({"message_id": 987654321})

    async def test_create_message_when_no_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_CHANNEL_MESSAGES.compile(channel=4560)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 987654321}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.create_message(
                mock_guild_text_channel,
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                poll=poll_obj,
                sticker=543345,
                stickers=[123321, 6572345],
                tts=True,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                reply=mock_message,
                reply_must_exist=False,
                flags=6643,
            )
            assert returned is patched_deserialize_message.return_value

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            sticker=543345,
            stickers=[123321, 6572345],
            tts=True,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=6643,
        )
        patched__request.assert_awaited_once_with(
            expected_route,
            json={"testing": "ensure_in_test", "message_reference": {"message_id": "101", "fail_if_not_exists": False}},
        )
        patched_deserialize_message.assert_called_once_with({"message_id": 987654321})

    async def test_crosspost_message(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_news_channel: channels.GuildNewsChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.POST_CHANNEL_CROSSPOST.compile(channel=4565, message=101)

        message = mock.Mock()

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "93939383883", "content": "foobar"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_message", return_value=message
            ) as patched_deserialize_message,
        ):
            result = await rest_client.crosspost_message(mock_guild_news_channel, mock_message)

            assert result is message
            patched_deserialize_message.assert_called_once_with({"id": "93939383883", "content": "foobar"})
            patched__request.assert_awaited_once_with(expected_route)

    async def test_edit_message_when_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=4560, message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.edit_message(
                mock_guild_text_channel,
                mock_message,
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                flags=messages.MessageFlag.NONE,
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                flags=messages.MessageFlag.NONE,
                mentions_everyone=False,
                mentions_reply=undefined.UNDEFINED,
                user_mentions=[9876],
                role_mentions=[1234],
                edit=True,
            )
            mock_form.add_field.assert_called_once_with(
                "payload_json", b'{"testing":"ensure_in_test"}', content_type="application/json"
            )
            patched__request.assert_awaited_once_with(expected_route, form_builder=mock_form)
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_message_when_no_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=4560, message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.edit_message(
                mock_guild_text_channel,
                mock_message,
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                flags=messages.MessageFlag.NONE,
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                flags=messages.MessageFlag.NONE,
                mentions_everyone=False,
                mentions_reply=undefined.UNDEFINED,
                user_mentions=[9876],
                role_mentions=[1234],
                edit=True,
            )
            patched__request.assert_awaited_once_with(expected_route, json={"testing": "ensure_in_test"})
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_follow_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_news_channel: channels.GuildNewsChannel,
        mock_guild_text_channel: channels.GuildTextChannel,
    ):
        expected_route = routes.POST_CHANNEL_FOLLOWERS.compile(channel=4565)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"channel_id": "929292", "webhook_id": "929383838"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_channel_follow"
            ) as patched_deserialize_channel_follow,
        ):
            result = await rest_client.follow_channel(
                mock_guild_news_channel, mock_guild_text_channel, reason="get followed"
            )

            assert result is patched_deserialize_channel_follow.return_value
            patched_deserialize_channel_follow.assert_called_once_with(
                {"channel_id": "929292", "webhook_id": "929383838"}
            )
            patched__request.assert_awaited_once_with(
                expected_route, json={"webhook_channel_id": "4560"}, reason="get followed"
            )

    async def test_delete_message(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.DELETE_CHANNEL_MESSAGE.compile(channel=4560, message=101)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_message(mock_guild_text_channel, mock_message, reason="broke laws")

        patched__request.assert_awaited_once_with(expected_route, reason="broke laws")

    async def test_delete_messages(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        expected_route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=4560)

        messages_list = [make_mock_message(i) for i in range(200)]
        expected_json1 = {"messages": [str(i) for i in range(100)]}
        expected_json2 = {"messages": [str(i) for i in range(100, 200)]}

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_messages(mock_guild_text_channel, *messages_list, reason="broke laws")

            patched__request.assert_has_awaits(
                [
                    mock.call(expected_route, json=expected_json1, reason="broke laws"),
                    mock.call(expected_route, json=expected_json2, reason="broke laws"),
                ]
            )

    async def test_delete_messages_when_one_message_left_in_chunk_and_delete_message_raises_message_not_found(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        messages = [make_mock_message(i) for i in range(101)]
        message = messages[-1]
        expected_json = {"messages": [str(i) for i in range(100)]}

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(
                rest_client,
                "delete_message",
                side_effect=errors.NotFoundError(url="", headers={}, raw_body="", code=10008),
            ) as patched_delete_message,
        ):
            await rest_client.delete_messages(mock_guild_text_channel, *messages, reason="broke laws")

        patched__request.assert_awaited_once_with(
            routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=mock_guild_text_channel),
            json=expected_json,
            reason="broke laws",
        )
        patched_delete_message.assert_awaited_once_with(mock_guild_text_channel, message, reason="broke laws")

    async def test_delete_messages_when_one_message_left_in_chunk_and_delete_message_raises_channel_not_found(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        messages = [make_mock_message(i) for i in range(101)]
        message = messages[-1]
        expected_json = {"messages": [str(i) for i in range(100)]}

        mock_not_found = errors.NotFoundError(url="", headers={}, raw_body="", code=10003)

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest_client, "delete_message", side_effect=mock_not_found) as patched_delete_message,
            pytest.raises(errors.BulkDeleteError) as exc_info,
        ):
            await rest_client.delete_messages(mock_guild_text_channel, *messages, reason="broke laws")

        assert exc_info.value.__cause__ is mock_not_found

        patched__request.assert_awaited_once_with(
            routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=mock_guild_text_channel),
            json=expected_json,
            reason="broke laws",
        )
        patched_delete_message.assert_awaited_once_with(mock_guild_text_channel, message, reason="broke laws")

    async def test_delete_messages_when_one_message_left_in_chunk(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        messages = [make_mock_message(i) for i in range(101)]
        message = messages[-1]
        expected_json = {"messages": [str(i) for i in range(100)]}

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_messages(mock_guild_text_channel, *messages, reason="broke laws")

            patched__request.assert_has_awaits(
                [
                    mock.call(
                        routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=mock_guild_text_channel),
                        json=expected_json,
                        reason="broke laws",
                    ),
                    mock.call(
                        routes.DELETE_CHANNEL_MESSAGE.compile(channel=mock_guild_text_channel, message=message),
                        reason="broke laws",
                    ),
                ]
            )

    async def test_delete_messages_when_exception(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        messages = [make_mock_message(i) for i in range(101)]

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock, side_effect=Exception),
            pytest.raises(errors.BulkDeleteError),
        ):
            await rest_client.delete_messages(mock_guild_text_channel, *messages, reason="broke laws")

    async def test_delete_messages_with_iterable(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        message_list = (make_mock_message(i) for i in range(101))

        message_1 = make_mock_message(444)
        message_2 = make_mock_message(6523)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_messages(
                mock_guild_text_channel, message_list, message_1, message_2, reason="broke laws"
            )

            patched__request.assert_has_awaits(
                [
                    mock.call(
                        routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=mock_guild_text_channel),
                        json={"messages": [str(i) for i in range(100)]},
                        reason="broke laws",
                    ),
                    mock.call(
                        routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=mock_guild_text_channel),
                        json={"messages": ["100", "444", "6523"]},
                        reason="broke laws",
                    ),
                ]
            )

    async def test_delete_messages_with_async_iterable(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        iterator = iterators.FlatLazyIterator(make_mock_message(i) for i in range(103))

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_messages(mock_guild_text_channel, iterator)

            patched__request.assert_has_awaits(
                [
                    mock.call(
                        routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=mock_guild_text_channel),
                        json={"messages": [str(i) for i in range(100)]},
                        reason=undefined.UNDEFINED,
                    ),
                    mock.call(
                        routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=mock_guild_text_channel),
                        json={"messages": ["100", "101", "102"]},
                        reason=undefined.UNDEFINED,
                    ),
                ]
            )

    async def test_delete_messages_with_async_iterable_and_args(self, rest_client: rest.RESTClientImpl):
        with pytest.raises(TypeError, match=re.escape("Cannot use *args with an async iterable.")):
            await rest_client.delete_messages(54123, iterators.FlatLazyIterator(()), 1, 2)

    async def test_add_reaction(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.PUT_MY_REACTION.compile(emoji="rooYay:123", channel=4560, message=101)

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"),
        ):
            await rest_client.add_reaction(mock_guild_text_channel, mock_message, "<:rooYay:123>")

        patched__request.assert_awaited_once_with(expected_route)

    async def test_delete_my_reaction(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.DELETE_MY_REACTION.compile(emoji="rooYay:123", channel=4560, message=101)

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"),
        ):
            await rest_client.delete_my_reaction(mock_guild_text_channel, mock_message, "<:rooYay:123>")

        patched__request.assert_awaited_once_with(expected_route)

    async def test_delete_all_reactions_for_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.DELETE_REACTION_EMOJI.compile(emoji="rooYay:123", channel=4560, message=101)

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"),
        ):
            await rest_client.delete_all_reactions_for_emoji(mock_guild_text_channel, mock_message, "<:rooYay:123>")

        patched__request.assert_awaited_once_with(expected_route)

    async def test_delete_reaction(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_user: users.User,
        mock_message: messages.Message,
    ):
        expected_route = routes.DELETE_REACTION_USER.compile(emoji="rooYay:123", channel=4560, message=101, user=789)

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"),
        ):
            await rest_client.delete_reaction(mock_guild_text_channel, mock_message, mock_user, "<:rooYay:123>")

        patched__request.assert_awaited_once_with(expected_route)

    async def test_delete_all_reactions(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.DELETE_ALL_REACTIONS.compile(channel=4560, message=101)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_all_reactions(mock_guild_text_channel, mock_message)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_create_webhook(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        file_resource_patch: files.Resource[typing.Any],
    ):
        webhook = mock.Mock(webhooks.PartialWebhook)
        expected_route = routes.POST_CHANNEL_WEBHOOKS.compile(channel=4560)

        expected_json = {"name": "test webhook", "avatar": "some data"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_incoming_webhook", return_value=webhook
            ) as patched_deserialize_incoming_webhook,
        ):
            returned = await rest_client.create_webhook(
                mock_guild_text_channel, "test webhook", avatar="someavatar.png", reason="why not"
            )
            assert returned is webhook

            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="why not")
            patched_deserialize_incoming_webhook.assert_called_once_with({"id": "456"})

    async def test_create_webhook_without_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_partial_webhook: webhooks.PartialWebhook,
    ):
        expected_route = routes.POST_CHANNEL_WEBHOOKS.compile(channel=4560)
        expected_json = {"name": "test webhook"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_incoming_webhook", return_value=mock_partial_webhook
            ) as patched_deserialize_incoming_webhook,
        ):
            assert await rest_client.create_webhook(mock_guild_text_channel, "test webhook") is mock_partial_webhook
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)
            patched_deserialize_incoming_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook(self, rest_client: rest.RESTClientImpl, mock_partial_webhook: webhooks.PartialWebhook):
        expected_route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=112, token="token")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_webhook", return_value=mock_partial_webhook
            ) as patched_deserialize_webhook,
        ):
            assert await rest_client.fetch_webhook(mock_partial_webhook, token="token") is mock_partial_webhook
            patched__request.assert_awaited_once_with(expected_route, auth=None)
            patched_deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook_without_token(
        self, rest_client: rest.RESTClientImpl, mock_partial_webhook: webhooks.PartialWebhook
    ):
        expected_route = routes.GET_WEBHOOK.compile(webhook=112)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_webhook", return_value=mock_partial_webhook
            ) as patched_deserialize_webhook,
        ):
            assert await rest_client.fetch_webhook(mock_partial_webhook) is mock_partial_webhook
            patched__request.assert_awaited_once_with(expected_route, auth=undefined.UNDEFINED)
            patched_deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_channel_webhooks(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        webhook1 = make_partial_webhook(238947239847)
        webhook2 = make_partial_webhook(218937419827)
        expected_route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=4560)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_webhook", side_effect=[webhook1, webhook2]
            ) as patched_deserialize_webhook,
        ):
            assert await rest_client.fetch_channel_webhooks(mock_guild_text_channel) == [webhook1, webhook2]
            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_webhook.call_count == 2
            patched_deserialize_webhook.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_fetch_channel_webhooks_ignores_unrecognised_webhook_type(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_partial_webhook: webhooks.PartialWebhook,
    ):
        expected_route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=4560)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_webhook",
                side_effect=[errors.UnrecognisedEntityError("yeet"), mock_partial_webhook],
            ) as patched_deserialize_webhook,
        ):
            assert await rest_client.fetch_channel_webhooks(mock_guild_text_channel) == [mock_partial_webhook]
            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_webhook.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_fetch_guild_webhooks(self, rest_client: rest.RESTClientImpl):
        webhook1 = make_partial_webhook(456)
        webhook2 = make_partial_webhook(789)

        expected_route = routes.GET_GUILD_WEBHOOKS.compile(guild=123)

        mock_guild = mock.Mock(guilds.PartialGuild, id=snowflakes.Snowflake(123))

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_webhook", side_effect=[webhook1, webhook2]
            ) as patched_deserialize_webhook,
        ):
            assert await rest_client.fetch_guild_webhooks(mock_guild) == [webhook1, webhook2]
            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_webhook.call_count == 2
            patched_deserialize_webhook.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_fetch_guild_webhooks_ignores_unrecognised_webhook_types(
        self, rest_client: rest.RESTClientImpl, mock_partial_webhook: webhooks.PartialWebhook
    ):
        expected_route = routes.GET_GUILD_WEBHOOKS.compile(guild=123)

        mock_guild = mock.Mock(guilds.PartialGuild, id=snowflakes.Snowflake(123))

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_webhook",
                side_effect=[errors.UnrecognisedEntityError("meow meow"), mock_partial_webhook],
            ) as patched_deserialize_webhook,
        ):
            assert await rest_client.fetch_guild_webhooks(mock_guild) == [mock_partial_webhook]
            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_webhook.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_edit_webhook(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_partial_webhook: webhooks.PartialWebhook,
    ):
        expected_route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(webhook=112, token="token")
        expected_json = {"name": "some other name", "channel": "4560", "avatar": None}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_webhook", return_value=mock_partial_webhook
            ) as patched_deserialize_webhook,
        ):
            returned = await rest_client.edit_webhook(
                mock_partial_webhook,
                token="token",
                name="some other name",
                avatar=None,
                channel=mock_guild_text_channel,
                reason="some smart reason to do this",
            )
            assert returned is mock_partial_webhook

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason="some smart reason to do this", auth=None
            )
            patched_deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_edit_webhook_without_token(
        self, rest_client: rest.RESTClientImpl, mock_partial_webhook: webhooks.PartialWebhook
    ):
        expected_route = routes.PATCH_WEBHOOK.compile(webhook=112)
        expected_json = {}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_webhook", return_value=mock_partial_webhook
            ) as patched_deserialize_webhook,
        ):
            returned = await rest_client.edit_webhook(mock_partial_webhook)
            assert returned is mock_partial_webhook

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason=undefined.UNDEFINED, auth=undefined.UNDEFINED
            )
            patched_deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_edit_webhook_when_avatar_is_file(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_webhook: webhooks.PartialWebhook,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.PATCH_WEBHOOK.compile(webhook=112)
        expected_json = {"avatar": "some data"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_webhook", return_value=mock_partial_webhook
            ) as patched_deserialize_webhook,
        ):
            assert await rest_client.edit_webhook(mock_partial_webhook, avatar="someavatar.png") is mock_partial_webhook

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason=undefined.UNDEFINED, auth=undefined.UNDEFINED
            )
            patched_deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_delete_webhook(
        self, rest_client: rest.RESTClientImpl, mock_partial_webhook: webhooks.PartialWebhook
    ):
        expected_route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(webhook=112, token="token")

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
        ) as patched__request:
            await rest_client.delete_webhook(mock_partial_webhook, token="token")
            patched__request.assert_awaited_once_with(expected_route, auth=None)

    async def test_delete_webhook_without_token(
        self, rest_client: rest.RESTClientImpl, mock_partial_webhook: webhooks.PartialWebhook
    ):
        expected_route = routes.DELETE_WEBHOOK.compile(webhook=112)

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
        ) as patched__request:
            await rest_client.delete_webhook(mock_partial_webhook)
            patched__request.assert_awaited_once_with(expected_route, auth=undefined.UNDEFINED)

    @pytest.mark.parametrize(
        ("webhook", "avatar_url"),
        [
            (mock.Mock(webhooks.ExecutableWebhook, webhook_id=432), files.URL("https://website.com/davfsa_logo")),
            (432, "https://website.com/davfsa_logo"),
        ],
    )
    async def test_execute_webhook_when_form(
        self, rest_client: rest.RESTClientImpl, webhook: webhooks.ExecutableWebhook, avatar_url: files.URL
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=432, token="hi, im a token")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
        ):
            returned = await rest_client.execute_webhook(
                webhook,
                "hi, im a token",
                username="davfsa",
                avatar_url=avatar_url,
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                poll=poll_obj,
                tts=True,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                flags=120,
            )
            assert returned is patched_deserialize_message.return_value

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )
        mock_form.add_field.assert_called_once_with(
            "payload_json",
            b'{"testing":"ensure_in_test","username":"davfsa","avatar_url":"https://website.com/davfsa_logo"}',
            content_type="application/json",
        )
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_form, query={"wait": "true"}, auth=None
        )
        patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_execute_webhook_when_form_and_thread(
        self, rest_client: rest.RESTClientImpl, mock_guild_public_thread_channel: channels.GuildThreadChannel
    ):
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=112, token="hi, im a token")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
        ):
            returned = await rest_client.execute_webhook(
                112, "hi, im a token", content="new content", thread=mock_guild_public_thread_channel
            )
            assert returned is patched_deserialize_message.return_value

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            component=undefined.UNDEFINED,
            components=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            poll=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )
        mock_form.add_field.assert_called_once_with(
            "payload_json", b'{"testing":"ensure_in_test"}', content_type="application/json"
        )
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_form, query={"wait": "true", "thread_id": "45611"}, auth=None
        )
        patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_execute_webhook_when_no_form(
        self, rest_client: rest.RESTClientImpl, mock_guild_public_thread_channel: channels.GuildThreadChannel
    ):
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=432, token="hi, im a token")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
        ):
            returned = await rest_client.execute_webhook(
                432, "hi, im a token", content="new content", thread=mock_guild_public_thread_channel
            )
            assert returned is patched_deserialize_message.return_value

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            component=undefined.UNDEFINED,
            components=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            polls=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )
        patched__request.assert_awaited_once_with(
            expected_route, json={"testing": "ensure_in_test"}, query={"wait": "true", "thread_id": "45611"}, auth=None
        )
        patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_execute_webhook_when_thread_and_no_form(self, rest_client: rest.RESTClientImpl):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=432, token="hi, im a token")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
        ):
            returned = await rest_client.execute_webhook(
                432,
                "hi, im a token",
                username="davfsa",
                avatar_url="https://website.com/davfsa_logo",
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                tts=True,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                flags=120,
            )
            assert returned is patched_deserialize_message.return_value

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )
        patched__request.assert_awaited_once_with(
            expected_route,
            json={"testing": "ensure_in_test", "username": "davfsa", "avatar_url": "https://website.com/davfsa_logo"},
            query={"wait": "true"},
            auth=None,
        )
        patched_deserialize_message.assert_called_once_with({"message_id": 123})

    @pytest.mark.parametrize("webhook", [mock.Mock(webhooks.ExecutableWebhook, webhook_id=432), 432])
    async def test_fetch_webhook_message(
        self,
        rest_client: rest.RESTClientImpl,
        mock_message: messages.Message,
        webhook: webhooks.ExecutableWebhook | int,
    ):
        message_obj = mock.Mock()
        expected_route = routes.GET_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_message", return_value=message_obj
            ) as patched_deserialize_message,
        ):
            assert await rest_client.fetch_webhook_message(webhook, "hi, im a token", mock_message) is message_obj

            patched__request.assert_awaited_once_with(expected_route, auth=None, query={})
            patched_deserialize_message.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook_message_when_thread(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_public_thread_channel: channels.GuildThreadChannel,
        mock_message: messages.Message,
    ):
        message_obj = mock.Mock()
        expected_route = routes.GET_WEBHOOK_MESSAGE.compile(webhook=112, token="hi, im a token", message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_message", return_value=message_obj
            ) as patched_deserialize_message,
        ):
            result = await rest_client.fetch_webhook_message(
                112, "hi, im a token", mock_message, thread=mock_guild_public_thread_channel
            )

            assert result is message_obj
            patched__request.assert_awaited_once_with(expected_route, auth=None, query={"thread_id": "45611"})
            patched_deserialize_message.assert_called_once_with({"id": "456"})

    @pytest.mark.parametrize("webhook", [mock.Mock(webhooks.ExecutableWebhook, webhook_id=432), 432])
    async def test_edit_webhook_message_when_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_message: messages.Message,
        webhook: webhooks.ExecutableWebhook | int,
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.edit_webhook_message(
                webhook,
                "hi, im a token",
                mock_message,
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                edit=True,
            )
            mock_form.add_field.assert_called_once_with(
                "payload_json", b'{"testing":"ensure_in_test"}', content_type="application/json"
            )
            patched__request.assert_awaited_once_with(expected_route, form_builder=mock_form, query={}, auth=None)
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_webhook_message_when_form_and_thread(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_public_thread_channel: channels.GuildThreadChannel,
        mock_message: messages.Message,
    ):
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=12354123, token="hi, im a token", message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.edit_webhook_message(
                12354123, "hi, im a token", mock_message, content="new content", thread=mock_guild_public_thread_channel
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=undefined.UNDEFINED,
                attachments=undefined.UNDEFINED,
                component=undefined.UNDEFINED,
                components=undefined.UNDEFINED,
                embed=undefined.UNDEFINED,
                embeds=undefined.UNDEFINED,
                mentions_everyone=undefined.UNDEFINED,
                user_mentions=undefined.UNDEFINED,
                role_mentions=undefined.UNDEFINED,
                edit=True,
            )
            mock_form.add_field.assert_called_once_with(
                "payload_json", b'{"testing":"ensure_in_test"}', content_type="application/json"
            )
            patched__request.assert_awaited_once_with(
                expected_route, form_builder=mock_form, query={"thread_id": "45611"}, auth=None
            )
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_webhook_message_when_no_form(
        self, rest_client: rest.RESTClientImpl, mock_message: messages.Message
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.edit_webhook_message(
                432,
                "hi, im a token",
                mock_message,
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                edit=True,
            )
            patched__request.assert_awaited_once_with(
                expected_route, json={"testing": "ensure_in_test"}, query={}, auth=None
            )
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_webhook_message_when_thread_and_no_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_public_thread_channel: channels.GuildThreadChannel,
        mock_message: messages.Message,
    ):
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=101)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
        ):
            returned = await rest_client.edit_webhook_message(
                432, "hi, im a token", mock_message, content="new content", thread=mock_guild_public_thread_channel
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=undefined.UNDEFINED,
                attachments=undefined.UNDEFINED,
                component=undefined.UNDEFINED,
                components=undefined.UNDEFINED,
                embed=undefined.UNDEFINED,
                embeds=undefined.UNDEFINED,
                mentions_everyone=undefined.UNDEFINED,
                user_mentions=undefined.UNDEFINED,
                role_mentions=undefined.UNDEFINED,
                edit=True,
            )
            patched__request.assert_awaited_once_with(
                expected_route, json={"testing": "ensure_in_test"}, query={"thread_id": "45611"}, auth=None
            )
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    @pytest.mark.parametrize("webhook", [mock.Mock(webhooks.ExecutableWebhook, webhook_id=123), 123])
    async def test_delete_webhook_message(
        self,
        rest_client: rest.RESTClientImpl,
        mock_message: messages.Message,
        webhook: webhooks.ExecutableWebhook | int,
    ):
        expected_route = routes.DELETE_WEBHOOK_MESSAGE.compile(webhook=123, token="token", message=101)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_webhook_message(webhook, "token", mock_message)

            patched__request.assert_awaited_once_with(expected_route, auth=None, query={})

    async def test_delete_webhook_message_when_thread(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_public_thread_channel: channels.GuildThreadChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.DELETE_WEBHOOK_MESSAGE.compile(webhook=123, token="token", message=101)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_webhook_message(
                123, "token", mock_message, thread=mock_guild_public_thread_channel
            )

            patched__request.assert_awaited_once_with(expected_route, auth=None, query={"thread_id": "45611"})

    async def test_fetch_gateway_url(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.GET_GATEWAY.compile()

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"url": "wss://some.url"}
        ) as patched__request:
            assert await rest_client.fetch_gateway_url() == "wss://some.url"

            patched__request.assert_awaited_once_with(expected_route, auth=None)

    async def test_fetch_gateway_bot(self, rest_client: rest.RESTClientImpl):
        bot = mock.Mock(sessions.GatewayBotInfo, id=123)
        expected_route = routes.GET_GATEWAY_BOT.compile()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_gateway_bot_info", return_value=bot
            ) as patched_deserialize_gateway_bot_info,
        ):
            assert await rest_client.fetch_gateway_bot_info() is bot

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_gateway_bot_info.assert_called_once_with({"id": "123"})

    async def test_fetch_invite(self, rest_client: rest.RESTClientImpl):
        input_invite = mock.Mock(invites.InviteCode, code="Jx4cNGG")
        return_invite = mock.Mock(invites.Invite)
        expected_route = routes.GET_INVITE.compile(invite_code="Jx4cNGG")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "Jx4cNGG"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_invite", return_value=return_invite
            ) as patched_deserialize_invite,
        ):
            assert await rest_client.fetch_invite(input_invite, with_counts=True) == return_invite

        patched__request.assert_awaited_once_with(expected_route, query={"with_counts": "true"})
        patched_deserialize_invite.assert_called_once_with({"code": "Jx4cNGG"})

    async def test_delete_invite(self, rest_client: rest.RESTClientImpl):
        input_invite = mock.Mock(invites.InviteCode, code="Jx4cNGG")
        expected_route = routes.DELETE_INVITE.compile(invite_code="Jx4cNGG")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"ok": "NO"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_invite") as patched_deserialize_invite,
        ):
            result = await rest_client.delete_invite(input_invite)

            assert result is patched_deserialize_invite.return_value

            patched_deserialize_invite.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(expected_route)

    async def test_fetch_my_user(self, rest_client: rest.RESTClientImpl, mock_user: users.User):
        expected_route = routes.GET_MY_USER.compile()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_my_user", return_value=mock_user
            ) as patched_deserialize_my_user,
        ):
            assert await rest_client.fetch_my_user() is mock_user

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user(self, rest_client: rest.RESTClientImpl, mock_user: users.User):
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_my_user", return_value=mock_user
            ) as patched_deserialize_my_user,
        ):
            assert await rest_client.edit_my_user(username="new username") is mock_user

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_avatar_is_None(self, rest_client: rest.RESTClientImpl, mock_user: users.User):
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "avatar": None}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_my_user", return_value=mock_user
            ) as patched_deserialize_my_user,
        ):
            assert await rest_client.edit_my_user(username="new username", avatar=None) is mock_user

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_avatar_is_file(
        self, rest_client: rest.RESTClientImpl, mock_user: users.User, file_resource_patch: files.Resource[typing.Any]
    ):
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "avatar": "some data"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_my_user", return_value=mock_user
            ) as patched_deserialize_my_user,
        ):
            assert await rest_client.edit_my_user(username="new username", avatar="someavatar.png") is mock_user

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_banner_is_None(self, rest_client: rest.RESTClientImpl, mock_user: users.User):
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "banner": None}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_my_user", return_value=mock_user
            ) as patched_deserialize_my_user,
        ):
            assert await rest_client.edit_my_user(username="new username", banner=None) is mock_user

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_banner_is_file(
        self, rest_client: rest.RESTClientImpl, mock_user: users.User, file_resource_patch: files.Resource[typing.Any]
    ):
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "banner": "some data"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_my_user", return_value=mock_user
            ) as patched_deserialize_my_user,
        ):
            assert await rest_client.edit_my_user(username="new username", banner="somebanner.png") is mock_user

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_fetch_my_connections(self, rest_client: rest.RESTClientImpl):
        connection1 = mock.Mock(applications.OwnConnection, id=123)
        connection2 = mock.Mock(applications.OwnConnection, id=456)
        expected_route = routes.GET_MY_CONNECTIONS.compile()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "123"}, {"id": "456"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_own_connection", side_effect=[connection1, connection2]
            ) as patched_deserialize_own_connection,
        ):
            assert await rest_client.fetch_my_connections() == [connection1, connection2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_own_connection.call_count == 2
            patched_deserialize_own_connection.assert_has_calls([mock.call({"id": "123"}), mock.call({"id": "456"})])

    async def test_leave_guild(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.DELETE_MY_GUILD.compile(guild=123)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.leave_guild(mock_partial_guild)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_create_dm_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_cache: cache.MutableCache,
        mock_dm_channel: channels.DMChannel,
        mock_user: users.User,
    ):
        expected_route = routes.POST_MY_CHANNELS.compile()
        expected_json = {"recipient_id": "789"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "43234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_dm", return_value=mock_dm_channel
            ) as patched_deserialize_dm,
            mock.patch.object(mock_cache, "set_dm_channel_id") as patched_set_dm_channel_id,
        ):
            assert await rest_client.create_dm_channel(mock_user) == mock_dm_channel

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_dm.assert_called_once_with({"id": "43234"})
            patched_set_dm_channel_id.assert_called_once_with(mock_user, mock_dm_channel.id)

    async def test_create_dm_channel_when_cacheless(
        self,
        rest_client: rest.RESTClientImpl,
        mock_cache: cache.MutableCache,
        mock_dm_channel: channels.DMChannel,
        mock_user: users.User,
    ):
        expected_route = routes.POST_MY_CHANNELS.compile()
        expected_json = {"recipient_id": "789"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "43234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_dm", return_value=mock_dm_channel
            ) as patched_deserialize_dm,
            mock.patch.object(rest_client, "_cache", None),
            mock.patch.object(mock_cache, "set_dm_channel_id") as patched_set_dm_channel_id,
        ):
            assert await rest_client.create_dm_channel(mock_user) == mock_dm_channel

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_dm.assert_called_once_with({"id": "43234"})
            patched_set_dm_channel_id.assert_not_called()

    async def test_fetch_application(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        expected_route = routes.GET_MY_APPLICATION.compile()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_application", return_value=mock_application
            ) as patched_deserialize_application,
        ):
            assert await rest_client.fetch_application() is mock_application

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_application.assert_called_once_with({"id": "123"})

    async def test_fetch_authorization(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.GET_MY_AUTHORIZATION.compile()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"application": {}}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_authorization_information"
            ) as patched_deserialize_authorization_information,
        ):
            result = await rest_client.fetch_authorization()

            assert result is patched_deserialize_authorization_information.return_value

            patched_deserialize_authorization_information.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(expected_route)

    async def test_authorize_client_credentials_token(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()

        with (
            mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form),
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"access_token": "43212123123123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_partial_token"
            ) as patched_deserialize_partial_token,
        ):
            await rest_client.authorize_client_credentials_token(65234123, "4312312", scopes=["scope1", "scope2"])

        mock_url_encoded_form.add_field.assert_has_calls(
            [mock.call("grant_type", "client_credentials"), mock.call("scope", "scope1 scope2")]
        )
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NjUyMzQxMjM6NDMxMjMxMg=="
        )
        patched_deserialize_partial_token.assert_called_once_with(patched__request.return_value)

    async def test_authorize_access_token_without_scopes(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()

        with (
            mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form),
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"access_token": 42}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_authorization_token"
            ) as patched_deserialize_authorization_token,
        ):
            result = await rest_client.authorize_access_token(65234, "43123", "a.code", "htt:redirect//me")

        mock_url_encoded_form.add_field.assert_has_calls(
            [
                mock.call("grant_type", "authorization_code"),
                mock.call("code", "a.code"),
                mock.call("redirect_uri", "htt:redirect//me"),
            ]
        )
        assert result is patched_deserialize_authorization_token.return_value
        patched_deserialize_authorization_token.assert_called_once_with(patched__request.return_value)
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NjUyMzQ6NDMxMjM="
        )

    async def test_authorize_access_token_with_scopes(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()

        with (
            mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form),
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"access_token": 42}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_authorization_token"
            ) as patched_deserialize_authorization_token,
        ):
            result = await rest_client.authorize_access_token(12343, "1235555", "a.codee", "htt:redirect//mee")

        mock_url_encoded_form.add_field.assert_has_calls(
            [
                mock.call("grant_type", "authorization_code"),
                mock.call("code", "a.codee"),
                mock.call("redirect_uri", "htt:redirect//mee"),
            ]
        )
        assert result is patched_deserialize_authorization_token.return_value
        patched_deserialize_authorization_token.assert_called_once_with(patched__request.return_value)
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic MTIzNDM6MTIzNTU1NQ=="
        )

    async def test_refresh_access_token_without_scopes(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()

        with (
            mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form),
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"access_token": 42}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_authorization_token"
            ) as patched_deserialize_authorization_token,
        ):
            result = await rest_client.refresh_access_token(454123, "123123", "a.codet")

        mock_url_encoded_form.add_field.assert_has_calls(
            [mock.call("grant_type", "refresh_token"), mock.call("refresh_token", "a.codet")]
        )
        assert result is patched_deserialize_authorization_token.return_value
        patched_deserialize_authorization_token.assert_called_once_with(patched__request.return_value)
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NDU0MTIzOjEyMzEyMw=="
        )

    async def test_refresh_access_token_with_scopes(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()

        with (
            mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form),
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"access_token": 42}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_authorization_token"
            ) as patched_deserialize_authorization_token,
        ):
            result = await rest_client.refresh_access_token(54123, "312312", "a.codett", scopes=["1", "3", "scope43"])

        mock_url_encoded_form.add_field.assert_has_calls(
            [
                mock.call("grant_type", "refresh_token"),
                mock.call("refresh_token", "a.codett"),
                mock.call("scope", "1 3 scope43"),
            ]
        )
        assert result is patched_deserialize_authorization_token.return_value
        patched_deserialize_authorization_token.assert_called_once_with(patched__request.return_value)
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NTQxMjM6MzEyMzEy"
        )

    async def test_revoke_access_token(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TOKEN_REVOKE.compile()
        mock_url_encoded_form = mock.Mock()

        with (
            mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form),
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_authorization_token"),
        ):
            await rest_client.revoke_access_token(54123, "123542", "not.a.token")

        mock_url_encoded_form.add_field.assert_called_once_with("token", "not.a.token")
        patched__request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NTQxMjM6MTIzNTQy"
        )

    async def test_add_user_to_guild(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        member = mock.Mock(guilds.Member, id=789)
        expected_route = routes.PUT_GUILD_MEMBER.compile(guild=123, user=789)
        expected_json = {
            "access_token": "token",
            "nick": "cool nick",
            "roles": ["234", "567"],
            "mute": True,
            "deaf": False,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_member", return_value=member
            ) as patched_deserialize_member,
        ):
            returned = await rest_client.add_user_to_guild(
                "token",
                mock_partial_guild,
                mock_user,
                nickname="cool nick",
                roles=[make_partial_role(234), make_partial_role(567)],
                mute=True,
                deaf=False,
            )
            assert returned is member

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_member.assert_called_once_with({"id": "789"}, guild_id=123)

    async def test_add_user_to_guild_when_already_in_guild(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        expected_route = routes.PUT_GUILD_MEMBER.compile(guild=123, user=789)
        expected_json = {"access_token": "token"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=None
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            assert await rest_client.add_user_to_guild("token", mock_partial_guild, mock_user) is None

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_member.assert_not_called()

    async def test_fetch_voice_regions(self, rest_client: rest.RESTClientImpl):
        voice_region1 = mock.Mock(voices.VoiceRegion, id="123")
        voice_region2 = mock.Mock(voices.VoiceRegion, id="456")
        expected_route = routes.GET_VOICE_REGIONS.compile()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "123"}, {"id": "456"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_voice_region", side_effect=[voice_region1, voice_region2]
            ) as patched_deserialize_voice_region,
        ):
            assert await rest_client.fetch_voice_regions() == [voice_region1, voice_region2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_voice_region.call_count == 2
            patched_deserialize_voice_region.assert_has_calls([mock.call({"id": "123"}), mock.call({"id": "456"})])

    async def test_fetch_user(self, rest_client: rest.RESTClientImpl, mock_user: users.User):
        user = mock.Mock(users.User, id=789)
        expected_route = routes.GET_USER.compile(user=789)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_user", return_value=user
            ) as patched_deserialize_user,
        ):
            assert await rest_client.fetch_user(mock_user) is user

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_user.assert_called_once_with({"id": "456"})

    async def test_fetch_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_custom_emoji: emojis.CustomEmoji,
    ):
        expected_route = routes.GET_GUILD_EMOJI.compile(emoji=4440, guild=123)

        emoji = make_custom_emoji(9989)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", return_value=emoji
            ) as patched_deserialize_known_custom_emoji,
        ):
            assert await rest_client.fetch_emoji(mock_partial_guild, mock_custom_emoji) is emoji

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_known_custom_emoji.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_fetch_guild_emojis(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        emoji1 = make_custom_emoji(2893472193)
        emoji2 = make_custom_emoji(9823748921)
        expected_route = routes.GET_GUILD_EMOJIS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", side_effect=[emoji1, emoji2]
            ) as patched_deserialize_known_custom_emoji,
        ):
            assert await rest_client.fetch_guild_emojis(mock_partial_guild) == [emoji1, emoji2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_known_custom_emoji.call_count == 2
            patched_deserialize_known_custom_emoji.assert_has_calls(
                [mock.call({"id": "456"}, guild_id=123), mock.call({"id": "789"}, guild_id=123)]
            )

    async def test_create_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_custom_emoji: emojis.CustomEmoji,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.POST_GUILD_EMOJIS.compile(guild=123)
        expected_json = {"name": "rooYay", "image": "some data", "roles": ["22398429", "82903740"]}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", return_value=mock_custom_emoji
            ) as patched_deserialize_known_custom_emoji,
        ):
            returned = await rest_client.create_emoji(
                mock_partial_guild,
                "rooYay",
                "rooYay.png",
                roles=[make_partial_role(22398429), make_partial_role(82903740)],
                reason="cause rooYay",
            )
            assert returned is mock_custom_emoji

            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="cause rooYay")
            patched_deserialize_known_custom_emoji.assert_called_once_with({"id": "234"}, guild_id=123)

    async def test_edit_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_custom_emoji: emojis.CustomEmoji,
    ):
        emoji = mock.Mock(emojis.CustomEmoji, id=234)
        expected_route = routes.PATCH_GUILD_EMOJI.compile(guild=123, emoji=4440)
        expected_json = {"name": "rooYay2", "roles": ["22398429", "82903740"]}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", return_value=emoji
            ) as patched_deserialize_known_custom_emoji,
        ):
            returned = await rest_client.edit_emoji(
                mock_partial_guild,
                mock_custom_emoji,
                name="rooYay2",
                roles=[make_partial_role(22398429), make_partial_role(82903740)],
                reason="Because we have got the power",
            )
            assert returned is emoji

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason="Because we have got the power"
            )
            patched_deserialize_known_custom_emoji.assert_called_once_with({"id": "234"}, guild_id=123)

    async def test_delete_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_custom_emoji: emojis.CustomEmoji,
    ):
        expected_route = routes.DELETE_GUILD_EMOJI.compile(guild=123, emoji=4440)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_emoji(mock_partial_guild, mock_custom_emoji, reason="testing")

            patched__request.assert_awaited_once_with(expected_route, reason="testing")

    async def test_fetch_application_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_custom_emoji: emojis.CustomEmoji,
    ):
        expected_route = routes.GET_APPLICATION_EMOJI.compile(emoji=28937492734, application=111)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", return_value=mock_custom_emoji
            ) as patched_deserialize_known_custom_emoji,
        ):
            assert (
                await rest_client.fetch_application_emoji(mock_application, make_custom_emoji(28937492734))
                is mock_custom_emoji
            )

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_known_custom_emoji.assert_called_once_with({"id": "456"})

    async def test_fetch_application_emojis(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        emoji1 = make_custom_emoji(2398472983)
        emoji2 = make_custom_emoji(2309842398)
        expected_route = routes.GET_APPLICATION_EMOJIS.compile(application=111)

        with (
            mock.patch.object(
                rest_client, "_request", return_value={"items": [{"id": "456"}, {"id": "789"}]}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", side_effect=[emoji1, emoji2]
            ) as patched_deserialize_known_custom_emoji,
        ):
            assert await rest_client.fetch_application_emojis(mock_application) == [emoji1, emoji2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_known_custom_emoji.call_count == 2
            patched_deserialize_known_custom_emoji.assert_has_calls(
                [mock.call({"id": "456"}), mock.call({"id": "789"})]
            )

    async def test_create_application_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_custom_emoji: emojis.CustomEmoji,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.POST_APPLICATION_EMOJIS.compile(application=111)
        expected_json = {"name": "rooYay", "image": "some data"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", return_value=mock_custom_emoji
            ) as patched_deserialize_known_custom_emoji,
        ):
            returned = await rest_client.create_application_emoji(mock_application, "rooYay", "rooYay.png")
            assert returned is mock_custom_emoji

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_known_custom_emoji.assert_called_once_with({"id": "234"})

    async def test_edit_application_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_custom_emoji: emojis.CustomEmoji,
    ):
        expected_route = routes.PATCH_APPLICATION_EMOJI.compile(application=111, emoji=23847234)
        expected_json = {"name": "rooYay2"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_known_custom_emoji", return_value=mock_custom_emoji
            ) as patched_deserialize_known_custom_emoji,
        ):
            returned = await rest_client.edit_application_emoji(
                mock_application, make_custom_emoji(23847234), name="rooYay2"
            )
            assert returned is mock_custom_emoji

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)
            patched_deserialize_known_custom_emoji.assert_called_once_with({"id": "234"})

    async def test_delete_application_emoji(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_custom_emoji: emojis.CustomEmoji,
    ):
        expected_route = routes.DELETE_APPLICATION_EMOJI.compile(application=111, emoji=4440)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_application_emoji(mock_application, mock_custom_emoji)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_fetch_sticker_packs(self, rest_client: rest.RESTClientImpl):
        pack1 = mock.Mock()
        pack2 = mock.Mock()
        pack3 = mock.Mock()
        expected_route = routes.GET_STICKER_PACKS.compile()

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"sticker_packs": [{"id": "123"}, {"id": "456"}, {"id": "789"}]},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_sticker_pack", side_effect=[pack1, pack2, pack3]
            ) as patched_deserialize_sticker_pack,
        ):
            assert await rest_client.fetch_available_sticker_packs() == [pack1, pack2, pack3]

            patched__request.assert_awaited_once_with(expected_route, auth=None)
            patched_deserialize_sticker_pack.assert_has_calls(
                [mock.call({"id": "123"}), mock.call({"id": "456"}), mock.call({"id": "789"})]
            )

    async def test_fetch_sticker_when_guild_sticker(
        self, rest_client: rest.RESTClientImpl, mock_partial_sticker: stickers.PartialSticker
    ):
        expected_route = routes.GET_STICKER.compile(sticker=222)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123", "guild_id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_sticker"
            ) as patched_deserialize_guild_sticker,
        ):
            returned = await rest_client.fetch_sticker(mock_partial_sticker)
            assert returned is patched_deserialize_guild_sticker.return_value

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_guild_sticker.assert_called_once_with({"id": "123", "guild_id": "456"})

    async def test_fetch_sticker_when_standard_sticker(
        self, rest_client: rest.RESTClientImpl, mock_partial_sticker: stickers.PartialSticker
    ):
        expected_route = routes.GET_STICKER.compile(sticker=222)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_standard_sticker"
            ) as patched_deserialize_standard_sticker,
        ):
            returned = await rest_client.fetch_sticker(mock_partial_sticker)
            assert returned is patched_deserialize_standard_sticker.return_value

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_standard_sticker.assert_called_once_with({"id": "123"})

    async def test_fetch_guild_stickers(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        sticker1 = mock.Mock()
        sticker2 = mock.Mock()
        sticker3 = mock.Mock()
        expected_route = routes.GET_GUILD_STICKERS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value=[{"id": "123"}, {"id": "456"}, {"id": "789"}],
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_sticker", side_effect=[sticker1, sticker2, sticker3]
            ) as patched_deserialize_guild_sticker,
        ):
            assert await rest_client.fetch_guild_stickers(mock_partial_guild) == [sticker1, sticker2, sticker3]

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_guild_sticker.assert_has_calls(
                [mock.call({"id": "123"}), mock.call({"id": "456"}), mock.call({"id": "789"})]
            )

    async def test_fetch_guild_sticker(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_sticker: stickers.PartialSticker,
    ):
        expected_route = routes.GET_GUILD_STICKER.compile(guild=123, sticker=222)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_sticker"
            ) as patched_deserialize_guild_sticker,
        ):
            returned = await rest_client.fetch_guild_sticker(mock_partial_guild, mock_partial_sticker)
            assert returned is patched_deserialize_guild_sticker.return_value

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_guild_sticker.assert_called_once_with({"id": "123"})

    async def test_create_sticker(self, rest_client: rest.RESTClientImpl):
        rest_client.create_sticker = mock.AsyncMock()
        file = mock.Mock()

        sticker = await rest_client.create_sticker(
            90210, "NewSticker", "funny", file, description="A sticker", reason="blah blah blah"
        )
        assert sticker is rest_client.create_sticker.return_value

        rest_client.create_sticker.assert_awaited_once_with(
            90210, "NewSticker", "funny", file, description="A sticker", reason="blah blah blah"
        )

    async def test_edit_sticker(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_sticker: stickers.PartialSticker,
    ):
        expected_route = routes.PATCH_GUILD_STICKER.compile(guild=123, sticker=222)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_sticker"
            ) as patched_deserialize_guild_sticker,
        ):
            returned = await rest_client.edit_sticker(
                mock_partial_guild,
                mock_partial_sticker,
                name="testing_sticker",
                description="blah",
                tag=":cry:",
                reason="i am bored and have too much time in my hands",
            )
            assert returned is patched_deserialize_guild_sticker.return_value

            patched__request.assert_awaited_once_with(
                expected_route,
                json={"name": "testing_sticker", "description": "blah", "tags": ":cry:"},
                reason="i am bored and have too much time in my hands",
            )
            patched_deserialize_guild_sticker.assert_called_once_with({"id": "456"})

    async def test_delete_sticker(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_sticker: stickers.PartialSticker,
    ):
        expected_route = routes.DELETE_GUILD_STICKER.compile(guild=123, sticker=222)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_sticker(
                mock_partial_guild, mock_partial_sticker, reason="i am bored and have too much time in my hands"
            )

            patched__request.assert_awaited_once_with(
                expected_route, reason="i am bored and have too much time in my hands"
            )

    async def test_fetch_guild(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.GET_GUILD.compile(guild=123)
        expected_query = {"with_counts": "true"}

        guild = mock.Mock(guilds.PartialGuild, id=23478274)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "1234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_rest_guild", return_value=guild
            ) as patched_deserialize_rest_guild,
        ):
            assert await rest_client.fetch_guild(mock_partial_guild) is guild

            patched__request.assert_awaited_once_with(expected_route, query=expected_query)
            patched_deserialize_rest_guild.assert_called_once_with({"id": "1234"})

    async def test_fetch_guild_preview(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        guild_preview = mock.Mock(guilds.GuildPreview, id=1234)
        expected_route = routes.GET_GUILD_PREVIEW.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "1234"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_preview", return_value=guild_preview
            ) as patched_deserialize_guild_preview,
        ):
            assert await rest_client.fetch_guild_preview(mock_partial_guild) is guild_preview

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_guild_preview.assert_called_once_with({"id": "1234"})

    async def test_delete_guild(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.DELETE_GUILD.compile(guild=123)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_guild(mock_partial_guild)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_edit_guild(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_voice_channel: channels.GuildVoiceChannel,
        mock_user: users.User,
    ):
        icon_resource = MockFileResource("icon data")
        splash_resource = MockFileResource("splash data")
        banner_resource = MockFileResource("banner data")
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {
            "name": "hikari",
            "verification_level": 3,
            "default_message_notifications": 1,
            "explicit_content_filter": 1,
            "afk_timeout": 60,
            "preferred_locale": "en-UK",
            "afk_channel_id": "4562",
            "owner_id": "789",
            "system_channel_id": "789",
            "rules_channel_id": "987",
            "public_updates_channel_id": "654",
            "icon": "icon data",
            "splash": "splash data",
            "banner": "banner data",
            "features": ["COMMUNITY", "RAID_ALERTS_DISABLED"],
        }

        with (
            mock.patch.object(files, "ensure_resource", side_effect=[icon_resource, splash_resource, banner_resource]),
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_rest_guild") as patched_deserialize_rest_guild,
        ):
            result = await rest_client.edit_guild(
                mock_partial_guild,
                name="hikari",
                verification_level=guilds.GuildVerificationLevel.HIGH,
                default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
                explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.MEMBERS_WITHOUT_ROLES,
                afk_channel=mock_guild_voice_channel,
                afk_timeout=60,
                icon="icon.png",
                owner=mock_user,
                splash="splash.png",
                banner="banner.png",
                system_channel=make_guild_text_channel(789),
                rules_channel=make_guild_text_channel(987),
                public_updates_channel=make_guild_text_channel(654),
                preferred_locale="en-UK",
                features=[guilds.GuildFeature.COMMUNITY, guilds.GuildFeature.RAID_ALERTS_DISABLED],
                reason="hikari best",
            )
            assert result is patched_deserialize_rest_guild.return_value

        patched_deserialize_rest_guild.assert_called_once_with(patched__request.return_value)
        patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="hikari best")

    async def test_edit_guild_when_images_are_None(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_voice_channel: channels.GuildVoiceChannel,
        mock_user: users.User,
    ):
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {
            "name": "hikari",
            "verification_level": 3,
            "default_message_notifications": 1,
            "explicit_content_filter": 1,
            "afk_timeout": 60,
            "preferred_locale": "en-UK",
            "afk_channel_id": "4562",
            "owner_id": "789",
            "system_channel_id": "789",
            "rules_channel_id": "987",
            "public_updates_channel_id": "654",
            "icon": None,
            "splash": None,
            "banner": None,
            "features": ["COMMUNITY", "RAID_ALERTS_DISABLED"],
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"ok": "NO"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_rest_guild") as patched_deserialize_rest_guild,
        ):
            result = await rest_client.edit_guild(
                mock_partial_guild,
                name="hikari",
                verification_level=guilds.GuildVerificationLevel.HIGH,
                default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
                explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.MEMBERS_WITHOUT_ROLES,
                afk_channel=mock_guild_voice_channel,
                afk_timeout=60,
                icon=None,
                owner=mock_user,
                splash=None,
                banner=None,
                system_channel=make_guild_text_channel(789),
                rules_channel=make_guild_text_channel(987),
                public_updates_channel=make_guild_text_channel(654),
                preferred_locale="en-UK",
                features=[guilds.GuildFeature.COMMUNITY, guilds.GuildFeature.RAID_ALERTS_DISABLED],
                reason="hikari best",
            )
            assert result is patched_deserialize_rest_guild.return_value

            patched_deserialize_rest_guild.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="hikari best")

    async def test_edit_guild_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "42"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_rest_guild") as patched_deserialize_rest_guild,
        ):
            result = await rest_client.edit_guild(mock_partial_guild)
            assert result is patched_deserialize_rest_guild.return_value

            patched_deserialize_rest_guild.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)

    async def test_set_guild_incident_actions(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.PUT_GUILD_INCIDENT_ACTIONS.compile(guild=123)
        expected_json = {"invites_disabled_until": "2023-09-01T14:48:02.222000+00:00", "dms_disabled_until": None}
        rest_client._request = mock.AsyncMock(return_value={"testing": "data"})

        result = await rest_client.set_guild_incident_actions(
            123, invites_disabled_until=datetime.datetime(2023, 9, 1, 14, 48, 2, 222000, tzinfo=datetime.timezone.utc)
        )
        assert result is rest_client._entity_factory.deserialize_guild_incidents.return_value

        rest_client._entity_factory.deserialize_guild_incidents.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)

    async def test_fetch_guild_channels(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        channel1 = make_guild_text_channel(456)
        channel2 = make_guild_text_channel(789)
        expected_route = routes.GET_GUILD_CHANNELS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_channel", side_effect=[channel1, channel2]
            ) as patched_deserialize_channel,
        ):
            assert await rest_client.fetch_guild_channels(mock_partial_guild) == [channel1, channel2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_channel.call_count == 2
            patched_deserialize_channel.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_fetch_guild_channels_ignores_unknown_channel_type(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_text_channel: channels.GuildTextChannel,
    ):
        expected_route = routes.GET_GUILD_CHANNELS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_channel",
                side_effect=[errors.UnrecognisedEntityError("echelon"), mock_guild_text_channel],
            ) as patched_deserialize_channel,
        ):
            assert await rest_client.fetch_guild_channels(mock_partial_guild) == [mock_guild_text_channel]

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_channel.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_create_guild_text_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_category: channels.GuildCategory,
    ):
        overwrite1 = make_permission_overwrite(9283749)
        overwrite2 = make_permission_overwrite(2837472)

        with (
            mock.patch.object(
                rest_client, "_create_guild_channel", new_callable=mock.AsyncMock
            ) as patched__create_guild_channel,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_text_channel"
            ) as patched_deserialize_guild_text_channel,
        ):
            returned = await rest_client.create_guild_text_channel(
                mock_partial_guild,
                "general",
                position=1,
                topic="general chat",
                nsfw=False,
                rate_limit_per_user=60,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                reason="because we need one",
                default_auto_archive_duration=123332,
            )
            assert returned is patched_deserialize_guild_text_channel.return_value

            patched__create_guild_channel.assert_awaited_once_with(
                mock_partial_guild,
                "general",
                channels.ChannelType.GUILD_TEXT,
                position=1,
                topic="general chat",
                nsfw=False,
                rate_limit_per_user=60,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                reason="because we need one",
                default_auto_archive_duration=123332,
            )
            patched_deserialize_guild_text_channel.assert_called_once_with(patched__create_guild_channel.return_value)

    async def test_create_guild_news_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_category: channels.GuildCategory,
    ):
        overwrite1 = make_permission_overwrite(9283749)
        overwrite2 = make_permission_overwrite(2837472)

        with (
            mock.patch.object(
                rest_client, "_create_guild_channel", new_callable=mock.AsyncMock
            ) as patched__create_guild_channel,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_news_channel"
            ) as patched_deserialize_guild_news_channel,
        ):
            returned = await rest_client.create_guild_news_channel(
                mock_partial_guild,
                "general",
                position=1,
                topic="general news",
                nsfw=False,
                rate_limit_per_user=60,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                reason="because we need one",
                default_auto_archive_duration=5445234,
            )
            assert returned is patched_deserialize_guild_news_channel.return_value

            patched__create_guild_channel.assert_awaited_once_with(
                mock_partial_guild,
                "general",
                channels.ChannelType.GUILD_NEWS,
                position=1,
                topic="general news",
                nsfw=False,
                rate_limit_per_user=60,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                reason="because we need one",
                default_auto_archive_duration=5445234,
            )
            patched_deserialize_guild_news_channel.assert_called_once_with(patched__create_guild_channel.return_value)

    async def test_create_guild_forum_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_category: channels.GuildCategory,
    ):
        overwrite1 = make_permission_overwrite(9283749)
        overwrite2 = make_permission_overwrite(2837472)

        tag1 = mock.Mock(channels.ForumTag, id=1203)
        tag2 = mock.Mock(channels.ForumTag, id=1204)

        with (
            mock.patch.object(
                rest_client, "_create_guild_channel", new_callable=mock.AsyncMock
            ) as patched__create_guild_channel,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_forum_channel"
            ) as patched_deserialize_guild_forum_channel,
        ):
            returned = await rest_client.create_guild_forum_channel(
                mock_partial_guild,
                "help-center",
                position=1,
                topic="get help!",
                nsfw=False,
                rate_limit_per_user=60,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                reason="because we need one",
                default_auto_archive_duration=5445234,
                default_thread_rate_limit_per_user=40,
                default_forum_layout=channels.ForumLayoutType.LIST_VIEW,
                default_sort_order=channels.ForumSortOrderType.LATEST_ACTIVITY,
                available_tags=[tag1, tag2],
                default_reaction_emoji="some reaction",
            )
            assert returned is patched_deserialize_guild_forum_channel.return_value

            patched__create_guild_channel.assert_awaited_once_with(
                mock_partial_guild,
                "help-center",
                channels.ChannelType.GUILD_FORUM,
                position=1,
                topic="get help!",
                nsfw=False,
                rate_limit_per_user=60,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                reason="because we need one",
                default_auto_archive_duration=5445234,
                default_thread_rate_limit_per_user=40,
                default_forum_layout=channels.ForumLayoutType.LIST_VIEW,
                default_sort_order=channels.ForumSortOrderType.LATEST_ACTIVITY,
                available_tags=[tag1, tag2],
                default_reaction_emoji="some reaction",
            )
            patched_deserialize_guild_forum_channel.assert_called_once_with(patched__create_guild_channel.return_value)

    async def test_create_guild_voice_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_category: channels.GuildCategory,
    ):
        overwrite1 = make_permission_overwrite(9283749)
        overwrite2 = make_permission_overwrite(2837472)

        with (
            mock.patch.object(
                rest_client, "_create_guild_channel", new_callable=mock.AsyncMock
            ) as patched__create_guild_channel,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_voice_channel"
            ) as patched_deserialize_guild_voice_channel,
        ):
            returned = await rest_client.create_guild_voice_channel(
                mock_partial_guild,
                "general",
                position=1,
                user_limit=60,
                bitrate=64,
                video_quality_mode=channels.VideoQualityMode.FULL,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                region="ok boomer",
                reason="because we need one",
            )
            assert returned is patched_deserialize_guild_voice_channel.return_value

            patched__create_guild_channel.assert_awaited_once_with(
                mock_partial_guild,
                "general",
                channels.ChannelType.GUILD_VOICE,
                position=1,
                user_limit=60,
                bitrate=64,
                video_quality_mode=channels.VideoQualityMode.FULL,
                permission_overwrites=[overwrite1, overwrite2],
                region="ok boomer",
                category=mock_guild_category,
                reason="because we need one",
            )
            patched_deserialize_guild_voice_channel.assert_called_once_with(patched__create_guild_channel.return_value)

    async def test_create_guild_stage_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_category: channels.GuildCategory,
    ):
        overwrite1 = make_permission_overwrite(9283749)
        overwrite2 = make_permission_overwrite(2837472)

        with (
            mock.patch.object(
                rest_client, "_create_guild_channel", new_callable=mock.AsyncMock
            ) as patched__create_guild_channel,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_stage_channel"
            ) as patched_deserialize_guild_stage_channel,
        ):
            returned = await rest_client.create_guild_stage_channel(
                mock_partial_guild,
                "general",
                position=1,
                user_limit=60,
                bitrate=64,
                permission_overwrites=[overwrite1, overwrite2],
                category=mock_guild_category,
                region="Doge Moon",
                reason="When doge == 1$",
            )
            assert returned is patched_deserialize_guild_stage_channel.return_value

            patched__create_guild_channel.assert_awaited_once_with(
                mock_partial_guild,
                "general",
                channels.ChannelType.GUILD_STAGE,
                position=1,
                user_limit=60,
                bitrate=64,
                permission_overwrites=[overwrite1, overwrite2],
                region="Doge Moon",
                category=mock_guild_category,
                reason="When doge == 1$",
            )
            patched_deserialize_guild_stage_channel.assert_called_once_with(patched__create_guild_channel.return_value)

    async def test_create_guild_category(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        overwrite1 = make_permission_overwrite(9283749)
        overwrite2 = make_permission_overwrite(2837472)

        with (
            mock.patch.object(
                rest_client, "_create_guild_channel", new_callable=mock.AsyncMock
            ) as patched__create_guild_channel,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_category"
            ) as patched_deserialize_guild_category,
        ):
            returned = await rest_client.create_guild_category(
                mock_partial_guild,
                "general",
                position=1,
                permission_overwrites=[overwrite1, overwrite2],
                reason="because we need one",
            )
            assert returned is patched_deserialize_guild_category.return_value

            patched__create_guild_channel.assert_awaited_once_with(
                mock_partial_guild,
                "general",
                channels.ChannelType.GUILD_CATEGORY,
                position=1,
                permission_overwrites=[overwrite1, overwrite2],
                reason="because we need one",
            )
            patched_deserialize_guild_category.assert_called_once_with(patched__create_guild_channel.return_value)

    @pytest.mark.parametrize(
        ("emoji", "expected_emoji_id", "expected_emoji_name"),
        [
            (emojis.CustomEmoji(id=snowflakes.Snowflake(989), name="emoji", is_animated=False), 989, None),
            (emojis.UnicodeEmoji("❤️"), None, "❤️"),
        ],
    )
    @pytest.mark.parametrize("default_auto_archive_duration", [12322, (datetime.timedelta(minutes=12322)), 12322.0])
    async def test__create_guild_channel(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_category: channels.GuildCategory,
        default_auto_archive_duration: int | float | datetime.timedelta,
        emoji: emojis.Emoji,
        expected_emoji_id: int | None,
        expected_emoji_name: str | None,
    ):
        overwrite1 = make_permission_overwrite(9283749)
        overwrite2 = make_permission_overwrite(2837472)
        tag1 = mock.Mock(channels.ForumTag, id=321)
        tag2 = mock.Mock(channels.ForumTag, id=123)

        expected_route = routes.POST_GUILD_CHANNELS.compile(guild=123)
        expected_json = {
            "type": 0,
            "name": "general",
            "position": 1,
            "topic": "some topic",
            "nsfw": True,
            "bitrate": 64,
            "user_limit": 99,
            "rate_limit_per_user": 60,
            "rtc_region": "wicky wicky",
            "parent_id": "4564",
            "permission_overwrites": [{"id": "987"}, {"id": "654"}],
            "default_auto_archive_duration": 12322,
            "default_thread_rate_limit_per_user": 40,
            "default_forum_layout": 1,
            "default_sort_order": 0,
            "default_reaction_emoji": {"emoji_id": expected_emoji_id, "emoji_name": expected_emoji_name},
            "available_tags": [{"id": "321"}, {"id": "123"}],
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "serialize_permission_overwrite", side_effect=[{"id": "987"}, {"id": "654"}]
            ) as patched_serialize_permission_overwrite,
            mock.patch.object(
                rest_client.entity_factory, "serialize_forum_tag", side_effect=[{"id": "321"}, {"id": "123"}]
            ) as patched_serialize_forum_tag,
        ):
            returned = await rest_client._create_guild_channel(
                mock_partial_guild,
                "general",
                channels.ChannelType.GUILD_TEXT,
                position=1,
                topic="some topic",
                nsfw=True,
                bitrate=64,
                user_limit=99,
                rate_limit_per_user=60,
                permission_overwrites=[overwrite1, overwrite2],
                region="wicky wicky",
                category=mock_guild_category,
                reason="we have got the power",
                default_auto_archive_duration=default_auto_archive_duration,
                default_thread_rate_limit_per_user=40,
                default_forum_layout=channels.ForumLayoutType.LIST_VIEW,
                default_sort_order=channels.ForumSortOrderType.LATEST_ACTIVITY,
                available_tags=[tag1, tag2],
                default_reaction_emoji=emoji,
            )
            assert returned is patched__request.return_value

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason="we have got the power"
            )
            assert patched_serialize_permission_overwrite.call_count == 2
            patched_serialize_permission_overwrite.assert_has_calls([mock.call(overwrite1), mock.call(overwrite2)])
            assert patched_serialize_forum_tag.call_count == 2
            patched_serialize_forum_tag.assert_has_calls([mock.call(tag1), mock.call(tag2)])

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(12322, 42069), (datetime.timedelta(minutes=12322), datetime.timedelta(seconds=42069)), (12322.0, 42069.4)],
    )
    async def test_create_message_thread(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
        auto_archive_duration: time.Intervalish,
        rate_limit_per_user: time.Intervalish,
    ):
        expected_route = routes.POST_MESSAGE_THREADS.compile(channel=4560, message=101)
        expected_payload = {"name": "Sass alert!!!", "auto_archive_duration": 12322, "rate_limit_per_user": 42069}

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "54123123", "name": "dlksksldalksad"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_guild_thread",
                return_value=mock.Mock(channels.GuildPublicThread),
            ) as patched_deserialize_guild_thread,
        ):
            result = await rest_client.create_message_thread(
                mock_guild_text_channel,
                mock_message,
                "Sass alert!!!",
                auto_archive_duration=auto_archive_duration,
                rate_limit_per_user=rate_limit_per_user,
                reason="because we need one",
            )

            assert result is patched_deserialize_guild_thread.return_value
            patched__request.assert_awaited_once_with(
                expected_route, json=expected_payload, reason="because we need one"
            )
            patched_deserialize_guild_thread.assert_called_once_with(patched__request.return_value)

    async def test_create_message_thread_without_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.POST_MESSAGE_THREADS.compile(channel=4560, message=101)
        expected_payload = {"name": "Sass alert!!!", "auto_archive_duration": 1440}

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "54123123", "name": "dlksksldalksad"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_thread", return_value=mock.Mock(channels.GuildNewsThread)
            ) as patched_deserialize_guild_thread,
        ):
            result = await rest_client.create_message_thread(mock_guild_text_channel, mock_message, "Sass alert!!!")

            assert result is patched_deserialize_guild_thread.return_value
            patched__request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
            patched_deserialize_guild_thread.assert_called_once_with(patched__request.return_value)

    async def test_create_message_thread_with_all_undefined(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_message: messages.Message,
    ):
        expected_route = routes.POST_MESSAGE_THREADS.compile(channel=4560, message=101)
        expected_payload = {"name": "Sass alert!!!"}

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "54123123", "name": "dlksksldalksad"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_thread", return_value=mock.Mock(channels.GuildNewsThread)
            ) as patched_deserialize_guild_thread,
        ):
            result = await rest_client.create_message_thread(
                mock_guild_text_channel, mock_message, "Sass alert!!!", auto_archive_duration=undefined.UNDEFINED
            )

            assert result is patched_deserialize_guild_thread.return_value
            patched__request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
            patched_deserialize_guild_thread.assert_called_once_with(patched__request.return_value)

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(54123, 101), (datetime.timedelta(minutes=54123), datetime.timedelta(seconds=101)), (54123.0, 101.4)],
    )
    async def test_create_thread(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        auto_archive_duration: time.Intervalish,
        rate_limit_per_user: time.Intervalish,
    ):
        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=4560)
        expected_payload = {
            "name": "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            "auto_archive_duration": 54123,
            "type": 10,
            "invitable": True,
            "rate_limit_per_user": 101,
        }

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "54123123", "name": "dlksksldalksad"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_thread"
            ) as patched_deserialize_guild_thread,
        ):
            result = await rest_client.create_thread(
                mock_guild_text_channel,
                channels.ChannelType.GUILD_NEWS_THREAD,
                "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
                auto_archive_duration=auto_archive_duration,
                invitable=True,
                rate_limit_per_user=rate_limit_per_user,
                reason="think of the catgirls!!! >:3",
            )

            assert result is patched_deserialize_guild_thread.return_value
            patched__request.assert_awaited_once_with(
                expected_route, json=expected_payload, reason="think of the catgirls!!! >:3"
            )
            patched_deserialize_guild_thread.assert_called_once_with(patched__request.return_value)

    async def test_create_thread_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=4560)
        expected_payload = {
            "name": "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            "auto_archive_duration": 1440,
            "type": 12,
        }

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "54123123", "name": "dlksksldalksad"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_thread"
            ) as patched_deserialize_guild_thread,
        ):
            result = await rest_client.create_thread(
                mock_guild_text_channel,
                channels.ChannelType.GUILD_PRIVATE_THREAD,
                "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            )

            assert result is patched_deserialize_guild_thread.return_value
            patched__request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
            patched_deserialize_guild_thread.assert_called_once_with(patched__request.return_value)

    async def test_create_thread_with_all_undefined(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=4560)
        expected_payload = {
            "name": "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            "type": 12,
        }

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "54123123", "name": "dlksksldalksad"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_thread"
            ) as patched_deserialize_guild_thread,
        ):
            result = await rest_client.create_thread(
                mock_guild_text_channel,
                channels.ChannelType.GUILD_PRIVATE_THREAD,
                "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
                auto_archive_duration=undefined.UNDEFINED,
            )

            assert result is patched_deserialize_guild_thread.return_value
            patched__request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
            patched_deserialize_guild_thread.assert_called_once_with(patched__request.return_value)

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(54123, 101), (datetime.timedelta(minutes=54123), datetime.timedelta(seconds=101)), (54123.0, 101.4)],
    )
    async def test_create_forum_post_when_no_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        auto_archive_duration: time.Intervalish,
        rate_limit_per_user: time.Intervalish,
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()

        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=4560)
        expected_payload = {
            "name": "Post with secret content!",
            "auto_archive_duration": 54123,
            "rate_limit_per_user": 101,
            "applied_tags": ["12220", "12201"],
            "message": mock_body,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"some": "message"}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_public_thread"
            ) as patched_deserialize_guild_public_thread,
        ):
            result = await rest_client.create_forum_post(
                mock_guild_text_channel,
                "Post with secret content!",
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                poll=poll_obj,
                sticker=132543,
                stickers=[654234, 123321],
                tts=True,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                flags=54123,
                auto_archive_duration=auto_archive_duration,
                rate_limit_per_user=rate_limit_per_user,
                tags=[snowflakes.Snowflake(12220), snowflakes.Snowflake(12201)],
                reason="Secrets!!",
            )

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            sticker=132543,
            stickers=[654234, 123321],
            tts=True,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=54123,
        )

        assert result is patched_deserialize_guild_public_thread.return_value
        patched__request.assert_awaited_once_with(expected_route, json=expected_payload, reason="Secrets!!")
        patched_deserialize_guild_public_thread.assert_called_once_with(patched__request.return_value)

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(54123, 101), (datetime.timedelta(minutes=54123), datetime.timedelta(seconds=101)), (54123.0, 101.4)],
    )
    async def test_create_forum_post_when_form(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_text_channel: channels.GuildTextChannel,
        auto_archive_duration: time.Intervalish,
        rate_limit_per_user: time.Intervalish,
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()
        mock_body = {"mock": "message body"}
        mock_form = mock.Mock()

        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=4560)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"some": "message"}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_public_thread"
            ) as patched_deserialize_guild_public_thread,
        ):
            result = await rest_client.create_forum_post(
                mock_guild_text_channel,
                "Post with secret content!",
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                poll=poll_obj,
                sticker=314542,
                stickers=[56234, 123312],
                tts=True,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                flags=54123,
                auto_archive_duration=auto_archive_duration,
                rate_limit_per_user=rate_limit_per_user,
                tags=[snowflakes.Snowflake(12220), snowflakes.Snowflake(12201)],
                reason="Secrets!!",
            )
            assert result is patched_deserialize_guild_public_thread.return_value

        patched__build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            sticker=314542,
            stickers=[56234, 123312],
            tts=True,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=54123,
        )

        mock_form.add_field.assert_called_once_with(
            "payload_json",
            b'{"name":"Post with secret content!","auto_archive_duration":54123,"rate_limit_per_user":101,'
            b'"applied_tags":["12220","12201"],"message":{"mock":"message body"}}',
            content_type="application/json",
        )
        patched__request.assert_awaited_once_with(expected_route, form_builder=mock_form, reason="Secrets!!")
        patched_deserialize_guild_public_thread.assert_called_once_with(patched__request.return_value)

    async def test_join_thread(
        self, rest_client: rest.RESTClientImpl, mock_guild_text_channel: channels.GuildTextChannel
    ):
        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.join_thread(mock_guild_text_channel)

            patched__request.assert_awaited_once_with(routes.PUT_MY_THREAD_MEMBER.compile(channel=4560))

    async def test_add_thread_member(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_public_thread_channel: channels.GuildThreadChannel,
        mock_user: users.User,
    ):
        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            # why is 8 afraid of 6 and 7?
            await rest_client.add_thread_member(mock_guild_public_thread_channel, mock_user)

            patched__request.assert_awaited_once_with(routes.PUT_THREAD_MEMBER.compile(channel=45611, user=789))

    async def test_leave_thread(
        self, rest_client: rest.RESTClientImpl, mock_guild_public_thread_channel: channels.GuildThreadChannel
    ):
        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.leave_thread(mock_guild_public_thread_channel)

            patched__request.assert_awaited_once_with(routes.DELETE_MY_THREAD_MEMBER.compile(channel=45611))

    async def test_remove_thread_member(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_public_thread_channel: channels.GuildThreadChannel,
        mock_user: users.User,
    ):
        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.remove_thread_member(mock_guild_public_thread_channel, mock_user)

            patched__request.assert_awaited_once_with(routes.DELETE_THREAD_MEMBER.compile(channel=45611, user=789))

    async def test_fetch_thread_member(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_public_thread_channel: channels.GuildThreadChannel,
        mock_user: users.User,
    ):
        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "9239292", "user_id": "949494"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_thread_member"
            ) as patched_deserialize_thread_member,
        ):
            result = await rest_client.fetch_thread_member(mock_guild_public_thread_channel, mock_user)

            assert result is patched_deserialize_thread_member.return_value
            patched_deserialize_thread_member.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(routes.GET_THREAD_MEMBER.compile(channel=45611, user=789))

    async def test_fetch_thread_members(
        self, rest_client: rest.RESTClientImpl, mock_guild_public_thread_channel: channels.GuildThreadChannel
    ):
        mock_payload_1 = mock.Mock()
        mock_payload_2 = mock.Mock()
        mock_payload_3 = mock.Mock()
        mock_member_1 = mock.Mock()
        mock_member_2 = mock.Mock()
        mock_member_3 = mock.Mock()

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value=[mock_payload_1, mock_payload_2, mock_payload_3],
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_thread_member",
                side_effect=[mock_member_1, mock_member_2, mock_member_3],
            ) as patched_deserialize_thread_member,
        ):
            result = await rest_client.fetch_thread_members(mock_guild_public_thread_channel)

            assert result == [mock_member_1, mock_member_2, mock_member_3]
            patched__request.assert_awaited_once_with(routes.GET_THREAD_MEMBERS.compile(channel=45611))
            patched_deserialize_thread_member.assert_has_calls(
                [mock.call(mock_payload_1), mock.call(mock_payload_2), mock.call(mock_payload_3)]
            )

    @pytest.mark.skip(reason="TODO")
    async def test_fetch_active_threads(self, rest_client: rest.RESTClientImpl): ...

    async def test_reposition_channels(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.PATCH_GUILD_CHANNELS.compile(guild=123)
        expected_json = [{"id": "456", "position": 1}, {"id": "789", "position": 2}]

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.reposition_channels(
                mock_partial_guild, {1: make_guild_text_channel(456), 2: make_guild_text_channel(789)}
            )

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)

    async def test_fetch_member(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        member = mock.Mock(guilds.Member, id=789)
        expected_route = routes.GET_GUILD_MEMBER.compile(guild=123, user=789)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_member", return_value=member
            ) as patched_deserialize_member,
        ):
            assert await rest_client.fetch_member(mock_partial_guild, mock_user) == member

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_member.assert_called_once_with({"id": "789"}, guild_id=123)

    async def test_fetch_my_member(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.GET_MY_GUILD_MEMBER.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "595995"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            result = await rest_client.fetch_my_member(mock_partial_guild)

            assert result is patched_deserialize_member.return_value
            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_member.assert_called_once_with(patched__request.return_value, guild_id=123)

    async def test_search_members(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        member = mock.Mock(guilds.Member, id=645234123)
        expected_route = routes.GET_GUILD_MEMBERS_SEARCH.compile(guild=123)
        expected_query = {"query": "a name", "limit": "1000"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "764435"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_member", return_value=member
            ) as patched_deserialize_member,
        ):
            assert await rest_client.search_members(mock_partial_guild, "a name") == [member]

            patched_deserialize_member.assert_called_once_with({"id": "764435"}, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, query=expected_query)

    async def test_edit_member(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_voice_channel: channels.GuildVoiceChannel,
        mock_user: users.User,
    ):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=789)
        expected_json = {
            "nick": "test",
            "roles": ["654", "321"],
            "mute": True,
            "deaf": False,
            "channel_id": "4562",
            "communication_disabled_until": "2021-10-18T07:18:11.554023+00:00",
        }
        mock_timestamp = datetime.datetime(2021, 10, 18, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            result = await rest_client.edit_member(
                mock_partial_guild,
                mock_user,
                nickname="test",
                roles=[make_partial_role(654), make_partial_role(321)],
                mute=True,
                deaf=False,
                voice_channel=mock_guild_voice_channel,
                communication_disabled_until=mock_timestamp,
                reason="because i can",
            )
            assert result is patched_deserialize_member.return_value

            patched_deserialize_member.assert_called_once_with(patched__request.return_value, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_member_when_voice_channel_is_None(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=789)
        expected_json = {"nick": "test", "roles": ["654", "321"], "mute": True, "deaf": False, "channel_id": None}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            result = await rest_client.edit_member(
                mock_partial_guild,
                mock_user,
                nickname="test",
                roles=[make_partial_role(654), make_partial_role(321)],
                mute=True,
                deaf=False,
                voice_channel=None,
                reason="because i can",
            )
            assert result is patched_deserialize_member.return_value

            patched_deserialize_member.assert_called_once_with(patched__request.return_value, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_member_when_communication_disabled_until_is_None(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=789)
        expected_json = {"communication_disabled_until": None}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            result = await rest_client.edit_member(
                mock_partial_guild, mock_user, communication_disabled_until=None, reason="because i can"
            )
            assert result is patched_deserialize_member.return_value

            patched_deserialize_member.assert_called_once_with(patched__request.return_value, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_member_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=789)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            result = await rest_client.edit_member(mock_partial_guild, mock_user)
            assert result is patched_deserialize_member.return_value

            patched_deserialize_member.assert_called_once_with(patched__request.return_value, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)

    async def test_my_edit_member(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.PATCH_MY_GUILD_MEMBER.compile(guild=123)
        expected_json = {"nick": "test"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            result = await rest_client.edit_my_member(mock_partial_guild, nickname="test", reason="because i can")
            assert result is patched_deserialize_member.return_value

            patched_deserialize_member.assert_called_once_with(patched__request.return_value, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_my_member_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.PATCH_MY_GUILD_MEMBER.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_member") as patched_deserialize_member,
        ):
            result = await rest_client.edit_my_member(mock_partial_guild)
            assert result is patched_deserialize_member.return_value

            patched_deserialize_member.assert_called_once_with(patched__request.return_value, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)

    async def test_add_role_to_member(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_user: users.User,
        mock_partial_role: guilds.PartialRole,
    ):
        expected_route = routes.PUT_GUILD_MEMBER_ROLE.compile(guild=123, user=789, role=333)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.add_role_to_member(
                mock_partial_guild, mock_user, mock_partial_role, reason="because i can"
            )

            patched__request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_remove_role_from_member(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_user: users.User,
        mock_partial_role: guilds.PartialRole,
    ):
        expected_route = routes.DELETE_GUILD_MEMBER_ROLE.compile(guild=123, user=789, role=333)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.remove_role_from_member(
                mock_partial_guild, mock_user, mock_partial_role, reason="because i can"
            )

            patched__request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_kick_user(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        expected_route = routes.DELETE_GUILD_MEMBER.compile(guild=123, user=789)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.kick_user(mock_partial_guild, mock_user, reason="because i can")

            patched__request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_ban_user(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        expected_route = routes.PUT_GUILD_BAN.compile(guild=123, user=789)
        expected_json = {"delete_message_seconds": 604800}

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.ban_user(
                mock_partial_guild, mock_user, delete_message_seconds=604800, reason="because i can"
            )

            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_unban_user(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        expected_route = routes.DELETE_GUILD_BAN.compile(guild=123, user=789)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.unban_user(mock_partial_guild, mock_user, reason="because i can")

            patched__request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_fetch_ban(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild, mock_user: users.User
    ):
        ban = mock.Mock(guilds.GuildBan)
        expected_route = routes.GET_GUILD_BAN.compile(guild=123, user=789)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_member_ban", return_value=ban
            ) as patched_deserialize_guild_member_ban,
        ):
            assert await rest_client.fetch_ban(mock_partial_guild, mock_user) == ban

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_guild_member_ban.assert_called_once_with({"id": "789"})

    async def test_fetch_roles(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        role1 = make_partial_role(456)
        role2 = make_partial_role(789)
        expected_route = routes.GET_GUILD_ROLES.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_role", side_effect=[role1, role2]
            ) as patched_deserialize_role,
        ):
            assert await rest_client.fetch_roles(mock_partial_guild) == [role1, role2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_role.call_count == 2
            patched_deserialize_role.assert_has_calls(
                [mock.call({"id": "456"}, guild_id=123), mock.call({"id": "789"}, guild_id=123)]
            )

    async def test_create_role(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.POST_GUILD_ROLES.compile(guild=123)
        expected_json = {
            "name": "admin",
            "permissions": 8,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "icon": "some data",
            "mentionable": False,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_role") as patched_deserialize_role,
        ):
            returned = await rest_client.create_role(
                mock_partial_guild,
                name="admin",
                permissions=permissions.Permissions.ADMINISTRATOR,
                color=colors.Color.from_int(12345),
                hoist=True,
                icon="icon.png",
                mentionable=False,
                reason="roles are cool",
            )
            assert returned is patched_deserialize_role.return_value

            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="roles are cool")
            patched_deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_create_role_when_permissions_undefined(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_role: guilds.PartialRole,
    ):
        expected_route = routes.POST_GUILD_ROLES.compile(guild=123)
        expected_json = {
            "name": "admin",
            "permissions": 0,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "mentionable": False,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_role", return_value=mock_partial_role
            ) as patched_deserialize_role,
        ):
            returned = await rest_client.create_role(
                mock_partial_guild,
                name="admin",
                color=colors.Color.from_int(12345),
                hoist=True,
                mentionable=False,
                reason="roles are cool",
            )
            assert returned is mock_partial_role

            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="roles are cool")
            patched_deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_create_role_when_color_and_colour_specified(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        with pytest.raises(TypeError, match=r"Can not specify 'color' and 'colour' together."):
            await rest_client.create_role(
                mock_partial_guild, color=colors.Color.from_int(12345), colour=colors.Color.from_int(12345)
            )

    async def test_create_role_when_icon_unicode_emoji_specified(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        with pytest.raises(TypeError, match=r"Can not specify 'icon' and 'unicode_emoji' together."):
            await rest_client.create_role(mock_partial_guild, icon="icon.png", unicode_emoji="\N{OK HAND SIGN}")

    async def test_reposition_roles(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.PATCH_GUILD_ROLES.compile(guild=123)
        expected_json = [{"id": "456", "position": 1}, {"id": "789", "position": 2}]

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.reposition_roles(
                mock_partial_guild, {1: make_partial_role(456), 2: make_partial_role(789)}
            )

            patched__request.assert_awaited_once_with(expected_route, json=expected_json)

    async def test_edit_role(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_role: guilds.PartialRole,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.PATCH_GUILD_ROLE.compile(guild=123, role=333)
        expected_json = {
            "name": "admin",
            "permissions": 8,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "icon": "some data",
            "mentionable": False,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_role") as patched_deserialize_role,
        ):
            returned = await rest_client.edit_role(
                mock_partial_guild,
                mock_partial_role,
                name="admin",
                permissions=permissions.Permissions.ADMINISTRATOR,
                color=colors.Color.from_int(12345),
                hoist=True,
                icon="icon.png",
                mentionable=False,
                reason="roles are cool",
            )
            assert returned is patched_deserialize_role.return_value

            patched__request.assert_awaited_once_with(expected_route, json=expected_json, reason="roles are cool")
            patched_deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_edit_role_when_color_and_colour_specified(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_role: guilds.PartialRole,
    ):
        with pytest.raises(TypeError, match=r"Can not specify 'color' and 'colour' together."):
            await rest_client.edit_role(
                mock_partial_guild,
                mock_partial_role,
                color=colors.Color.from_int(12345),
                colour=colors.Color.from_int(12345),
            )

    async def test_edit_role_when_icon_and_unicode_emoji_specified(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_role: guilds.PartialRole,
    ):
        with pytest.raises(TypeError, match=r"Can not specify 'icon' and 'unicode_emoji' together."):
            await rest_client.edit_role(
                mock_partial_guild, mock_partial_role, icon="icon.png", unicode_emoji="\N{OK HAND SIGN}"
            )

    async def test_delete_role(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_partial_role: guilds.PartialRole,
    ):
        expected_route = routes.DELETE_GUILD_ROLE.compile(guild=123, role=333)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_role(mock_partial_guild, mock_partial_role)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_estimate_guild_prune_count(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.GET_GUILD_PRUNE.compile(guild=123)
        expected_query = {"days": "1"}

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"pruned": "69"}
        ) as patched__request:
            assert await rest_client.estimate_guild_prune_count(mock_partial_guild, days=1) == 69
            patched__request.assert_awaited_once_with(expected_route, query=expected_query)

    async def test_estimate_guild_prune_count_with_include_roles(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.GET_GUILD_PRUNE.compile(guild=123)
        expected_query = {"days": "1", "include_roles": "456,678"}

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"pruned": "69"}
        ) as patched__request:
            returned = await rest_client.estimate_guild_prune_count(
                mock_partial_guild, days=1, include_roles=[make_partial_role(456), make_partial_role(678)]
            )
            assert returned == 69

            patched__request.assert_awaited_once_with(expected_route, query=expected_query)

    async def test_begin_guild_prune(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.POST_GUILD_PRUNE.compile(guild=123)
        expected_json = {"days": 1, "compute_prune_count": True, "include_roles": ["456", "678"]}

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"pruned": "69"}
        ) as patched__request:
            returned = await rest_client.begin_guild_prune(
                mock_partial_guild,
                days=1,
                compute_prune_count=True,
                include_roles=[make_partial_role(456), make_partial_role(678)],
                reason="cause inactive people bad",
            )
            assert returned == 69

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason="cause inactive people bad"
            )

    async def test_fetch_guild_voice_regions(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        voice_region1 = mock.Mock(voices.VoiceRegion, id="456")
        voice_region2 = mock.Mock(voices.VoiceRegion, id="789")
        expected_route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_voice_region", side_effect=[voice_region1, voice_region2]
            ) as patched_deserialize_voice_region,
        ):
            assert await rest_client.fetch_guild_voice_regions(mock_partial_guild) == [voice_region1, voice_region2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_voice_region.call_count == 2
            patched_deserialize_voice_region.assert_has_calls([mock.call({"id": "456"}), mock.call({"id": "789"})])

    async def test_fetch_guild_invites(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        invite1 = make_invite_with_metadata("ashdfjhas")
        invite2 = make_invite_with_metadata("asdjfhasj")
        expected_route = routes.GET_GUILD_INVITES.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_invite_with_metadata", side_effect=[invite1, invite2]
            ) as patched_deserialize_invite_with_metadata,
        ):
            assert await rest_client.fetch_guild_invites(mock_partial_guild) == [invite1, invite2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_invite_with_metadata.call_count == 2
            patched_deserialize_invite_with_metadata.assert_has_calls(
                [mock.call({"id": "456"}), mock.call({"id": "789"})]
            )

    async def test_fetch_integrations(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        integration1 = mock.Mock(guilds.Integration, id=456)
        integration2 = mock.Mock(guilds.Integration, id=789)
        expected_route = routes.GET_GUILD_INTEGRATIONS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "456"}, {"id": "789"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_integration", side_effect=[integration1, integration2]
            ) as patched_deserialize_integration,
        ):
            assert await rest_client.fetch_integrations(mock_partial_guild) == [integration1, integration2]

            patched__request.assert_awaited_once_with(expected_route)
            assert patched_deserialize_integration.call_count == 2
            patched_deserialize_integration.assert_has_calls(
                [mock.call({"id": "456"}, guild_id=123), mock.call({"id": "789"}, guild_id=123)]
            )

    async def test_fetch_widget(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        widget = mock.Mock(guilds.GuildWidget, id=23847293)
        expected_route = routes.GET_GUILD_WIDGET.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_widget", return_value=widget
            ) as patched_deserialize_guild_widget,
        ):
            assert await rest_client.fetch_widget(mock_partial_guild) == widget

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_guild_widget.assert_called_once_with({"id": "789"})

    async def test_edit_widget(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_text_channel: channels.GuildTextChannel,
    ):
        widget = mock.Mock(guilds.GuildWidget, id=456)
        expected_route = routes.PATCH_GUILD_WIDGET.compile(guild=123)
        expected_json = {"enabled": True, "channel": "4560"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_widget", return_value=widget
            ) as patched_deserialize_guild_widget,
        ):
            returned = await rest_client.edit_widget(
                mock_partial_guild,
                channel=mock_guild_text_channel,
                enabled=True,
                reason="this should have been enabled",
            )
            assert returned is widget

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason="this should have been enabled"
            )
            patched_deserialize_guild_widget.assert_called_once_with({"id": "456"})

    async def test_edit_widget_when_channel_is_None(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        widget = mock.Mock(guilds.GuildWidget, id=456)
        expected_route = routes.PATCH_GUILD_WIDGET.compile(guild=123)
        expected_json = {"enabled": True, "channel": None}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_widget", return_value=widget
            ) as patched_deserialize_guild_widget,
        ):
            returned = await rest_client.edit_widget(
                mock_partial_guild, channel=None, enabled=True, reason="this should have been enabled"
            )
            assert returned is widget

            patched__request.assert_awaited_once_with(
                expected_route, json=expected_json, reason="this should have been enabled"
            )
            patched_deserialize_guild_widget.assert_called_once_with({"id": "456"})

    async def test_edit_widget_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        widget = mock.Mock(guilds.GuildWidget, id=456)
        expected_route = routes.PATCH_GUILD_WIDGET.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "456"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_widget", return_value=widget
            ) as patched_deserialize_guild_widget,
        ):
            assert await rest_client.edit_widget(mock_partial_guild) == widget

            patched__request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)
            patched_deserialize_guild_widget.assert_called_once_with({"id": "456"})

    async def test_fetch_welcome_screen(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.GET_GUILD_WELCOME_SCREEN.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"haha": "funny"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_welcome_screen"
            ) as patched_deserialize_welcome_screen,
        ):
            result = await rest_client.fetch_welcome_screen(mock_partial_guild)
            assert result is patched_deserialize_welcome_screen.return_value

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_welcome_screen.assert_called_once_with(patched__request.return_value)

    async def test_edit_welcome_screen_with_optional_kwargs(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        mock_channel = mock.Mock()
        expected_route = routes.PATCH_GUILD_WELCOME_SCREEN.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"go": "home", "you're": "drunk"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_welcome_screen"
            ) as patched_deserialize_welcome_screen,
            mock.patch.object(
                rest_client.entity_factory, "serialize_welcome_channel"
            ) as patched_serialize_welcome_channel,
        ):
            result = await rest_client.edit_welcome_screen(
                mock_partial_guild, description="blam blam", enabled=True, channels=[mock_channel]
            )
            assert result is patched_deserialize_welcome_screen.return_value

            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "description": "blam blam",
                    "enabled": True,
                    "welcome_channels": [patched_serialize_welcome_channel.return_value],
                },
            )
            patched_deserialize_welcome_screen.assert_called_once_with(patched__request.return_value)
            patched_serialize_welcome_channel.assert_called_once_with(mock_channel)

    async def test_edit_welcome_screen_with_null_kwargs(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.PATCH_GUILD_WELCOME_SCREEN.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"go": "go", "power": "rangers"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_welcome_screen"
            ) as patched_deserialize_welcome_screen,
            mock.patch.object(
                rest_client.entity_factory, "serialize_welcome_channel"
            ) as patched_serialize_welcome_channel,
        ):
            result = await rest_client.edit_welcome_screen(mock_partial_guild, description=None, channels=None)
            assert result is patched_deserialize_welcome_screen.return_value

            patched__request.assert_awaited_once_with(
                expected_route, json={"description": None, "welcome_channels": None}
            )
            patched_deserialize_welcome_screen.assert_called_once_with(patched__request.return_value)
            patched_serialize_welcome_channel.assert_not_called()

    async def test_edit_welcome_screen_without_optional_kwargs(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.PATCH_GUILD_WELCOME_SCREEN.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"screen": "NBO"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_welcome_screen"
            ) as patched_deserialize_welcome_screen,
            mock.patch.object(rest_client.entity_factory, "serialize_welcome_channel"),
        ):
            result = await rest_client.edit_welcome_screen(mock_partial_guild)
            assert result is patched_deserialize_welcome_screen.return_value

            patched__request.assert_awaited_once_with(expected_route, json={})
            patched_deserialize_welcome_screen.assert_called_once_with(patched__request.return_value)

    async def test_fetch_vanity_url(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        vanity_url = mock.Mock(invites.VanityURL, code="asdhfjkahsd")
        expected_route = routes.GET_GUILD_VANITY_URL.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "789"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_vanity_url", return_value=vanity_url
            ) as patched_deserialize_vanity_url,
        ):
            assert await rest_client.fetch_vanity_url(mock_partial_guild) == vanity_url

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_vanity_url.assert_called_once_with({"id": "789"})

    async def test_fetch_template(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.GET_TEMPLATE.compile(template="kodfskoijsfikoiok")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "KSDAOKSDKIO"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.fetch_template("kodfskoijsfikoiok")
            assert result is patched_deserialize_template.return_value

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_template.assert_called_once_with({"code": "KSDAOKSDKIO"})

    async def test_fetch_guild_templates(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.GET_GUILD_TEMPLATES.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"code": "jirefu98ai90w"}]
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.fetch_guild_templates(mock_partial_guild)
            assert result == [patched_deserialize_template.return_value]

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_template.assert_called_once_with({"code": "jirefu98ai90w"})

    async def test_sync_guild_template(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.PUT_GUILD_TEMPLATE.compile(guild=123, template="oeroeoeoeoeo")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "ldsaosdokskdoa"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.sync_guild_template(mock_partial_guild, template="oeroeoeoeoeo")
            assert result is patched_deserialize_template.return_value

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_template.assert_called_once_with({"code": "ldsaosdokskdoa"})

    async def test_create_guild_from_template_without_icon(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TEMPLATE.compile(template="odkkdkdkd")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "543123123"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_rest_guild") as patched_deserialize_rest_guild,
        ):
            result = await rest_client.create_guild_from_template("odkkdkdkd", "ok a name")
            assert result is patched_deserialize_rest_guild.return_value

            patched__request.assert_awaited_once_with(expected_route, json={"name": "ok a name"})
            patched_deserialize_rest_guild.assert_called_once_with({"id": "543123123"})

    async def test_create_guild_from_template_with_icon(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_TEMPLATE.compile(template="odkkdkdkd")
        icon_resource = MockFileResource("icon data")

        with (
            mock.patch.object(files, "ensure_resource", return_value=icon_resource),
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "543123123"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_rest_guild") as patched_deserialize_rest_guild,
        ):
            result = await rest_client.create_guild_from_template("odkkdkdkd", "ok a name", icon="icon.png")
            assert result is patched_deserialize_rest_guild.return_value

        patched__request.assert_awaited_once_with(expected_route, json={"name": "ok a name", "icon": "icon data"})
        patched_deserialize_rest_guild.assert_called_once_with({"id": "543123123"})

    async def test_create_template_without_description(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_routes = routes.POST_GUILD_TEMPLATES.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "94949sdfkds"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.create_template(mock_partial_guild, "OKOKOK")
            assert result is patched_deserialize_template.return_value

            patched__request.assert_awaited_once_with(expected_routes, json={"name": "OKOKOK"})
            patched_deserialize_template.assert_called_once_with({"code": "94949sdfkds"})

    async def test_create_template_with_description(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.POST_GUILD_TEMPLATES.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "76345345"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.create_template(mock_partial_guild, "33", description="43123123")
            assert result is patched_deserialize_template.return_value

            patched__request.assert_awaited_once_with(expected_route, json={"name": "33", "description": "43123123"})
            patched_deserialize_template.assert_called_once_with({"code": "76345345"})

    async def test_edit_template_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.PATCH_GUILD_TEMPLATE.compile(guild=123, template="oeodsosda")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "9493293ikiwopop"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.edit_template(mock_partial_guild, "oeodsosda")
            assert result is patched_deserialize_template.return_value

            patched__request.assert_awaited_once_with(expected_route, json={})
            patched_deserialize_template.assert_called_once_with({"code": "9493293ikiwopop"})

    async def test_edit_template_with_optionals(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.PATCH_GUILD_TEMPLATE.compile(guild=123, template="oeodsosda2")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "9493293ikiwopop"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.edit_template(
                mock_partial_guild, "oeodsosda2", name="new name", description="i'm lazy"
            )
            assert result is patched_deserialize_template.return_value

            patched__request.assert_awaited_once_with(
                expected_route, json={"name": "new name", "description": "i'm lazy"}
            )
            patched_deserialize_template.assert_called_once_with({"code": "9493293ikiwopop"})

    async def test_delete_template(self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild):
        expected_route = routes.DELETE_GUILD_TEMPLATE.compile(guild=123, template="eoiesri9er99")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"code": "oeoekfgkdkf"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_template") as patched_deserialize_template,
        ):
            result = await rest_client.delete_template(mock_partial_guild, "eoiesri9er99")
            assert result is patched_deserialize_template.return_value

            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_template.assert_called_once_with({"code": "oeoekfgkdkf"})

    async def test_fetch_application_command_with_guild(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.GET_APPLICATION_GUILD_COMMAND.compile(application=111, guild=123, command=666)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "424242"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.fetch_application_command(
                mock_application, mock_partial_command, mock_partial_guild
            )

            assert result is patched_deserialize_command.return_value
            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_command.assert_called_once_with(patched__request.return_value, guild_id=123)

    async def test_fetch_application_command_without_guild(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.GET_APPLICATION_COMMAND.compile(application=111, command=666)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "424242"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.fetch_application_command(mock_application, mock_partial_command)

            assert result is patched_deserialize_command.return_value
            patched__request.assert_awaited_once_with(expected_route)
            patched_deserialize_command.assert_called_once_with(patched__request.return_value, guild_id=None)

    async def test_fetch_application_commands_with_guild(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        expected_route = routes.GET_APPLICATION_GUILD_COMMANDS.compile(application=111, guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "34512312"}]
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.fetch_application_commands(mock_application, mock_partial_guild)

            assert result == [patched_deserialize_command.return_value]
            patched__request.assert_awaited_once_with(expected_route, query={"with_localizations": "true"})
            patched_deserialize_command.assert_called_once_with({"id": "34512312"}, guild_id=123)

    async def test_fetch_application_commands_without_guild(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        expected_route = routes.GET_APPLICATION_COMMANDS.compile(application=111)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "34512312"}]
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.fetch_application_commands(mock_application)

            assert result == [patched_deserialize_command.return_value]
            patched__request.assert_awaited_once_with(expected_route, query={"with_localizations": "true"})
            patched_deserialize_command.assert_called_once_with({"id": "34512312"}, guild_id=None)

    async def test_fetch_application_commands_ignores_unknown_command_types(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        mock_command = mock.Mock()
        expected_route = routes.GET_APPLICATION_GUILD_COMMANDS.compile(application=111, guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "541234"}, {"id": "553234"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_command",
                side_effect=[errors.UnrecognisedEntityError("eep"), mock_command],
            ) as patched_deserialize_command,
        ):
            result = await rest_client.fetch_application_commands(mock_application, mock_partial_guild)

            assert result == [mock_command]
            patched__request.assert_awaited_once_with(expected_route, query={"with_localizations": "true"})
            patched_deserialize_command.assert_has_calls(
                [mock.call({"id": "541234"}, guild_id=123), mock.call({"id": "553234"}, guild_id=123)]
            )

    async def test__create_application_command_with_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        expected_route = routes.POST_APPLICATION_GUILD_COMMAND.compile(application=111, guild=123)
        mock_option = mock.Mock()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "29393939"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "serialize_command_option"
            ) as patched_serialize_command_option,
        ):
            result = await rest_client._create_application_command(
                application=mock_application,
                type=100,
                name="okokok",
                description="not ok anymore",
                guild=mock_partial_guild,
                options=[mock_option],
                default_member_permissions=permissions.Permissions.ADMINISTRATOR,
                nsfw=True,
            )

            assert result is patched__request.return_value
            patched_serialize_command_option.assert_called_once_with(mock_option)
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "type": 100,
                    "name": "okokok",
                    "description": "not ok anymore",
                    "options": [patched_serialize_command_option.return_value],
                    "default_member_permissions": 8,
                    "nsfw": True,
                },
            )

    async def test_create_application_command_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        expected_route = routes.POST_APPLICATION_COMMAND.compile(application=111)

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "29393939"}
        ) as patched__request:
            result = await rest_client._create_application_command(
                application=mock_application, type=100, name="okokok", description="not ok anymore"
            )

            assert result is patched__request.return_value
            patched__request.assert_awaited_once_with(
                expected_route, json={"type": 100, "name": "okokok", "description": "not ok anymore"}
            )

    async def test__create_application_command_standardizes_default_member_permissions(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        expected_route = routes.POST_APPLICATION_COMMAND.compile(application=111)

        with mock.patch.object(
            rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "29393939"}
        ) as patched__request:
            result = await rest_client._create_application_command(
                application=mock_application,
                type=100,
                name="okokok",
                description="not ok anymore",
                default_member_permissions=permissions.Permissions.NONE,
            )

            assert result is patched__request.return_value
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "type": 100,
                    "name": "okokok",
                    "description": "not ok anymore",
                    "default_member_permissions": None,
                },
            )

    async def test_create_slash_command(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        mock_options = mock.Mock()

        with (
            mock.patch.object(
                rest_client.entity_factory, "deserialize_slash_command"
            ) as patched_deserialize_slash_command,
            mock.patch.object(rest_client, "_create_application_command") as patched__create_application_command,
        ):
            result = await rest_client.create_slash_command(
                mock_application,
                "okokok",
                "not ok anymore",
                guild=mock_partial_guild,
                options=mock_options,
                name_localizations={locales.Locale.TR: "hhh"},
                description_localizations={locales.Locale.TR: "jello"},
                default_member_permissions=permissions.Permissions.ADMINISTRATOR,
                nsfw=True,
            )

            assert result is patched_deserialize_slash_command.return_value
            patched_deserialize_slash_command.assert_called_once_with(
                patched__create_application_command.return_value, guild_id=123
            )
            patched__create_application_command.assert_awaited_once_with(
                application=mock_application,
                type=commands.CommandType.SLASH,
                name="okokok",
                description="not ok anymore",
                guild=mock_partial_guild,
                options=mock_options,
                name_localizations={"tr": "hhh"},
                description_localizations={"tr": "jello"},
                default_member_permissions=permissions.Permissions.ADMINISTRATOR,
                nsfw=True,
            )

    async def test_create_context_menu_command(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        with (
            mock.patch.object(
                rest_client.entity_factory, "deserialize_context_menu_command"
            ) as patched_deserialize_context_menu_command,
            mock.patch.object(rest_client, "_create_application_command") as patched__create_application_command,
        ):
            result = await rest_client.create_context_menu_command(
                mock_application,
                commands.CommandType.USER,
                "okokok",
                guild=mock_partial_guild,
                default_member_permissions=permissions.Permissions.ADMINISTRATOR,
                nsfw=True,
                name_localizations={locales.Locale.TR: "hhh"},
            )

            assert result is patched_deserialize_context_menu_command.return_value
            patched_deserialize_context_menu_command.assert_called_once_with(
                patched__create_application_command.return_value, guild_id=123
            )
            patched__create_application_command.assert_awaited_once_with(
                application=mock_application,
                type=commands.CommandType.USER,
                name="okokok",
                guild=mock_partial_guild,
                default_member_permissions=permissions.Permissions.ADMINISTRATOR,
                nsfw=True,
                name_localizations={"tr": "hhh"},
            )

    async def test_set_application_commands_with_guild(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        expected_route = routes.PUT_APPLICATION_GUILD_COMMANDS.compile(application=111, guild=123)
        mock_command_builder = mock.Mock()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "9459329932"}]
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.set_application_commands(
                mock_application, [mock_command_builder], mock_partial_guild
            )

            assert result == [patched_deserialize_command.return_value]
            patched_deserialize_command.assert_called_once_with({"id": "9459329932"}, guild_id=123)
            patched__request.assert_awaited_once_with(expected_route, json=[mock_command_builder.build.return_value])
            mock_command_builder.build.assert_called_once_with(rest_client.entity_factory)

    async def test_set_application_commands_without_guild(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        expected_route = routes.PUT_APPLICATION_COMMANDS.compile(application=111)
        mock_command_builder = mock.Mock()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "9459329932"}]
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.set_application_commands(mock_application, [mock_command_builder])

            assert result == [patched_deserialize_command.return_value]
            patched_deserialize_command.assert_called_once_with({"id": "9459329932"}, guild_id=None)
            patched__request.assert_awaited_once_with(expected_route, json=[mock_command_builder.build.return_value])
            mock_command_builder.build.assert_called_once_with(rest_client.entity_factory)

    async def test_set_application_commands_without_guild_handles_unknown_command_types(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        mock_command = mock.Mock()
        expected_route = routes.PUT_APPLICATION_GUILD_COMMANDS.compile(application=111, guild=123)
        mock_command_builder = mock.Mock()

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value=[{"id": "435765"}, {"id": "4949493933"}],
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_command",
                side_effect=[errors.UnrecognisedEntityError("meow"), mock_command],
            ) as patched_deserialize_command,
        ):
            result = await rest_client.set_application_commands(
                mock_application, [mock_command_builder], mock_partial_guild
            )

            assert result == [mock_command]
            patched_deserialize_command.assert_has_calls(
                [mock.call({"id": "435765"}, guild_id=123), mock.call({"id": "4949493933"}, guild_id=123)]
            )
            patched__request.assert_awaited_once_with(expected_route, json=[mock_command_builder.build.return_value])
            mock_command_builder.build.assert_called_once_with(rest_client.entity_factory)

    async def test_edit_application_command_with_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.PATCH_APPLICATION_GUILD_COMMAND.compile(application=111, guild=123, command=666)
        mock_option = mock.Mock()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "94594994"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
            mock.patch.object(
                rest_client.entity_factory, "serialize_command_option"
            ) as patched_serialize_command_option,
        ):
            result = await rest_client.edit_application_command(
                mock_application,
                mock_partial_command,
                mock_partial_guild,
                name="ok sis",
                description="cancelled",
                options=[mock_option],
                default_member_permissions=permissions.Permissions.BAN_MEMBERS,
            )

            assert result is patched_deserialize_command.return_value
            patched_deserialize_command.assert_called_once_with(patched__request.return_value, guild_id=123)
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "name": "ok sis",
                    "description": "cancelled",
                    "options": [patched_serialize_command_option.return_value],
                    "default_member_permissions": 4,
                },
            )
            patched_serialize_command_option.assert_called_once_with(mock_option)

    async def test_edit_application_command_without_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.PATCH_APPLICATION_COMMAND.compile(application=111, command=666)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "94594994"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.edit_application_command(mock_application, mock_partial_command)

            assert result is patched_deserialize_command.return_value
            patched_deserialize_command.assert_called_once_with(patched__request.return_value, guild_id=None)
            patched__request.assert_awaited_once_with(expected_route, json={})

    async def test_edit_application_command_standardizes_default_member_permissions(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.PATCH_APPLICATION_COMMAND.compile(application=111, command=666)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "94594994"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_command") as patched_deserialize_command,
        ):
            result = await rest_client.edit_application_command(
                mock_application, mock_partial_command, default_member_permissions=permissions.Permissions.NONE
            )

            assert result is patched_deserialize_command.return_value
            patched_deserialize_command.assert_called_once_with(patched__request.return_value, guild_id=None)
            patched__request.assert_awaited_once_with(expected_route, json={"default_member_permissions": None})

    async def test_delete_application_command_with_guild(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.DELETE_APPLICATION_GUILD_COMMAND.compile(application=111, command=666, guild=123)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_application_command(mock_application, mock_partial_command, mock_partial_guild)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_delete_application_command_without_guild(
        self,
        rest_client: rest.RESTClientImpl,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.DELETE_APPLICATION_COMMAND.compile(application=111, command=666)

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_application_command(mock_application, mock_partial_command)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_fetch_application_guild_commands_permissions(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
    ):
        expected_route = routes.GET_APPLICATION_GUILD_COMMANDS_PERMISSIONS.compile(application=111, guild=123)
        mock_command_payload = mock.Mock()

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[mock_command_payload]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_command_permissions"
            ) as patched_deserialize_guild_command_permissions,
        ):
            result = await rest_client.fetch_application_guild_commands_permissions(
                mock_application, mock_partial_guild
            )

            assert result == [patched_deserialize_guild_command_permissions.return_value]
            patched_deserialize_guild_command_permissions.assert_called_once_with(mock_command_payload)
            patched__request.assert_awaited_once_with(expected_route)

    async def test_fetch_application_command_permissions(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        expected_route = routes.GET_APPLICATION_COMMAND_PERMISSIONS.compile(application=111, guild=123, command=666)
        mock_command_payload = {"id": "9393939393"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=mock_command_payload
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_command_permissions"
            ) as patched_deserialize_guild_command_permissions,
        ):
            result = await rest_client.fetch_application_command_permissions(
                mock_application, mock_partial_guild, mock_partial_command
            )

            assert result is patched_deserialize_guild_command_permissions.return_value
            patched_deserialize_guild_command_permissions.assert_called_once_with(mock_command_payload)
            patched__request.assert_awaited_once_with(expected_route)

    async def test_set_application_command_permissions(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_application: applications.Application,
        mock_partial_command: commands.PartialCommand,
    ):
        route = routes.PUT_APPLICATION_COMMAND_PERMISSIONS.compile(application=111, guild=123, command=666)
        mock_permission = mock.Mock()
        mock_command_payload = {"id": "29292929"}

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=mock_command_payload
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_guild_command_permissions"
            ) as patched_deserialize_guild_command_permissions,
            mock.patch.object(
                rest_client.entity_factory, "serialize_command_permission"
            ) as patched_serialize_command_permission,
        ):
            result = await rest_client.set_application_command_permissions(
                mock_application, mock_partial_guild, mock_partial_command, [mock_permission]
            )

            assert result is patched_deserialize_guild_command_permissions.return_value
            patched_deserialize_guild_command_permissions.assert_called_once_with(mock_command_payload)
            patched__request.assert_awaited_once_with(
                route, json={"permissions": [patched_serialize_command_permission.return_value]}
            )

    async def test_fetch_interaction_response(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        expected_route = routes.GET_INTERACTION_RESPONSE.compile(webhook=111, token="go homo or go gnomo")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "94949494949"}
            ) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
        ):
            result = await rest_client.fetch_interaction_response(mock_application, "go homo or go gnomo")

            assert result is patched_deserialize_message.return_value
            patched_deserialize_message.assert_called_once_with(patched__request.return_value)
            patched__request.assert_awaited_once_with(expected_route, auth=None)

    async def test_create_interaction_response_when_form(
        self, rest_client: rest.RESTClientImpl, mock_partial_interaction: interactions.PartialInteraction
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        mock_form.add_field.assert_called_once_with(
            "payload_json", b'{"type":1,"data":{"testing":"ensure_in_test"}}', content_type="application/json"
        )
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=777, token="some token")

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message"),
        ):
            await rest_client.create_interaction_response(
                mock_partial_interaction,
                "some token",
                1,
                "some content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                poll=poll_obj,
                tts=True,
                flags=120,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
            )

        patched__build_message_payload.assert_called_once_with(
            content="some content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )
        patched__request.assert_awaited_once_with(expected_route, form_builder=mock_form, auth=None)

    async def test_create_interaction_response_when_no_form(
        self, rest_client: rest.RESTClientImpl, mock_partial_interaction: interactions.PartialInteraction
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        poll_obj = mock.Mock()

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message"),
        ):
            await rest_client.create_interaction_response(
                mock_partial_interaction,
                "some token",
                1,
                "some content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                poll=poll_obj,
                tts=True,
                flags=120,
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
            )

        patched__build_message_payload.assert_called_once_with(
            content="some content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            poll=poll_obj,
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )
        patched__request.assert_awaited_once_with(
            expected_route, json={"type": 1, "data": {"testing": "ensure_in_test"}}, auth=None
        )

    async def test_edit_interaction_response_when_form(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_INTERACTION_RESPONSE.compile(webhook=111, token="some token")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, mock_form)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
        ):
            returned = await rest_client.edit_interaction_response(
                mock_application,
                "some token",
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                edit=True,
            )
            mock_form.add_field.assert_called_once_with(
                "payload_json", b'{"testing":"ensure_in_test"}', content_type="application/json"
            )
            patched__request.assert_awaited_once_with(expected_route, form_builder=mock_form, auth=None)
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_interaction_response_when_no_form(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        attachment_obj = mock.Mock()
        attachment_obj2 = mock.Mock()
        component_obj = mock.Mock()
        component_obj2 = mock.Mock()
        embed_obj = mock.Mock()
        embed_obj2 = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_INTERACTION_RESPONSE.compile(webhook=111, token="some token")

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"message_id": 123}
            ) as patched__request,
            mock.patch.object(
                rest_client, "_build_message_payload", return_value=(mock_body, None)
            ) as patched__build_message_payload,
            mock.patch.object(rest_client.entity_factory, "deserialize_message") as patched_deserialize_message,
        ):
            returned = await rest_client.edit_interaction_response(
                mock_application,
                "some token",
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
            )
            assert returned is patched_deserialize_message.return_value

            patched__build_message_payload.assert_called_once_with(
                content="new content",
                attachment=attachment_obj,
                attachments=[attachment_obj2],
                component=component_obj,
                components=[component_obj2],
                embed=embed_obj,
                embeds=[embed_obj2],
                mentions_everyone=False,
                user_mentions=[9876],
                role_mentions=[1234],
                edit=True,
            )
            patched__request.assert_awaited_once_with(expected_route, json={"testing": "ensure_in_test"}, auth=None)
            patched_deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_delete_interaction_response(
        self, rest_client: rest.RESTClientImpl, mock_application: applications.Application
    ):
        expected_route = routes.DELETE_INTERACTION_RESPONSE.compile(webhook=111, token="go homo now")

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.delete_interaction_response(mock_application, "go homo now")

            patched__request.assert_awaited_once_with(expected_route, auth=None)

    async def test_create_autocomplete_response(
        self, rest_client: rest.RESTClientImpl, mock_partial_interaction: interactions.PartialInteraction
    ):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=777, token="snek")

        choices = [
            special_endpoints.AutocompleteChoiceBuilder(name="c", value="d"),
            special_endpoints.AutocompleteChoiceBuilder(name="eee", value="fff"),
        ]

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.create_autocomplete_response(mock_partial_interaction, "snek", choices)

            patched__request.assert_awaited_once_with(
                expected_route,
                json={"type": 8, "data": {"choices": [{"name": "c", "value": "d"}, {"name": "eee", "value": "fff"}]}},
                auth=None,
            )

    async def test_create_autocomplete_response_for_deprecated_command_choices(
        self, rest_client: rest.RESTClientImpl, mock_partial_interaction: interactions.PartialInteraction
    ):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=777, token="snek")

        choices = [
            special_endpoints.AutocompleteChoiceBuilder(name="a", value="b"),
            special_endpoints.AutocompleteChoiceBuilder(name="foo", value="bar"),
        ]

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.create_autocomplete_response(mock_partial_interaction, "snek", choices)

            patched__request.assert_awaited_once_with(
                expected_route,
                json={"type": 8, "data": {"choices": [{"name": "a", "value": "b"}, {"name": "foo", "value": "bar"}]}},
                auth=None,
            )

    async def test_create_modal_response(
        self, rest_client: rest.RESTClientImpl, mock_partial_interaction: interactions.PartialInteraction
    ):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=777, token="snek")
        component = mock.Mock()

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.create_modal_response(
                mock_partial_interaction, "snek", title="title", custom_id="idd", component=component
            )

            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "type": 9,
                    "data": {"title": "title", "custom_id": "idd", "components": [component.build.return_value]},
                },
                auth=None,
            )

    async def test_create_modal_response_with_plural_args(
        self, rest_client: rest.RESTClientImpl, mock_partial_interaction: interactions.PartialInteraction
    ):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=777, token="snek")
        component = mock.Mock()

        with mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request:
            await rest_client.create_modal_response(
                mock_partial_interaction, "snek", title="title", custom_id="idd", components=[component]
            )

            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "type": 9,
                    "data": {"title": "title", "custom_id": "idd", "components": [component.build.return_value]},
                },
                auth=None,
            )

    async def test_create_modal_response_when_both_component_and_components_passed(
        self, rest_client: rest.RESTClientImpl, mock_partial_interaction: interactions.PartialInteraction
    ):
        with pytest.raises(ValueError, match="Must specify exactly only one of 'component' or 'components'"):
            await rest_client.create_modal_response(
                mock_partial_interaction, "snek", title="title", custom_id="idd", component=mock.Mock(), components=[]
            )

    async def test_fetch_scheduled_event(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
    ):
        expected_route = routes.GET_GUILD_SCHEDULED_EVENT.compile(guild=123, scheduled_event=888)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "4949494949"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_event"
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.fetch_scheduled_event(mock_partial_guild, mock_scheduled_event)

            assert result is patched_deserialize_scheduled_event.return_value
            patched_deserialize_scheduled_event.assert_called_once_with({"id": "4949494949"})
            patched__request.assert_awaited_once_with(expected_route, query={"with_user_count": "true"})

    async def test_fetch_scheduled_events(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.GET_GUILD_SCHEDULED_EVENTS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=[{"id": "494920234", "type": "1"}]
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_event"
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.fetch_scheduled_events(mock_partial_guild)

            assert result == [patched_deserialize_scheduled_event.return_value]
            patched_deserialize_scheduled_event.assert_called_once_with({"id": "494920234", "type": "1"})
            patched__request.assert_awaited_once_with(expected_route, query={"with_user_count": "true"})

    async def test_fetch_scheduled_events_handles_unrecognised_events(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        mock_event = mock.Mock()
        expected_route = routes.GET_GUILD_SCHEDULED_EVENTS.compile(guild=123)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value=[{"id": "432234", "type": "1"}, {"id": "4939394", "type": "494949"}],
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory,
                "deserialize_scheduled_event",
                side_effect=[errors.UnrecognisedEntityError("evil laugh"), mock_event],
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.fetch_scheduled_events(mock_partial_guild)

            assert result == [mock_event]
            patched_deserialize_scheduled_event.assert_has_calls(
                [mock.call({"id": "432234", "type": "1"}), mock.call({"id": "4939394", "type": "494949"})]
            )
            patched__request.assert_awaited_once_with(expected_route, query={"with_user_count": "true"})

    async def test_create_stage_event(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=123)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "494949", "name": "MEOsdasdWWWWW"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_stage_event"
            ) as patched_deserialize_scheduled_stage_event,
        ):
            result = await rest_client.create_stage_event(
                mock_partial_guild,
                mock_guild_stage_channel,
                "boob man",
                datetime.datetime(2001, 1, 1, 17, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                description="o",
                end_time=datetime.datetime(2002, 2, 2, 17, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                image="tksksk.txt",
                privacy_level=654134,
                reason="bye bye",
            )

            assert result is patched_deserialize_scheduled_stage_event.return_value
            patched_deserialize_scheduled_stage_event.assert_called_once_with({"id": "494949", "name": "MEOsdasdWWWWW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "channel_id": "45613",
                    "name": "boob man",
                    "description": "o",
                    "entity_type": scheduled_events.ScheduledEventType.STAGE_INSTANCE,
                    "privacy_level": 654134,
                    "scheduled_start_time": "2001-01-01T17:42:41.891222+00:00",
                    "scheduled_end_time": "2002-02-02T17:42:41.891222+00:00",
                    "image": "some data",
                },
                reason="bye bye",
            )

    async def test_create_stage_event_without_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
    ):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "494949", "name": "MEOWWWWW"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_stage_event"
            ) as patched_deserialize_scheduled_stage_event,
        ):
            result = await rest_client.create_stage_event(
                mock_partial_guild,
                mock_guild_stage_channel,
                "boob man",
                datetime.datetime(2021, 3, 11, 17, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            )

            assert result is patched_deserialize_scheduled_stage_event.return_value
            patched_deserialize_scheduled_stage_event.assert_called_once_with({"id": "494949", "name": "MEOWWWWW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "channel_id": "45613",
                    "name": "boob man",
                    "entity_type": scheduled_events.ScheduledEventType.STAGE_INSTANCE,
                    "privacy_level": scheduled_events.EventPrivacyLevel.GUILD_ONLY,
                    "scheduled_start_time": "2021-03-11T17:42:41.891222+00:00",
                },
                reason=undefined.UNDEFINED,
            )

    async def test_create_voice_event(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=123)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "494942342439", "name": "MEOW"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_voice_event"
            ) as patched_deserialize_scheduled_voice_event,
        ):
            result = await rest_client.create_voice_event(
                mock_partial_guild,
                mock_guild_stage_channel,
                "boom man",
                datetime.datetime(2021, 3, 9, 13, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                description="hhhhh",
                end_time=datetime.datetime(2069, 3, 9, 13, 1, 41, 891222, tzinfo=datetime.timezone.utc),
                image="meow.txt",
                privacy_level=6523123,
                reason="it was the {insert political part here}",
            )

            assert result is patched_deserialize_scheduled_voice_event.return_value
            patched_deserialize_scheduled_voice_event.assert_called_once_with({"id": "494942342439", "name": "MEOW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "channel_id": "45613",
                    "name": "boom man",
                    "entity_type": scheduled_events.ScheduledEventType.VOICE,
                    "privacy_level": 6523123,
                    "scheduled_start_time": "2021-03-09T13:42:41.891222+00:00",
                    "scheduled_end_time": "2069-03-09T13:01:41.891222+00:00",
                    "description": "hhhhh",
                    "image": "some data",
                },
                reason="it was the {insert political part here}",
            )

    async def test_create_voice_event_without_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_stage_channel: channels.GuildStageChannel,
    ):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=123)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "123321123", "name": "MEOW"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_voice_event"
            ) as patched_deserialize_scheduled_voice_event,
        ):
            result = await rest_client.create_voice_event(
                mock_partial_guild,
                mock_guild_stage_channel,
                "boom man",
                datetime.datetime(2021, 3, 9, 13, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            )

            assert result is patched_deserialize_scheduled_voice_event.return_value
            patched_deserialize_scheduled_voice_event.assert_called_once_with({"id": "123321123", "name": "MEOW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "channel_id": "45613",
                    "name": "boom man",
                    "entity_type": scheduled_events.ScheduledEventType.VOICE,
                    "privacy_level": scheduled_events.EventPrivacyLevel.GUILD_ONLY,
                    "scheduled_start_time": "2021-03-09T13:42:41.891222+00:00",
                },
                reason=undefined.UNDEFINED,
            )

    async def test_create_external_event(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=123)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "494949", "name": "MerwwerEOW"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_external_event"
            ) as patched_deserialize_scheduled_external_event,
        ):
            result = await rest_client.create_external_event(
                mock_partial_guild,
                "hi",
                "Outside",
                datetime.datetime(2021, 3, 6, 2, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                datetime.datetime(2023, 5, 6, 16, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                description="This is a description",
                image="icon.png",
                privacy_level=6454,
                reason="chairman meow",
            )

            assert result is patched_deserialize_scheduled_external_event.return_value
            patched_deserialize_scheduled_external_event.assert_called_once_with({"id": "494949", "name": "MerwwerEOW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "name": "hi",
                    "entity_metadata": {"location": "Outside"},
                    "entity_type": scheduled_events.ScheduledEventType.EXTERNAL,
                    "privacy_level": 6454,
                    "scheduled_start_time": "2021-03-06T02:42:41.891222+00:00",
                    "scheduled_end_time": "2023-05-06T16:42:41.891222+00:00",
                    "description": "This is a description",
                    "image": "some data",
                },
                reason="chairman meow",
            )

    async def test_create_external_event_without_optionals(
        self, rest_client: rest.RESTClientImpl, mock_partial_guild: guilds.PartialGuild
    ):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=123)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "494923443249", "name": "MEOW"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_external_event"
            ) as patched_deserialize_scheduled_external_event,
        ):
            result = await rest_client.create_external_event(
                mock_partial_guild,
                "hi",
                "Outside",
                datetime.datetime(2021, 3, 6, 2, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                datetime.datetime(2023, 5, 6, 16, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            )

            assert result is patched_deserialize_scheduled_external_event.return_value
            patched_deserialize_scheduled_external_event.assert_called_once_with({"id": "494923443249", "name": "MEOW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "name": "hi",
                    "entity_metadata": {"location": "Outside"},
                    "entity_type": scheduled_events.ScheduledEventType.EXTERNAL,
                    "privacy_level": scheduled_events.EventPrivacyLevel.GUILD_ONLY,
                    "scheduled_start_time": "2021-03-06T02:42:41.891222+00:00",
                    "scheduled_end_time": "2023-05-06T16:42:41.891222+00:00",
                },
                reason=undefined.UNDEFINED,
            )

    async def test_edit_scheduled_event(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
        file_resource_patch: files.Resource[typing.Any],
    ):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=123, scheduled_event=888)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "494949", "name": "MEO43345W"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_event"
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.edit_scheduled_event(
                mock_partial_guild,
                mock_scheduled_event,
                channel=mock_guild_text_channel,
                description="hihihi",
                entity_type=scheduled_events.ScheduledEventType.VOICE,
                image="icon.png",
                location="Trans-land",
                name="Nihongo",
                privacy_level=69,
                start_time=datetime.datetime(2022, 3, 6, 12, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                end_time=datetime.datetime(2022, 5, 6, 12, 42, 41, 891222, tzinfo=datetime.timezone.utc),
                status=64,
                reason="go home",
            )

            assert result is patched_deserialize_scheduled_event.return_value
            patched_deserialize_scheduled_event.assert_called_once_with({"id": "494949", "name": "MEO43345W"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={
                    "channel_id": "4560",
                    "entity_metadata": {"location": "Trans-land"},
                    "name": "Nihongo",
                    "privacy_level": 69,
                    "scheduled_start_time": "2022-03-06T12:42:41.891222+00:00",
                    "scheduled_end_time": "2022-05-06T12:42:41.891222+00:00",
                    "description": "hihihi",
                    "entity_type": scheduled_events.ScheduledEventType.VOICE,
                    "status": 64,
                    "image": "some data",
                },
                reason="go home",
            )

    async def test_edit_scheduled_event_with_null_fields(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
    ):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=123, scheduled_event=888)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "494949", "name": "ME222222OW"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_event"
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.edit_scheduled_event(
                mock_partial_guild, mock_scheduled_event, channel=None, description=None, end_time=None
            )

            assert result is patched_deserialize_scheduled_event.return_value
            patched_deserialize_scheduled_event.assert_called_once_with({"id": "494949", "name": "ME222222OW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={"channel_id": None, "description": None, "scheduled_end_time": None},
                reason=undefined.UNDEFINED,
            )

    async def test_edit_scheduled_event_without_optionals(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
    ):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=123, scheduled_event=888)

        with (
            mock.patch.object(
                rest_client,
                "_request",
                new_callable=mock.AsyncMock,
                return_value={"id": "494123321949", "name": "MEOW"},
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_event"
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.edit_scheduled_event(mock_partial_guild, mock_scheduled_event)

            assert result is patched_deserialize_scheduled_event.return_value
            patched_deserialize_scheduled_event.assert_called_once_with({"id": "494123321949", "name": "MEOW"})
            patched__request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)

    async def test_edit_scheduled_event_when_changing_to_external(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_guild_text_channel: channels.GuildTextChannel,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
    ):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=123, scheduled_event=888)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "49342344949", "name": "MEOW"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_event"
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.edit_scheduled_event(
                mock_partial_guild,
                mock_scheduled_event,
                entity_type=scheduled_events.ScheduledEventType.EXTERNAL,
                channel=mock_guild_text_channel,
            )

            assert result is patched_deserialize_scheduled_event.return_value
            patched_deserialize_scheduled_event.assert_called_once_with({"id": "49342344949", "name": "MEOW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={"channel_id": "4560", "entity_type": scheduled_events.ScheduledEventType.EXTERNAL},
                reason=undefined.UNDEFINED,
            )

    async def test_edit_scheduled_event_when_changing_to_external_and_channel_id_not_explicitly_passed(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
    ):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=123, scheduled_event=888)

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value={"id": "494949", "name": "MEOW"}
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_scheduled_event"
            ) as patched_deserialize_scheduled_event,
        ):
            result = await rest_client.edit_scheduled_event(
                mock_partial_guild, mock_scheduled_event, entity_type=scheduled_events.ScheduledEventType.EXTERNAL
            )

            assert result is patched_deserialize_scheduled_event.return_value
            patched_deserialize_scheduled_event.assert_called_once_with({"id": "494949", "name": "MEOW"})
            patched__request.assert_awaited_once_with(
                expected_route,
                json={"channel_id": None, "entity_type": scheduled_events.ScheduledEventType.EXTERNAL},
                reason=undefined.UNDEFINED,
            )

    async def test_delete_scheduled_event(
        self,
        rest_client: rest.RESTClientImpl,
        mock_partial_guild: guilds.PartialGuild,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
    ):
        expected_route = routes.DELETE_GUILD_SCHEDULED_EVENT.compile(guild=123, scheduled_event=888)

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_scheduled_event"),
        ):
            await rest_client.delete_scheduled_event(mock_partial_guild, mock_scheduled_event)

            patched__request.assert_awaited_once_with(expected_route)

    async def test_fetch_stage_instance(
        self, rest_client: rest.RESTClientImpl, mock_guild_stage_channel: channels.GuildStageChannel
    ):
        expected_route = routes.GET_STAGE_INSTANCE.compile(channel=45613)
        mock_payload = {
            "id": "8406",
            "guild_id": "19703",
            "channel_id": "123",
            "topic": "ur mom",
            "privacy_level": 1,
            "discoverable_disabled": False,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=mock_payload
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_stage_instance"
            ) as patched_deserialize_stage_instance,
        ):
            result = await rest_client.fetch_stage_instance(channel=mock_guild_stage_channel)

            assert result is patched_deserialize_stage_instance.return_value
            patched__request.assert_called_once_with(expected_route)
            patched_deserialize_stage_instance.assert_called_once_with(mock_payload)

    async def test_create_stage_instance(
        self,
        rest_client: rest.RESTClientImpl,
        mock_guild_stage_channel: channels.GuildStageChannel,
        mock_scheduled_event: scheduled_events.ScheduledEvent,
    ):
        expected_route = routes.POST_STAGE_INSTANCE.compile()
        expected_json = {"channel_id": "45613", "topic": "ur mom", "guild_scheduled_event_id": "888"}
        mock_payload = {
            "id": "8406",
            "guild_id": "19703",
            "channel_id": "7334",
            "topic": "ur mom",
            "privacy_level": 2,
            "guild_scheduled_event_id": "3361203239",
            "discoverable_disabled": False,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=mock_payload
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_stage_instance"
            ) as patched_deserialize_stage_instance,
        ):
            result = await rest_client.create_stage_instance(
                channel=mock_guild_stage_channel, topic="ur mom", scheduled_event_id=mock_scheduled_event
            )

            assert result is patched_deserialize_stage_instance.return_value
            patched__request.assert_called_once_with(expected_route, json=expected_json)
            patched_deserialize_stage_instance.assert_called_once_with(mock_payload)

    async def test_edit_stage_instance(
        self, rest_client: rest.RESTClientImpl, mock_guild_stage_channel: channels.GuildStageChannel
    ):
        expected_route = routes.PATCH_STAGE_INSTANCE.compile(channel=45613)
        expected_json = {"topic": "ur mom", "privacy_level": 2}
        mock_payload = {
            "id": "8406",
            "guild_id": "19703",
            "channel_id": "7334",
            "topic": "ur mom",
            "privacy_level": 2,
            "discoverable_disabled": False,
        }

        with (
            mock.patch.object(
                rest_client, "_request", new_callable=mock.AsyncMock, return_value=mock_payload
            ) as patched__request,
            mock.patch.object(
                rest_client.entity_factory, "deserialize_stage_instance"
            ) as patched_deserialize_stage_instance,
        ):
            result = await rest_client.edit_stage_instance(
                channel=mock_guild_stage_channel,
                topic="ur mom",
                privacy_level=stage_instances.StageInstancePrivacyLevel.GUILD_ONLY,
            )

            assert result is patched_deserialize_stage_instance.return_value
            patched__request.assert_called_once_with(expected_route, json=expected_json)
            patched_deserialize_stage_instance.assert_called_once_with(mock_payload)

    async def test_delete_stage_instance(
        self, rest_client: rest.RESTClientImpl, mock_guild_stage_channel: channels.GuildStageChannel
    ):
        expected_route = routes.DELETE_STAGE_INSTANCE.compile(channel=45613)

        with (
            mock.patch.object(rest_client, "_request", new_callable=mock.AsyncMock) as patched__request,
            mock.patch.object(rest_client.entity_factory, "deserialize_stage_instance"),
        ):
            await rest_client.delete_stage_instance(channel=mock_guild_stage_channel)

        patched__request.assert_called_once_with(expected_route)

    async def test_fetch_poll_voters(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.GET_POLL_ANSWER.compile(
            channel=StubModel(45874392), message=StubModel(398475938475), answer=StubModel(4)
        )

        rest_client._request = mock.AsyncMock(return_value=[{"id": "1234"}])

        with mock.patch.object(
            rest_client._entity_factory, "deserialize_user", return_value=mock.Mock()
        ) as patched_deserialize_user:
            await rest_client.fetch_poll_voters(
                StubModel(45874392), StubModel(398475938475), StubModel(4), after=StubModel(43587935), limit=6
            )

            patched_deserialize_user.assert_called_once_with({"id": "1234"})

        rest_client._request.assert_awaited_once_with(expected_route, query={"after": "43587935", "limit": "6"})

    async def test_end_poll(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_EXPIRE_POLL.compile(
            channel=StubModel(45874392), message=StubModel(398475938475), answer=StubModel(4)
        )

        message_obj = mock.Mock()

        rest_client._request = mock.AsyncMock(return_value={"id": "398475938475"})

        rest_client._entity_factory.deserialize_message = mock.Mock(return_value=message_obj)

        response = await rest_client.end_poll(StubModel(45874392), StubModel(398475938475))

        rest_client._request.assert_awaited_once_with(expected_route)

        assert response is message_obj
