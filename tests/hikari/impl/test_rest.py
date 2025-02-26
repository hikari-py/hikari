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
from hikari import invites
from hikari import iterators
from hikari import locales
from hikari import messages as message_models
from hikari import permissions
from hikari import scheduled_events
from hikari import snowflakes
from hikari import stage_instances
from hikari import undefined
from hikari import urls
from hikari import users
from hikari import webhooks
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
    def rest_client(self):
        class StubRestClient:
            http_settings = object()
            proxy_settings = object()

        return StubRestClient()

    @pytest.fixture
    def executor(self):
        return mock.Mock()

    @pytest.fixture
    def entity_factory(self):
        return mock.Mock()

    @pytest.fixture
    def rest_provider(self, rest_client, executor, entity_factory):
        return rest._RESTProvider(lambda: entity_factory, executor, lambda: rest_client)

    def test_rest_property(self, rest_provider, rest_client):
        assert rest_provider.rest == rest_client

    def test_http_settings_property(self, rest_provider, rest_client):
        assert rest_provider.http_settings == rest_client.http_settings

    def test_proxy_settings_property(self, rest_provider, rest_client):
        assert rest_provider.proxy_settings == rest_client.proxy_settings

    def test_entity_factory_property(self, rest_provider, entity_factory):
        assert rest_provider.entity_factory == entity_factory

    def test_executor_property(self, rest_provider, executor):
        assert rest_provider.executor == executor


#############################
# ClientCredentialsStrategy #
#############################


class TestClientCredentialsStrategy:
    @pytest.fixture
    def mock_token(self):
        return mock.Mock(
            applications.PartialOAuth2Token,
            expires_in=datetime.timedelta(weeks=1),
            token_type=applications.TokenType.BEARER,
            access_token="okokok.fofofo.ddd",
        )

    def test_client_id_property(self):
        mock_client = hikari_test_helpers.mock_class_namespace(applications.Application, id=43123, init_=False)()
        token = rest.ClientCredentialsStrategy(client=mock_client, client_secret="123123123")

        assert token.client_id == 43123

    def test_scopes_property(self):
        token = rest.ClientCredentialsStrategy(client=123, client_secret="123123123", scopes=[123, 5643])

        assert token.scopes == (123, 5643)

    def test_token_type_property(self):
        token = rest.ClientCredentialsStrategy(client=123, client_secret="123123123", scopes=[])

        assert token.token_type is applications.TokenType.BEARER

    @pytest.mark.asyncio
    async def test_acquire_on_new_instance(self, mock_token):
        mock_rest = mock.Mock(authorize_client_credentials_token=mock.AsyncMock(return_value=mock_token))

        result = await rest.ClientCredentialsStrategy(client=54123123, client_secret="123123123").acquire(mock_rest)

        assert result == "Bearer okokok.fofofo.ddd"

        mock_rest.authorize_client_credentials_token.assert_awaited_once_with(
            client=54123123, client_secret="123123123", scopes=("applications.commands.update", "identify")
        )

    @pytest.mark.asyncio
    async def test_acquire_handles_out_of_date_token(self, mock_token):
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
    async def test_acquire_handles_token_being_set_before_lock_is_acquired(self, mock_token):
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
    async def test_acquire_after_invalidation(self, mock_token):
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
            def __init__(self, strategy):
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
    def rest_app(self):
        return hikari_test_helpers.mock_class_namespace(rest.RESTApp, slots_=False)(
            executor=None,
            http_settings=mock.Mock(spec_set=config.HTTPSettings),
            max_rate_limit=float("inf"),
            max_retries=0,
            proxy_settings=mock.Mock(spec_set=config.ProxySettings),
            url="https://some.url",
        )

    def test_executor_property(self, rest_app):
        mock_executor = object()
        rest_app._executor = mock_executor
        assert rest_app.executor is mock_executor

    def test_http_settings_property(self, rest_app):
        mock_http_settings = object()
        rest_app._http_settings = mock_http_settings
        assert rest_app.http_settings is mock_http_settings

    def test_proxy_settings(self, rest_app):
        mock_proxy_settings = object()
        rest_app._proxy_settings = mock_proxy_settings
        assert rest_app.proxy_settings is mock_proxy_settings

    def test_acquire(self, rest_app):
        rest_app._client_session = object()
        rest_app._bucket_manager = object()
        stack = contextlib.ExitStack()
        mock_entity_factory = stack.enter_context(mock.patch.object(entity_factory, "EntityFactoryImpl"))
        mock_client = stack.enter_context(mock.patch.object(rest, "RESTClientImpl"))

        with stack:
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

    def test_acquire_defaults_to_bearer_for_a_string_token(self, rest_app):
        rest_app._client_session = object()
        rest_app._bucket_manager = object()
        stack = contextlib.ExitStack()
        mock_entity_factory = stack.enter_context(mock.patch.object(entity_factory, "EntityFactoryImpl"))
        mock_client = stack.enter_context(mock.patch.object(rest, "RESTClientImpl"))

        with stack:
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
def rest_client_class():
    return hikari_test_helpers.mock_class_namespace(rest.RESTClientImpl, slots_=False)


@pytest.fixture
def mock_cache():
    return mock.Mock()


@pytest.fixture
def rest_client(rest_client_class, mock_cache):
    obj = rest_client_class(
        cache=mock_cache,
        http_settings=mock.Mock(spec=config.HTTPSettings),
        max_rate_limit=float("inf"),
        proxy_settings=mock.Mock(spec=config.ProxySettings),
        token="some_token",
        token_type="tYpe",
        max_retries=0,
        rest_url="https://some.where/api/v3",
        executor=object(),
        entity_factory=mock.Mock(),
        bucket_manager=mock.Mock(
            acquire_bucket=mock.Mock(return_value=hikari_test_helpers.AsyncContextManagerMock()),
            acquire_authentication=mock.AsyncMock(),
        ),
        client_session=mock.Mock(request=mock.AsyncMock()),
    )
    obj._close_event = object()
    return obj


@pytest.fixture
def file_resource():
    class Stream:
        def __init__(self, data):
            self.open = False
            self.data = data

        async def data_uri(self):
            if not self.open:
                raise RuntimeError("Tried to read off a closed stream")

            return self.data

        async def __aenter__(self):
            self.open = True
            return self

        async def __aexit__(self, exc_type, exc, exc_tb) -> None:
            self.open = False

    class FileResource(files.Resource):
        filename = None
        url = None

        def __init__(self, stream_data):
            self._stream = Stream(data=stream_data)

        def stream(self, executor):
            return self._stream

    return FileResource


@pytest.fixture
def file_resource_patch(file_resource):
    resource = file_resource("some data")
    with mock.patch.object(files, "ensure_resource", return_value=resource):
        yield resource


class StubModel(snowflakes.Unique):
    id = None

    def __init__(self, id=0):
        self.id = snowflakes.Snowflake(id)


class TestStringifyHttpMessage:
    def test_when_body_is_None(self, rest_client):
        headers = {"HEADER1": "value1", "HEADER2": "value2", "Authorization": "this will never see the light of day"}
        expected_return = "    HEADER1: value1\n    HEADER2: value2\n    Authorization: **REDACTED TOKEN**"
        assert rest._stringify_http_message(headers, None) == expected_return

    @pytest.mark.parametrize(("body", "expected"), [(bytes("hello :)", "ascii"), "hello :)"), (123, "123")])
    def test_when_body_is_not_None(self, rest_client, body, expected):
        headers = {"HEADER1": "value1", "HEADER2": "value2", "Authorization": "this will never see the light of day"}
        expected_return = (
            f"    HEADER1: value1\n    HEADER2: value2\n    Authorization: **REDACTED TOKEN**\n\n    {expected}"
        )
        assert rest._stringify_http_message(headers, body) == expected_return


class TestTransformEmojiToUrlFormat:
    @pytest.mark.parametrize(
        ("emoji", "expected_return"),
        [
            (emojis.CustomEmoji(id=123, name="rooYay", is_animated=False), "rooYay:123"),
            ("\N{OK HAND SIGN}", "\N{OK HAND SIGN}"),
            (emojis.UnicodeEmoji("\N{OK HAND SIGN}"), "\N{OK HAND SIGN}"),
        ],
    )
    def test_expected(self, rest_client, emoji, expected_return):
        assert rest._transform_emoji_to_url_format(emoji, undefined.UNDEFINED) == expected_return

    def test_with_id(self, rest_client):
        assert rest._transform_emoji_to_url_format("rooYay", 123) == "rooYay:123"

    @pytest.mark.parametrize(
        "emoji", [emojis.CustomEmoji(id=123, name="rooYay", is_animated=False), emojis.UnicodeEmoji("\N{OK HAND SIGN}")]
    )
    def test_when_id_passed_with_emoji_object(self, rest_client, emoji):
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
                entity_factory=None,
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
                entity_factory=None,
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
            entity_factory=None,
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
            entity_factory=None,
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
            entity_factory=None,
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
                entity_factory=None,
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
            entity_factory=None,
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
            entity_factory=None,
        )
        assert obj._rest_url == "https://some.where/api/v2"

    def test___enter__(self, rest_client):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            rest_client.__enter__()

    def test___exit__(self, rest_client):
        try:
            rest_client.__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)

    @pytest.mark.parametrize(("attributes", "expected_result"), [(None, False), (object(), True)])
    def test_is_alive_property(self, rest_client, attributes, expected_result):
        rest_client._close_event = attributes

        assert rest_client.is_alive is expected_result

    def test_entity_factory_property(self, rest_client):
        assert rest_client.entity_factory is rest_client._entity_factory

    def test_http_settings_property(self, rest_client):
        mock_http_settings = object()
        rest_client._http_settings = mock_http_settings
        assert rest_client.http_settings is mock_http_settings

    def test_proxy_settings_property(self, rest_client):
        mock_proxy_settings = object()
        rest_client._proxy_settings = mock_proxy_settings
        assert rest_client.proxy_settings is mock_proxy_settings

    def test_token_type_property(self, rest_client):
        mock_type = object()
        rest_client._token_type = mock_type
        assert rest_client.token_type is mock_type

    @pytest.mark.parametrize("client_session_owner", [True, False])
    @pytest.mark.parametrize("bucket_manager_owner", [True, False])
    @pytest.mark.asyncio
    async def test_close(self, rest_client, client_session_owner, bucket_manager_owner):
        rest_client._close_event = mock_close_event = mock.Mock()
        rest_client._client_session.close = client_close = mock.AsyncMock()
        rest_client._bucket_manager.close = bucket_close = mock.AsyncMock()
        rest_client._client_session_owner = client_session_owner
        rest_client._bucket_manager_owner = bucket_manager_owner

        await rest_client.close()

        mock_close_event.set.assert_called_once_with()
        assert rest_client._close_event is None

        if client_session_owner:
            client_close.assert_awaited_once_with()
            assert rest_client._client_session is None
        else:
            client_close.assert_not_called()
            assert rest_client._client_session is not None

        if bucket_manager_owner:
            bucket_close.assert_awaited_once_with()
        else:
            rest_client._bucket_manager.assert_not_called()

    @pytest.mark.parametrize("client_session_owner", [True, False])
    @pytest.mark.parametrize("bucket_manager_owner", [True, False])
    @pytest.mark.asyncio  # Function needs to be executed in a running loop
    async def test_start(self, rest_client, client_session_owner, bucket_manager_owner):
        rest_client._client_session = None
        rest_client._close_event = None
        rest_client._bucket_manager = mock.Mock()
        rest_client._client_session_owner = client_session_owner
        rest_client._bucket_manager_owner = bucket_manager_owner

        with mock.patch.object(net, "create_client_session") as create_client_session:
            with mock.patch.object(net, "create_tcp_connector") as create_tcp_connector:
                with mock.patch.object(asyncio, "Event") as event:
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

    def test_start_when_active(self, rest_client):
        rest_client._close_event = object()

        with pytest.raises(errors.ComponentStateConflictError):
            rest_client.start()

    #######################
    # Non-async endpoints #
    #######################

    def test_trigger_typing(self, rest_client):
        channel = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "TypingIndicator", return_value=stub_iterator) as typing_indicator:
            assert rest_client.trigger_typing(channel) == stub_iterator

            typing_indicator.assert_called_once_with(
                request_call=rest_client._request, channel=channel, rest_close_event=rest_client._close_event
            )

    @pytest.mark.parametrize(
        "before",
        [
            datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc),
            StubModel(735757641938108416),
        ],
    )
    def test_fetch_messages_with_before(self, rest_client, before):
        channel = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(channel, before=before) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=channel,
                direction="before",
                first_id="735757641938108416",
            )

    @pytest.mark.parametrize(
        "after",
        [
            datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc),
            StubModel(735757641938108416),
        ],
    )
    def test_fetch_messages_with_after(self, rest_client, after):
        channel = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(channel, after=after) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=channel,
                direction="after",
                first_id="735757641938108416",
            )

    @pytest.mark.parametrize(
        "around",
        [
            datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc),
            StubModel(735757641938108416),
        ],
    )
    def test_fetch_messages_with_around(self, rest_client, around):
        channel = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(channel, around=around) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=channel,
                direction="around",
                first_id="735757641938108416",
            )

    def test_fetch_messages_with_default(self, rest_client):
        channel = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MessageIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_messages(channel) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=channel,
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
    def test_fetch_messages_when_more_than_one_kwarg_passed(self, rest_client, kwargs):
        with pytest.raises(TypeError):
            rest_client.fetch_messages(StubModel(123), **kwargs)

    def test_fetch_reactions_for_emoji(self, rest_client):
        channel = StubModel(123)
        message = StubModel(456)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "ReactorIterator", return_value=stub_iterator) as iterator:
            with mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"):
                assert rest_client.fetch_reactions_for_emoji(channel, message, "<:rooYay:123>") == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                channel=channel,
                message=message,
                emoji="rooYay:123",
            )

    def test_fetch_my_guilds_when_start_at_is_undefined(self, rest_client):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "OwnGuildIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_my_guilds() == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                newest_first=False,
                first_id="0",
            )

    def test_fetch_my_guilds_when_start_at_is_datetime(self, rest_client):
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

    def test_fetch_my_guilds_when_start_at_is_else(self, rest_client):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "OwnGuildIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_my_guilds(newest_first=True, start_at=StubModel(123)) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                newest_first=True,
                first_id="123",
            )

    def test_guild_builder(self, rest_client):
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "GuildBuilder", return_value=stub_iterator) as iterator:
            assert rest_client.guild_builder("hikari") == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                executor=rest_client._executor,
                request_call=rest_client._request,
                name="hikari",
            )

    def test_fetch_audit_log_when_before_is_undefined(self, rest_client):
        guild = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "AuditLogIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_audit_log(guild) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                guild=guild,
                before=undefined.UNDEFINED,
                user=undefined.UNDEFINED,
                action_type=undefined.UNDEFINED,
            )

    def test_fetch_audit_log_when_before_datetime(self, rest_client):
        guild = StubModel(123)
        user = StubModel(456)
        stub_iterator = mock.Mock()
        datetime_obj = datetime.datetime(2020, 7, 23, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc)

        with mock.patch.object(special_endpoints, "AuditLogIterator", return_value=stub_iterator) as iterator:
            returned = rest_client.fetch_audit_log(
                guild, user=user, before=datetime_obj, event_type=audit_logs.AuditLogEventType.GUILD_UPDATE
            )
            assert returned is stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                guild=guild,
                before="735757641938108416",
                user=user,
                action_type=audit_logs.AuditLogEventType.GUILD_UPDATE,
            )

    def test_fetch_audit_log_when_before_is_else(self, rest_client):
        guild = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "AuditLogIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_audit_log(guild, before=StubModel(456)) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                guild=guild,
                before="456",
                user=undefined.UNDEFINED,
                action_type=undefined.UNDEFINED,
            )

    def test_fetch_public_archived_threads(self, rest_client: rest.RESTClientImpl):
        mock_datetime = time.utc_datetime()
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_public_archived_threads(StubModel(54123123), before=mock_datetime)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client._deserialize_public_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PUBLIC_ARCHIVED_THREADS.compile(channel=54123123),
            before=mock_datetime.isoformat(),
            before_is_timestamp=True,
        )

    def test_fetch_public_archived_threads_when_before_not_specified(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_public_archived_threads(StubModel(432234))

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client._deserialize_public_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PUBLIC_ARCHIVED_THREADS.compile(channel=432234),
            before=undefined.UNDEFINED,
            before_is_timestamp=True,
        )

    def test_fetch_private_archived_threads(self, rest_client: rest.RESTClientImpl):
        mock_datetime = time.utc_datetime()
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_private_archived_threads(StubModel(432234432), before=mock_datetime)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PRIVATE_ARCHIVED_THREADS.compile(channel=432234432),
            before=mock_datetime.isoformat(),
            before_is_timestamp=True,
        )

    def test_fetch_private_archived_threads_when_before_not_specified(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_private_archived_threads(StubModel(543345543))

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_PRIVATE_ARCHIVED_THREADS.compile(channel=543345543),
            before=undefined.UNDEFINED,
            before_is_timestamp=True,
        )

    @pytest.mark.parametrize(
        "before", [datetime.datetime(2022, 2, 28, 10, 58, 30, 987193, tzinfo=datetime.timezone.utc), 947809989634818048]
    )
    def test_fetch_joined_private_archived_threads(
        self, rest_client: rest.RESTClientImpl, before: typing.Union[datetime.datetime, snowflakes.Snowflake]
    ):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_joined_private_archived_threads(StubModel(543123), before=before)

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_JOINED_PRIVATE_ARCHIVED_THREADS.compile(channel=543123),
            before="947809989634818048",
            before_is_timestamp=False,
        )

    def test_fetch_joined_private_archived_threads_when_before_not_specified(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildThreadIterator") as iterator:
            result = rest_client.fetch_joined_private_archived_threads(StubModel(323232))

        assert result is iterator.return_value
        iterator.assert_called_once_with(
            deserialize=rest_client.entity_factory.deserialize_guild_private_thread,
            entity_factory=rest_client.entity_factory,
            request_call=rest_client._request,
            route=routes.GET_JOINED_PRIVATE_ARCHIVED_THREADS.compile(channel=323232),
            before=undefined.UNDEFINED,
            before_is_timestamp=False,
        )

    def test_fetch_members(self, rest_client):
        guild = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MemberIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_members(guild) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory, request_call=rest_client._request, guild=guild
            )

    def test_kick_member(self, rest_client):
        mock_kick_user = mock.Mock()
        rest_client.kick_user = mock_kick_user

        result = rest_client.kick_member(123, 5423, reason="oewkwkwk")

        assert result is mock_kick_user.return_value
        mock_kick_user.assert_called_once_with(123, 5423, reason="oewkwkwk")

    def test_ban_member(self, rest_client):
        mock_ban_user = mock.Mock()
        rest_client.ban_user = mock_ban_user

        result = rest_client.ban_member(43123, 54123, delete_message_seconds=518400, reason="wowowowo")

        assert result is mock_ban_user.return_value
        mock_ban_user.assert_called_once_with(43123, 54123, delete_message_seconds=518400, reason="wowowowo")

    def test_unban_member(self, rest_client):
        mock_unban_user = mock.Mock()
        rest_client.unban_user = mock_unban_user

        reason = rest_client.unban_member(123, 321, reason="ayaya")

        assert reason is mock_unban_user.return_value
        mock_unban_user.assert_called_once_with(123, 321, reason="ayaya")

    def test_fetch_bans(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(187, newest_first=True, start_at=StubModel(65652342134))

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, 187, True, "65652342134"
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_bans_when_datetime_for_start_at(self, rest_client: rest.RESTClientImpl):
        start_at = datetime.datetime(2022, 3, 6, 12, 1, 58, 415625, tzinfo=datetime.timezone.utc)
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(9000, newest_first=True, start_at=start_at)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, 9000, True, "950000286338908160"
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_bans_when_start_at_undefined(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(8844)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, 8844, False, str(snowflakes.Snowflake.min())
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_bans_when_start_at_undefined_and_newest_first(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "GuildBanIterator") as iterator_cls:
            iterator = rest_client.fetch_bans(3848, newest_first=True)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, 3848, True, str(snowflakes.Snowflake.max())
        )
        assert iterator is iterator_cls.return_value

    def test_slash_command_builder(self, rest_client):
        result = rest_client.slash_command_builder("a name", "a description")
        assert isinstance(result, special_endpoints.SlashCommandBuilder)

    def test_context_menu_command_command_builder(self, rest_client):
        result = rest_client.context_menu_command_builder(3, "a name")
        assert isinstance(result, special_endpoints.ContextMenuCommandBuilder)
        assert result.type == commands.CommandType.MESSAGE

    def test_build_message_action_row(self, rest_client):
        with mock.patch.object(special_endpoints, "MessageActionRowBuilder") as action_row_builder:
            assert rest_client.build_message_action_row() is action_row_builder.return_value

        action_row_builder.assert_called_once_with()

    def test_build_modal_action_row(self, rest_client):
        with mock.patch.object(special_endpoints, "ModalActionRowBuilder") as action_row_builder:
            assert rest_client.build_modal_action_row() is action_row_builder.return_value

        action_row_builder.assert_called_once_with()

    def test__build_message_payload_with_undefined_args(self, rest_client):
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
    def test__build_message_payload_with_None_args(self, rest_client, args):
        kwargs = {}
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

    def test__build_message_payload_with_edit_and_all_mentions_undefined(self, rest_client):
        with mock.patch.object(mentions, "generate_allowed_mentions") as generate_allowed_mentions:
            body, form = rest_client._build_message_payload(edit=True)

        assert body == {}
        assert form is None

        generate_allowed_mentions.assert_not_called()

    def test__build_message_payload_embed_content_syntactic_sugar(self, rest_client):
        embed = mock.Mock(embeds.Embed)

        stack = contextlib.ExitStack()
        generate_allowed_mentions = stack.enter_context(
            mock.patch.object(mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1})
        )
        rest_client._entity_factory.serialize_embed.return_value = ({"embed": 1}, [])

        with stack:
            body, form = rest_client._build_message_payload(content=embed)

        # Returned
        assert body == {"embeds": [{"embed": 1}], "allowed_mentions": {"allowed_mentions": 1}}
        assert form is None

        # Embeds
        rest_client._entity_factory.serialize_embed.assert_called_once_with(embed)

        # Generate allowed mentions
        generate_allowed_mentions.assert_called_once_with(
            undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED
        )

    def test__build_message_payload_attachment_content_syntactic_sugar(self, rest_client):
        attachment = mock.Mock(files.Resource)
        resource_attachment = mock.Mock(filename="attachment.png")

        stack = contextlib.ExitStack()
        ensure_resource = stack.enter_context(
            mock.patch.object(files, "ensure_resource", return_value=resource_attachment)
        )
        generate_allowed_mentions = stack.enter_context(
            mock.patch.object(mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1})
        )
        url_encoded_form = stack.enter_context(mock.patch.object(data_binding, "URLEncodedFormBuilder"))

        with stack:
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

    def test__build_message_payload_with_singular_args(self, rest_client):
        attachment = object()
        resource_attachment1 = mock.Mock(filename="attachment.png")
        resource_attachment2 = mock.Mock(filename="attachment2.png")
        component = mock.Mock(build=mock.Mock(return_value={"component": 1}))
        embed = object()
        embed_attachment = object()
        mentions_everyone = object()
        mentions_reply = object()
        user_mentions = object()
        role_mentions = object()

        stack = contextlib.ExitStack()
        ensure_resource = stack.enter_context(
            mock.patch.object(files, "ensure_resource", side_effect=[resource_attachment1, resource_attachment2])
        )
        generate_allowed_mentions = stack.enter_context(
            mock.patch.object(mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1})
        )
        url_encoded_form = stack.enter_context(mock.patch.object(data_binding, "URLEncodedFormBuilder"))
        rest_client._entity_factory.serialize_embed.return_value = ({"embed": 1}, [embed_attachment])

        with stack:
            body, form = rest_client._build_message_payload(
                content=987654321,
                attachment=attachment,
                component=component,
                embed=embed,
                sticker=StubModel(5412123),
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
            "sticker_ids": ["5412123"],
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
        rest_client._entity_factory.serialize_embed.assert_called_once_with(embed)

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

    def test__build_message_payload_with_plural_args(self, rest_client):
        attachment1 = object()
        attachment2 = mock.Mock(message_models.Attachment, id=123, filename="attachment123.png")
        resource_attachment1 = mock.Mock(filename="attachment.png")
        resource_attachment2 = mock.Mock(filename="attachment2.png")
        resource_attachment3 = mock.Mock(filename="attachment3.png")
        resource_attachment4 = mock.Mock(filename="attachment4.png")
        resource_attachment5 = mock.Mock(filename="attachment5.png")
        resource_attachment6 = mock.Mock(filename="attachment6.png")
        component1 = mock.Mock(build=mock.Mock(return_value={"component": 1}))
        component2 = mock.Mock(build=mock.Mock(return_value={"component": 2}))
        embed1 = object()
        embed2 = object()
        embed_attachment1 = object()
        embed_attachment2 = object()
        embed_attachment3 = object()
        embed_attachment4 = object()
        mentions_everyone = object()
        mentions_reply = object()
        user_mentions = object()
        role_mentions = object()

        stack = contextlib.ExitStack()
        ensure_resource = stack.enter_context(
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
            )
        )
        generate_allowed_mentions = stack.enter_context(
            mock.patch.object(mentions, "generate_allowed_mentions", return_value={"allowed_mentions": 1})
        )
        url_encoded_form = stack.enter_context(mock.patch.object(data_binding, "URLEncodedFormBuilder"))
        rest_client._entity_factory.serialize_embed.side_effect = [
            ({"embed": 1}, [embed_attachment1, embed_attachment2]),
            ({"embed": 2}, [embed_attachment3, embed_attachment4]),
        ]

        with stack:
            body, form = rest_client._build_message_payload(
                content=987654321,
                attachments=[attachment1, attachment2],
                components=[component1, component2],
                embeds=[embed1, embed2],
                stickers=[54612123, StubModel(123321)],
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
            "sticker_ids": ["54612123", "123321"],
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
        assert rest_client._entity_factory.serialize_embed.call_count == 2
        rest_client._entity_factory.serialize_embed.assert_has_calls([mock.call(embed1), mock.call(embed2)])

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

    def test__build_message_payload_with_edit_and_attachment_object_passed(self, rest_client):
        attachment1 = object()
        attachment2 = mock.Mock(message_models.Attachment, id=123, filename="attachment123.png")
        resource_attachment1 = mock.Mock(filename="attachment.png")
        resource_attachment2 = mock.Mock(filename="attachment2.png")
        resource_attachment3 = mock.Mock(filename="attachment3.png")
        resource_attachment4 = mock.Mock(filename="attachment4.png")
        resource_attachment5 = mock.Mock(filename="attachment5.png")
        component1 = mock.Mock(build=mock.Mock(return_value={"component": 1}))
        component2 = mock.Mock(build=mock.Mock(return_value={"component": 2}))
        embed1 = object()
        embed2 = object()
        embed_attachment1 = object()
        embed_attachment2 = object()
        embed_attachment3 = object()
        embed_attachment4 = object()

        stack = contextlib.ExitStack()
        ensure_resource = stack.enter_context(
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
            )
        )
        url_encoded_form = stack.enter_context(mock.patch.object(data_binding, "URLEncodedFormBuilder"))
        rest_client._entity_factory.serialize_embed.side_effect = [
            ({"embed": 1}, [embed_attachment1, embed_attachment2]),
            ({"embed": 2}, [embed_attachment3, embed_attachment4]),
        ]

        with stack:
            body, form = rest_client._build_message_payload(
                content=987654321,
                attachments=[attachment1, attachment2],
                components=[component1, component2],
                embeds=[embed1, embed2],
                flags=120,
                tts=True,
                mentions_everyone=None,
                mentions_reply=None,
                user_mentions=None,
                role_mentions=None,
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
            "allowed_mentions": {"parse": []},
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
        self, rest_client, singular_arg, plural_arg
    ):
        with pytest.raises(
            ValueError, match=rf"You may only specify one of '{singular_arg}' or '{plural_arg}', not both"
        ):
            rest_client._build_message_payload(**{singular_arg: object(), plural_arg: object()})

    def test_interaction_deferred_builder(self, rest_client):
        result = rest_client.interaction_deferred_builder(5)

        assert result.type == 5
        assert isinstance(result, special_endpoints.InteractionDeferredBuilder)

    def test_interaction_autocomplete_builder(self, rest_client):
        result = rest_client.interaction_autocomplete_builder(
            [special_endpoints.AutocompleteChoiceBuilder(name="name", value="value")]
        )

        assert result.choices == [special_endpoints.AutocompleteChoiceBuilder(name="name", value="value")]

    def test_interaction_message_builder(self, rest_client):
        result = rest_client.interaction_message_builder(4)

        assert result.type == 4
        assert isinstance(result, special_endpoints.InteractionMessageBuilder)

    def test_interaction_modal_builder(self, rest_client):
        result = rest_client.interaction_modal_builder("aaaaa", "custom")

        assert result.type == 9
        assert result.title == "aaaaa"
        assert result.custom_id == "custom"

    def test_fetch_scheduled_event_users(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(
                33432234, 6666655555, newest_first=True, start_at=StubModel(65652342134)
            )

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, True, "65652342134", 33432234, 6666655555
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_scheduled_event_users_when_datetime_for_start_at(self, rest_client: rest.RESTClientImpl):
        start_at = datetime.datetime(2022, 3, 6, 12, 1, 58, 415625, tzinfo=datetime.timezone.utc)
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(54123, 656324, newest_first=True, start_at=start_at)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, True, "950000286338908160", 54123, 656324
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_scheduled_event_users_when_start_at_undefined(self, rest_client: rest.RESTClientImpl):
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(54563245, 123321123)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory,
            rest_client._request,
            False,
            str(snowflakes.Snowflake.min()),
            54563245,
            123321123,
        )
        assert iterator is iterator_cls.return_value

    def test_fetch_scheduled_event_users_when_start_at_undefined_and_newest_first(
        self, rest_client: rest.RESTClientImpl
    ):
        with mock.patch.object(special_endpoints, "ScheduledEventUserIterator") as iterator_cls:
            iterator = rest_client.fetch_scheduled_event_users(6423, 65456234, newest_first=True)

        iterator_cls.assert_called_once_with(
            rest_client._entity_factory, rest_client._request, True, str(snowflakes.Snowflake.max()), 6423, 65456234
        )
        assert iterator is iterator_cls.return_value


@pytest.mark.asyncio
class TestRESTClientImplAsync:
    @pytest.fixture
    def exit_exception(self):
        class ExitException(Exception): ...

        return ExitException

    async def test___aenter__and__aexit__(self, rest_client):
        rest_client.close = mock.AsyncMock()
        rest_client.start = mock.Mock()

        async with rest_client as client:
            assert client is rest_client
            rest_client.start.assert_called_once()
            rest_client.close.assert_not_called()

        rest_client.close.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test_perform_request_errors_if_both_json_and_form_builder_passed(self, rest_client):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        with pytest.raises(ValueError, match="Can only provide one of 'json' or 'form_builder', not both"):
            await rest_client._perform_request(route, json=object(), form_builder=object())

    @hikari_test_helpers.timeout()
    async def test_perform_request_builds_json_when_passed(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception
        rest_client._token = None

        with mock.patch.object(data_binding, "JSONPayload") as json_payload:
            with pytest.raises(exit_exception):
                await rest_client._perform_request(route, json={"some": "data"})

        json_payload.assert_called_once_with({"some": "data"}, dumps=rest_client._dumps)
        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert kwargs["data"] is json_payload.return_value

    @hikari_test_helpers.timeout()
    async def test_perform_request_builds_form_when_passed(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception
        rest_client._token = None
        mock_form = mock.AsyncMock()
        mock_stack = mock.AsyncMock()
        mock_stack.__aenter__ = mock_stack

        with mock.patch.object(contextlib, "AsyncExitStack", return_value=mock_stack) as exit_stack:
            with pytest.raises(exit_exception):
                await rest_client._perform_request(route, form_builder=mock_form)

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        mock_form.build.assert_awaited_once_with(exit_stack.return_value, executor=rest_client._executor)
        assert kwargs["data"] is mock_form.build.return_value

    @hikari_test_helpers.timeout()
    async def test_perform_request_url_encodes_reason_header(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception

        with pytest.raises(exit_exception):
            await rest_client._perform_request(route, reason="光のenergyが　大地に降りそそぐ")

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert kwargs["headers"][rest._X_AUDIT_LOG_REASON_HEADER] == (
            "%E5%85%89%E3%81%AEenergy%E3%81%8C%E3%80%80%E5%A4%"
            "A7%E5%9C%B0%E3%81%AB%E9%99%8D%E3%82%8A%E3%81%9D%E3%81%9D%E3%81%90"
        )

    @hikari_test_helpers.timeout()
    async def test_perform_request_with_strategy_token(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception
        rest_client._token = mock.Mock(rest_api.TokenStrategy, acquire=mock.AsyncMock(return_value="Bearer ok.ok.ok"))

        with pytest.raises(exit_exception):
            await rest_client._perform_request(route)

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"

    @hikari_test_helpers.timeout()
    async def test_perform_request_retries_strategy_once(self, rest_client, exit_exception):
        class StubResponse:
            status = http.HTTPStatus.UNAUTHORIZED
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value", "HEADER": "value"}

            async def read(self):
                return '{"something": null}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request = hikari_test_helpers.CopyingAsyncMock(
            side_effect=[StubResponse(), exit_exception]
        )
        rest_client._token = mock.Mock(
            rest_api.TokenStrategy, acquire=mock.AsyncMock(side_effect=["Bearer ok.ok.ok", "Bearer ok2.ok2.ok2"])
        )

        with pytest.raises(exit_exception):
            await rest_client._perform_request(route)

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"
        _, kwargs = rest_client._client_session.request.call_args_list[1]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok2.ok2.ok2"

    @hikari_test_helpers.timeout()
    async def test_perform_request_raises_after_re_auth_attempt(self, rest_client, exit_exception):
        class StubResponse:
            status = http.HTTPStatus.UNAUTHORIZED
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value", "HEADER": "value"}
            real_url = "okokokok"

            async def read(self):
                return '{"something": null}'

            async def json(self):
                return {"something": None}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request = hikari_test_helpers.CopyingAsyncMock(
            side_effect=[StubResponse(), StubResponse(), StubResponse()]
        )
        rest_client._token = mock.Mock(
            rest_api.TokenStrategy, acquire=mock.AsyncMock(side_effect=["Bearer ok.ok.ok", "Bearer ok2.ok2.ok2"])
        )

        with pytest.raises(errors.UnauthorizedError):
            await rest_client._perform_request(route)

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"
        _, kwargs = rest_client._client_session.request.call_args_list[1]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok2.ok2.ok2"

    @hikari_test_helpers.timeout()
    async def test_perform_request_when__token_is_None(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception
        rest_client._token = None

        with pytest.raises(exit_exception):
            await rest_client._perform_request(route)

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]

    @hikari_test_helpers.timeout()
    async def test_perform_request_when__token_is_not_None(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception
        rest_client._token = "token"

        with pytest.raises(exit_exception):
            await rest_client._perform_request(route)

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "token"

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_no_auth_passed(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception
        rest_client._token = "token"

        with pytest.raises(exit_exception):
            await rest_client._perform_request(route, auth=None)

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]
        rest_client._bucket_manager.acquire_bucket.assert_called_once_with(route, None)
        rest_client._bucket_manager.acquire_bucket.return_value.assert_used_once()

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_auth_passed(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.side_effect = exit_exception
        rest_client._token = "token"

        with pytest.raises(exit_exception):
            await rest_client._perform_request(route, auth="ooga booga")

        _, kwargs = rest_client._client_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "ooga booga"
        rest_client._bucket_manager.acquire_bucket.assert_called_once_with(route, "ooga booga")
        rest_client._bucket_manager.acquire_bucket.return_value.assert_used_once()

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_is_NO_CONTENT(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.return_value = StubResponse()
        rest_client._parse_ratelimits = mock.AsyncMock(return_value=None)

        assert (await rest_client._perform_request(route)) is None

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_is_APPLICATION_JSON(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.OK
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value", "HEADER": "value"}

            async def read(self):
                return '{"something": null}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.return_value = StubResponse()
        rest_client._parse_ratelimits = mock.AsyncMock(return_value=None)

        assert (await rest_client._perform_request(route)) == {"something": None}

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_is_not_JSON(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.IM_USED
            content_type = "text/html"
            reason = "cause why not"
            real_url = "https://some.url"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.return_value = StubResponse()
        rest_client._parse_ratelimits = mock.AsyncMock(return_value=None)

        with pytest.raises(errors.HTTPError):
            await rest_client._perform_request(route)

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_response_unhandled_status(self, rest_client, exit_exception):
        class StubResponse:
            status = http.HTTPStatus.NOT_IMPLEMENTED
            content_type = "text/html"
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.return_value = StubResponse()

        rest_client._parse_ratelimits = mock.AsyncMock(return_value=None)

        with mock.patch.object(net, "generate_error_response", return_value=exit_exception):
            with pytest.raises(exit_exception):
                await rest_client._perform_request(route)

    @hikari_test_helpers.timeout()
    async def test_perform_request_when_status_in_retry_codes_will_retry_until_exhausted(
        self, rest_client, exit_exception
    ):
        class StubResponse:
            status = http.HTTPStatus.INTERNAL_SERVER_ERROR

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.return_value = StubResponse()
        rest_client._max_retries = 3
        rest_client._parse_ratelimits = mock.AsyncMock(return_value=None)

        stack = contextlib.ExitStack()
        stack.enter_context(pytest.raises(exit_exception))
        exponential_backoff = stack.enter_context(
            mock.patch.object(
                rate_limits,
                "ExponentialBackOff",
                return_value=mock.Mock(__next__=mock.Mock(side_effect=[1, 2, 3, 4, 5])),
            )
        )
        asyncio_sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        generate_error_response = stack.enter_context(
            mock.patch.object(net, "generate_error_response", return_value=exit_exception)
        )

        with stack:
            await rest_client._perform_request(route)

        assert exponential_backoff.return_value.__next__.call_count == 3
        exponential_backoff.assert_called_once_with(maximum=16)
        asyncio_sleep.assert_has_awaits([mock.call(1), mock.call(2), mock.call(3)])
        generate_error_response.assert_called_once_with(rest_client._client_session.request.return_value)

    @hikari_test_helpers.timeout()
    @pytest.mark.parametrize("exception", [asyncio.TimeoutError, aiohttp.ClientConnectionError])
    async def test_perform_request_when_connection_error_will_retry_until_exhausted(self, rest_client, exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exception))
        rest_client._max_retries = 3
        rest_client._parse_ratelimits = mock.AsyncMock()
        rest_client._client_session = mock_session

        stack = contextlib.ExitStack()
        stack.enter_context(pytest.raises(errors.HTTPError))
        exponential_backoff = stack.enter_context(
            mock.patch.object(
                rate_limits,
                "ExponentialBackOff",
                return_value=mock.Mock(__next__=mock.Mock(side_effect=[1, 2, 3, 4, 5])),
            )
        )
        asyncio_sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))

        with stack:
            await rest_client._perform_request(route)

        assert exponential_backoff.return_value.__next__.call_count == 3
        exponential_backoff.assert_called_once_with(maximum=16)
        asyncio_sleep.assert_has_awaits([mock.call(1), mock.call(2), mock.call(3)])

    @pytest.mark.parametrize("enabled", [True, False])
    @hikari_test_helpers.timeout()
    async def test_perform_request_logger(self, rest_client, enabled):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            headers = {}
            reason = "cause why not"

            async def read(self):
                return None

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client._client_session.request.return_value = StubResponse()
        rest_client._parse_ratelimits = mock.AsyncMock(return_value=None)

        with mock.patch.object(rest, "_LOGGER", new=mock.Mock(isEnabledFor=mock.Mock(return_value=enabled))) as logger:
            await rest_client._perform_request(route)

        if enabled:
            assert logger.log.call_count == 2
        else:
            assert logger.log.call_count == 0

    async def test__parse_ratelimits_when_bucket_provided_updates_rate_limits(self, rest_client):
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

        assert await rest_client._parse_ratelimits(route, "auth", response) is None

        rest_client._bucket_manager.update_rate_limits.assert_called_once_with(
            compiled_route=route,
            bucket_header="bucket_header",
            authentication="auth",
            remaining_header=987654321,
            limit_header=123456789,
            reset_after=12.2,
        )

    async def test__parse_ratelimits_when_not_ratelimited(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.OK
            headers = {}

            json = mock.AsyncMock()

        response = StubResponse()
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)

        await rest_client._parse_ratelimits(route, "auth", response)

        response.json.assert_not_called()

    async def test__parse_ratelimits_when_ratelimited(self, rest_client, exit_exception):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}

            async def read(self):
                raise exit_exception

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(exit_exception):
            await rest_client._parse_ratelimits(route, "auth", StubResponse())

    async def test__parse_ratelimits_when_unexpected_content_type(self, rest_client):
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

    async def test__parse_ratelimits_when_global_ratelimit(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return '{"global": true, "retry_after": "2"}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        assert (await rest_client._parse_ratelimits(route, "auth", StubResponse())) == 0

        rest_client._bucket_manager.throttle.assert_called_once_with(2.0)

    async def test__parse_ratelimits_when_remaining_header_under_or_equal_to_0(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {rest._X_RATELIMIT_REMAINING_HEADER: "0"}
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "2", "global": False}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        assert await rest_client._parse_ratelimits(route, "some auth", StubResponse()) == 0

    async def test__parse_ratelimits_when_retry_after_is_not_too_long(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return '{"retry_after": "0.002"}'

        rest_client._bucket_manager.max_rate_limit = 10

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        assert await rest_client._parse_ratelimits(route, "some auth", StubResponse()) == 0.002

    async def test__parse_ratelimits_when_retry_after_is_too_long(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return '{"retry_after": "4"}'

        rest_client._bucket_manager.max_rate_limit = 3

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(errors.RateLimitTooLongError):
            await rest_client._parse_ratelimits(route, "auth", StubResponse())

    #############
    # Endpoints #
    #############

    async def test_fetch_channel(self, rest_client):
        expected_route = routes.GET_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload": "NO"})

        assert await rest_client.fetch_channel(StubModel(123)) == mock_object
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)

    async def test_fetch_channel_with_dm_channel_when_cacheful(self, rest_client, mock_cache):
        expected_route = routes.GET_CHANNEL.compile(channel=123)
        mock_object = mock.Mock(spec=channels.DMChannel, type=channels.ChannelType.DM)
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload": "NO"})

        assert await rest_client.fetch_channel(StubModel(123)) == mock_object
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)
        mock_cache.set_dm_channel_id.assert_called_once_with(mock_object.recipient.id, mock_object.id)

    async def test_fetch_channel_with_dm_channel_when_cacheless(self, rest_client, mock_cache):
        expected_route = routes.GET_CHANNEL.compile(channel=123)
        mock_object = mock.Mock(spec=channels.DMChannel, type=channels.ChannelType.DM)
        rest_client._cache = None
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload": "NO"})

        assert await rest_client.fetch_channel(StubModel(123)) == mock_object
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)
        mock_cache.set_dm_channel_id.assert_not_called()

    @pytest.mark.parametrize(
        ("emoji", "expected_emoji_id", "expected_emoji_name"),
        [(123, 123, None), ("emoji", None, "emoji"), (None, None, None)],
    )
    @pytest.mark.parametrize(
        ("auto_archive_duration", "default_auto_archive_duration"),
        [(12322, 445123), (datetime.timedelta(minutes=12322), datetime.timedelta(minutes=445123)), (12322.0, 445123.1)],
    )
    async def test_edit_channel(
        self,
        rest_client,
        auto_archive_duration,
        default_auto_archive_duration,
        emoji,
        expected_emoji_id,
        expected_emoji_name,
    ):
        expected_route = routes.PATCH_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload": "GO"})
        rest_client._entity_factory.serialize_permission_overwrite = mock.Mock(
            return_value={"type": "member", "allow": 1024, "deny": 8192, "id": "1235431"}
        )
        rest_client._entity_factory.serialize_forum_tag = mock.Mock(
            return_value={"id": 0, "name": "testing", "moderated": True, "emoji_id": None, "emoji_name": None}
        )
        expected_json = {
            "name": "new name",
            "position": 1,
            "rtc_region": "ostrich-city",
            "topic": "new topic",
            "nsfw": True,
            "bitrate": 10,
            "video_quality_mode": 2,
            "user_limit": 100,
            "rate_limit_per_user": 30,
            "parent_id": "1234",
            "permission_overwrites": [{"type": "member", "allow": 1024, "deny": 8192, "id": "1235431"}],
            "default_auto_archive_duration": 445123,
            "default_thread_rate_limit_per_user": 40,
            "default_forum_layout": 1,
            "default_sort_order": 0,
            "default_reaction_emoji": {"emoji_id": expected_emoji_id, "emoji_name": expected_emoji_name},
            "available_tags": [{"id": 0, "name": "testing", "moderated": True, "emoji_id": None, "emoji_name": None}],
            "archived": True,
            "locked": False,
            "invitable": True,
            "auto_archive_duration": 12322,
            "flags": 12,
            "applied_tags": ["0"],
        }

        result = await rest_client.edit_channel(
            StubModel(123),
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
            parent_category=StubModel(1234),
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
            flags=12,
            applied_tags=[StubModel(0)],
        )

        assert result == mock_object
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="some reason :)")
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)

    async def test_edit_channel_without_optionals(self, rest_client):
        expected_route = routes.PATCH_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload": "no"})

        assert await rest_client.edit_channel(StubModel(123)) == mock_object
        rest_client._request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)

    async def test_delete_channel(self, rest_client):
        expected_route = routes.DELETE_CHANNEL.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "NNNNN"})

        result = await rest_client.delete_channel(StubModel(123), reason="some reason :)")

        assert result is rest_client._entity_factory.deserialize_channel.return_value
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route, reason="some reason :)")

    async def test_delete_channel_without_optionals(self, rest_client):
        expected_route = routes.DELETE_CHANNEL.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "NNNNN"})

        result = await rest_client.delete_channel(StubModel(123))

        assert result is rest_client._entity_factory.deserialize_channel.return_value
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route, reason=undefined.UNDEFINED)

    async def test_edit_my_voice_state_when_requesting_to_speak(self, rest_client):
        rest_client._request = mock.AsyncMock()
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=5421)
        mock_datetime = mock.Mock(isoformat=mock.Mock(return_value="blamblamblam"))

        with mock.patch.object(time, "utc_datetime", return_value=mock_datetime):
            result = await rest_client.edit_my_voice_state(
                StubModel(5421), StubModel(999), suppress=True, request_to_speak=True
            )

            time.utc_datetime.assert_called_once()
            mock_datetime.isoformat.assert_called_once()

        assert result is None
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"channel_id": "999", "suppress": True, "request_to_speak_timestamp": "blamblamblam"}
        )

    async def test_edit_my_voice_state_when_revoking_speak_request(self, rest_client):
        rest_client._request = mock.AsyncMock()
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=5421)

        result = await rest_client.edit_my_voice_state(
            StubModel(5421), StubModel(999), suppress=True, request_to_speak=False
        )

        assert result is None
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"channel_id": "999", "suppress": True, "request_to_speak_timestamp": None}
        )

    async def test_fetch_my_voice_state(self, rest_client):
        expected_route = routes.GET_MY_GUILD_VOICE_STATE.compile(guild=5454)

        expected_json = {
            "guild_id": "5454",
            "channel_id": "3940568093485",
            "user_id": "237890809345627",
            "member": {
                "nick": "foobarbaz",
                "roles": ["11111", "22222", "33333", "44444"],
                "joined_at": "2015-04-26T06:26:56.936000+00:00",
                "premium_since": "2019-05-17T06:26:56.936000+00:00",
                "avatar": "estrogen",
                "deaf": False,
                "mute": True,
                "pending": False,
                "communication_disabled_until": "2021-10-18T06:26:56.936000+00:00",
            },
            "session_id": "39405894b9058guhfguh43t9g",
            "deaf": False,
            "mute": True,
            "self_deaf": False,
            "self_mute": True,
            "self_stream": False,
            "self_video": True,
            "suppress": False,
            "request_to_speak_timestamp": "2021-04-17T10:11:19.970105+00:00",
        }

        rest_client._request = mock.AsyncMock(return_value=expected_json)

        with mock.patch.object(
            rest_client._entity_factory, "deserialize_voice_state", return_value=mock.Mock()
        ) as patched_deserialize_voice_state:
            await rest_client.fetch_my_voice_state(StubModel(5454))

            patched_deserialize_voice_state.assert_called_once_with(expected_json)

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_voice_state(self, rest_client):
        expected_route = routes.GET_GUILD_VOICE_STATE.compile(guild=5454, user=1234567890)

        expected_json = {
            "guild_id": "5454",
            "channel_id": "3940568093485",
            "user_id": "1234567890",
            "member": {
                "nick": "foobarbaz",
                "roles": ["11111", "22222", "33333", "44444"],
                "joined_at": "2015-04-26T06:26:56.936000+00:00",
                "premium_since": "2019-05-17T06:26:56.936000+00:00",
                "avatar": "estrogen",
                "deaf": False,
                "mute": True,
                "pending": False,
                "communication_disabled_until": "2021-10-18T06:26:56.936000+00:00",
            },
            "session_id": "39405894b9058guhfguh43t9g",
            "deaf": False,
            "mute": True,
            "self_deaf": False,
            "self_mute": True,
            "self_stream": False,
            "self_video": True,
            "suppress": False,
            "request_to_speak_timestamp": "2021-04-17T10:11:19.970105+00:00",
        }

        rest_client._request = mock.AsyncMock(return_value=expected_json)

        with mock.patch.object(
            rest_client._entity_factory, "deserialize_voice_state", return_value=mock.Mock()
        ) as patched_deserialize_voice_state:
            await rest_client.fetch_voice_state(StubModel(5454), StubModel(1234567890))

            patched_deserialize_voice_state.assert_called_once_with(expected_json)

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_edit_my_voice_state_when_providing_datetime_for_request_to_speak(self, rest_client):
        rest_client._request = mock.AsyncMock()
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=5421)
        mock_datetime = mock.Mock(spec=datetime.datetime, isoformat=mock.Mock(return_value="blamblamblam2"))

        result = await rest_client.edit_my_voice_state(
            StubModel(5421), StubModel(999), suppress=True, request_to_speak=mock_datetime
        )

        assert result is None
        mock_datetime.isoformat.assert_called_once()
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"channel_id": "999", "suppress": True, "request_to_speak_timestamp": "blamblamblam2"}
        )

    async def test_edit_my_voice_state_without_optional_fields(self, rest_client):
        rest_client._request = mock.AsyncMock()
        expected_route = routes.PATCH_MY_GUILD_VOICE_STATE.compile(guild=5421)

        result = await rest_client.edit_my_voice_state(StubModel(5421), StubModel(999))

        assert result is None
        rest_client._request.assert_awaited_once_with(expected_route, json={"channel_id": "999"})

    async def test_edit_voice_state(self, rest_client):
        rest_client._request = mock.AsyncMock()
        expected_route = routes.PATCH_GUILD_VOICE_STATE.compile(guild=543123, user=32123)

        result = await rest_client.edit_voice_state(StubModel(543123), StubModel(321), StubModel(32123), suppress=True)

        assert result is None
        rest_client._request.assert_awaited_once_with(expected_route, json={"channel_id": "321", "suppress": True})

    async def test_edit_voice_state_without_optional_arguments(self, rest_client):
        rest_client._request = mock.AsyncMock()
        expected_route = routes.PATCH_GUILD_VOICE_STATE.compile(guild=543123, user=32123)

        result = await rest_client.edit_voice_state(StubModel(543123), StubModel(321), StubModel(32123))

        assert result is None
        rest_client._request.assert_awaited_once_with(expected_route, json={"channel_id": "321"})

    async def test_edit_permission_overwrite(self, rest_client):
        target = StubModel(456)
        expected_route = routes.PUT_CHANNEL_PERMISSIONS.compile(channel=123, overwrite=456)
        rest_client._request = mock.AsyncMock()
        expected_json = {"type": 1, "allow": 4, "deny": 1}

        await rest_client.edit_permission_overwrite(
            StubModel(123),
            target,
            target_type=channels.PermissionOverwriteType.MEMBER,
            allow=permissions.Permissions.BAN_MEMBERS,
            deny=permissions.Permissions.CREATE_INSTANT_INVITE,
            reason="cause why not :)",
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="cause why not :)")

    @pytest.mark.parametrize(
        ("target", "expected_type"),
        [
            (mock.Mock(users.UserImpl, id=456), channels.PermissionOverwriteType.MEMBER),
            (mock.Mock(guilds.Role, id=456), channels.PermissionOverwriteType.ROLE),
            (
                mock.Mock(channels.PermissionOverwrite, id=456, type=channels.PermissionOverwriteType.MEMBER),
                channels.PermissionOverwriteType.MEMBER,
            ),
        ],
    )
    async def test_edit_permission_overwrite_when_target_undefined(self, rest_client, target, expected_type):
        expected_route = routes.PUT_CHANNEL_PERMISSIONS.compile(channel=123, overwrite=456)
        rest_client._request = mock.AsyncMock()
        expected_json = {"type": expected_type}

        await rest_client.edit_permission_overwrite(StubModel(123), target)
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)

    async def test_edit_permission_overwrite_when_cant_determine_target_type(self, rest_client):
        with pytest.raises(TypeError):
            await rest_client.edit_permission_overwrite(StubModel(123), StubModel(123))

    async def test_delete_permission_overwrite(self, rest_client):
        expected_route = routes.DELETE_CHANNEL_PERMISSIONS.compile(channel=123, overwrite=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_permission_overwrite(StubModel(123), StubModel(456))
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_channel_invites(self, rest_client):
        invite1 = StubModel(456)
        invite2 = StubModel(789)
        expected_route = routes.GET_CHANNEL_INVITES.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_invite_with_metadata = mock.Mock(side_effect=[invite1, invite2])

        assert await rest_client.fetch_channel_invites(StubModel(123)) == [invite1, invite2]
        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_invite_with_metadata.call_count == 2
        rest_client._entity_factory.deserialize_invite_with_metadata.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_create_invite(self, rest_client):
        expected_route = routes.POST_CHANNEL_INVITES.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value={"ID": "NOOOOOOOOPOOOOOOOI!"})
        expected_json = {
            "max_age": 60,
            "max_uses": 4,
            "temporary": True,
            "unique": True,
            "target_type": invites.TargetType.STREAM,
            "target_user_id": "456",
            "target_application_id": "789",
        }

        result = await rest_client.create_invite(
            StubModel(123),
            max_age=datetime.timedelta(minutes=1),
            max_uses=4,
            temporary=True,
            unique=True,
            target_type=invites.TargetType.STREAM,
            target_user=StubModel(456),
            target_application=StubModel(789),
            reason="cause why not :)",
        )

        assert result is rest_client._entity_factory.deserialize_invite_with_metadata.return_value
        rest_client._entity_factory.deserialize_invite_with_metadata.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="cause why not :)")

    async def test_fetch_pins(self, rest_client):
        message1 = StubModel(456)
        message2 = StubModel(789)
        expected_route = routes.GET_CHANNEL_PINS.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_message = mock.Mock(side_effect=[message1, message2])

        assert await rest_client.fetch_pins(StubModel(123)) == [message1, message2]
        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_message.call_count == 2
        rest_client._entity_factory.deserialize_message.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_pin_message(self, rest_client):
        expected_route = routes.PUT_CHANNEL_PINS.compile(channel=123, message=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.pin_message(StubModel(123), StubModel(456))
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_unpin_message(self, rest_client):
        expected_route = routes.DELETE_CHANNEL_PIN.compile(channel=123, message=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.unpin_message(StubModel(123), StubModel(456))
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_message(self, rest_client):
        message_obj = mock.Mock()
        expected_route = routes.GET_CHANNEL_MESSAGE.compile(channel=123, message=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_message = mock.Mock(return_value=message_obj)

        assert await rest_client.fetch_message(StubModel(123), StubModel(456)) is message_obj
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"id": "456"})

    async def test_create_message_when_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_CHANNEL_MESSAGES.compile(channel=123456789)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.create_message(
            StubModel(123456789),
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            sticker=54234,
            stickers=[564123, 431123],
            tts=True,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
            reply=StubModel(987654321),
            reply_must_exist=False,
            flags=54123,
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
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
            b'{"testing":"ensure_in_test","message_reference":{"message_id":"987654321","fail_if_not_exists":false}}',
            content_type="application/json",
        )
        rest_client._request.assert_awaited_once_with(expected_route, form_builder=mock_form)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_create_message_when_no_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_CHANNEL_MESSAGES.compile(channel=123456789)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.create_message(
            StubModel(123456789),
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            sticker=543345,
            stickers=[123321, 6572345],
            tts=True,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
            reply=StubModel(987654321),
            reply_must_exist=False,
            flags=6643,
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            sticker=543345,
            stickers=[123321, 6572345],
            tts=True,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=6643,
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "testing": "ensure_in_test",
                "message_reference": {"message_id": "987654321", "fail_if_not_exists": False},
            },
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_crosspost_message(self, rest_client):
        expected_route = routes.POST_CHANNEL_CROSSPOST.compile(channel=444432, message=12353234)
        mock_message = object()
        rest_client._entity_factory.deserialize_message = mock.Mock(return_value=mock_message)
        rest_client._request = mock.AsyncMock(return_value={"id": "93939383883", "content": "foobar"})

        result = await rest_client.crosspost_message(StubModel(444432), StubModel(12353234))

        assert result is mock_message
        rest_client._entity_factory.deserialize_message.assert_called_once_with(
            {"id": "93939383883", "content": "foobar"}
        )
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_edit_message_when_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=123456789, message=987654321)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_message(
            StubModel(123456789),
            StubModel(987654321),
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
            flags=120,
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            flags=120,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            edit=True,
        )
        mock_form.add_field.assert_called_once_with(
            "payload_json", b'{"testing":"ensure_in_test"}', content_type="application/json"
        )
        rest_client._request.assert_awaited_once_with(expected_route, form_builder=mock_form)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_message_when_no_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_CHANNEL_MESSAGE.compile(channel=123456789, message=987654321)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_message(
            StubModel(123456789),
            StubModel(987654321),
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
            flags=120,
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            flags=120,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            edit=True,
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={"testing": "ensure_in_test"})
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_follow_channel(self, rest_client):
        expected_route = routes.POST_CHANNEL_FOLLOWERS.compile(channel=3333)
        rest_client._request = mock.AsyncMock(return_value={"channel_id": "929292", "webhook_id": "929383838"})

        result = await rest_client.follow_channel(StubModel(3333), StubModel(606060), reason="get followed")

        assert result is rest_client._entity_factory.deserialize_channel_follow.return_value
        rest_client._entity_factory.deserialize_channel_follow.assert_called_once_with(
            {"channel_id": "929292", "webhook_id": "929383838"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"webhook_channel_id": "606060"}, reason="get followed"
        )

    async def test_delete_message(self, rest_client):
        expected_route = routes.DELETE_CHANNEL_MESSAGE.compile(channel=123, message=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_message(StubModel(123), StubModel(456), reason="broke laws")
        rest_client._request.assert_awaited_once_with(expected_route, reason="broke laws")

    async def test_delete_messages(self, rest_client):
        messages = [StubModel(i) for i in range(200)]
        expected_route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=123)
        expected_json1 = {"messages": [str(i) for i in range(100)]}
        expected_json2 = {"messages": [str(i) for i in range(100, 200)]}

        rest_client._request = mock.AsyncMock()

        await rest_client.delete_messages(StubModel(123), *messages, reason="broke laws")

        rest_client._request.assert_has_awaits(
            [
                mock.call(expected_route, json=expected_json1, reason="broke laws"),
                mock.call(expected_route, json=expected_json2, reason="broke laws"),
            ]
        )

    async def test_delete_messages_when_one_message_left_in_chunk_and_delete_message_raises_message_not_found(
        self, rest_client
    ):
        channel = StubModel(123)
        messages = [StubModel(i) for i in range(101)]
        message = messages[-1]
        expected_json = {"messages": [str(i) for i in range(100)]}

        rest_client._request = mock.AsyncMock()
        rest_client.delete_message = mock.AsyncMock(
            side_effect=errors.NotFoundError(url="", headers={}, raw_body="", code=10008)
        )

        await rest_client.delete_messages(channel, *messages, reason="broke laws")

        rest_client._request.assert_awaited_once_with(
            routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel), json=expected_json, reason="broke laws"
        )
        rest_client.delete_message.assert_awaited_once_with(channel, message, reason="broke laws")

    async def test_delete_messages_when_one_message_left_in_chunk_and_delete_message_raises_channel_not_found(
        self, rest_client
    ):
        channel = StubModel(123)
        messages = [StubModel(i) for i in range(101)]
        message = messages[-1]
        expected_json = {"messages": [str(i) for i in range(100)]}

        rest_client._request = mock.AsyncMock()
        mock_not_found = errors.NotFoundError(url="", headers={}, raw_body="", code=10003)
        rest_client.delete_message = mock.AsyncMock(side_effect=mock_not_found)

        with pytest.raises(errors.BulkDeleteError) as exc_info:
            await rest_client.delete_messages(channel, *messages, reason="broke laws")

        assert exc_info.value.__cause__ is mock_not_found

        rest_client._request.assert_awaited_once_with(
            routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel), json=expected_json, reason="broke laws"
        )
        rest_client.delete_message.assert_awaited_once_with(channel, message, reason="broke laws")

    async def test_delete_messages_when_one_message_left_in_chunk(self, rest_client):
        channel = StubModel(123)
        messages = [StubModel(i) for i in range(101)]
        message = messages[-1]
        expected_json = {"messages": [str(i) for i in range(100)]}

        rest_client._request = mock.AsyncMock()

        await rest_client.delete_messages(channel, *messages, reason="broke laws")

        rest_client._request.assert_has_awaits(
            [
                mock.call(
                    routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel),
                    json=expected_json,
                    reason="broke laws",
                ),
                mock.call(routes.DELETE_CHANNEL_MESSAGE.compile(channel=channel, message=message), reason="broke laws"),
            ]
        )

    async def test_delete_messages_when_exception(self, rest_client):
        channel = StubModel(123)
        messages = [StubModel(i) for i in range(101)]

        rest_client._request = mock.AsyncMock(side_effect=Exception)

        with pytest.raises(errors.BulkDeleteError):
            await rest_client.delete_messages(channel, *messages)

    async def test_delete_messages_with_iterable(self, rest_client):
        channel = StubModel(54123)
        messages = (StubModel(i) for i in range(101))

        rest_client._request = mock.AsyncMock()

        await rest_client.delete_messages(channel, messages, StubModel(444), StubModel(6523), reason="broke laws")

        rest_client._request.assert_has_awaits(
            [
                mock.call(
                    routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel),
                    json={"messages": [str(i) for i in range(100)]},
                    reason="broke laws",
                ),
                mock.call(
                    routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel),
                    json={"messages": ["100", "444", "6523"]},
                    reason="broke laws",
                ),
            ]
        )

    async def test_delete_messages_with_async_iterable(self, rest_client):
        channel = StubModel(54123)
        iterator = iterators.FlatLazyIterator(StubModel(i) for i in range(103))

        rest_client._request = mock.AsyncMock()

        await rest_client.delete_messages(channel, iterator, reason="broke laws")

        rest_client._request.assert_has_awaits(
            [
                mock.call(
                    routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel),
                    json={"messages": [str(i) for i in range(100)]},
                    reason="broke laws",
                ),
                mock.call(
                    routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel),
                    json={"messages": ["100", "101", "102"]},
                    reason="broke laws",
                ),
            ]
        )

    async def test_delete_messages_with_async_iterable_and_args(self, rest_client):
        with pytest.raises(TypeError, match=re.escape("Cannot use *args with an async iterable.")):
            await rest_client.delete_messages(54123, iterators.FlatLazyIterator(()), 1, 2)

    async def test_add_reaction(self, rest_client):
        expected_route = routes.PUT_MY_REACTION.compile(emoji="rooYay:123", channel=123, message=456)
        rest_client._request = mock.AsyncMock()

        with mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"):
            await rest_client.add_reaction(StubModel(123), StubModel(456), "<:rooYay:123>")

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_my_reaction(self, rest_client):
        expected_route = routes.DELETE_MY_REACTION.compile(emoji="rooYay:123", channel=123, message=456)
        rest_client._request = mock.AsyncMock()

        with mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"):
            await rest_client.delete_my_reaction(StubModel(123), StubModel(456), "<:rooYay:123>")

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_all_reactions_for_emoji(self, rest_client):
        expected_route = routes.DELETE_REACTION_EMOJI.compile(emoji="rooYay:123", channel=123, message=456)
        rest_client._request = mock.AsyncMock()

        with mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"):
            await rest_client.delete_all_reactions_for_emoji(StubModel(123), StubModel(456), "<:rooYay:123>")

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_reaction(self, rest_client):
        expected_route = routes.DELETE_REACTION_USER.compile(emoji="rooYay:123", channel=123, message=456, user=789)
        rest_client._request = mock.AsyncMock()

        with mock.patch.object(rest, "_transform_emoji_to_url_format", return_value="rooYay:123"):
            await rest_client.delete_reaction(StubModel(123), StubModel(456), StubModel(789), "<:rooYay:123>")

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_all_reactions(self, rest_client):
        expected_route = routes.DELETE_ALL_REACTIONS.compile(channel=123, message=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_all_reactions(StubModel(123), StubModel(456))
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_create_webhook(self, rest_client, file_resource_patch):
        webhook = StubModel(456)
        expected_route = routes.POST_CHANNEL_WEBHOOKS.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        expected_json = {"name": "test webhook", "avatar": "some data"}
        rest_client._entity_factory.deserialize_incoming_webhook = mock.Mock(return_value=webhook)

        returned = await rest_client.create_webhook(
            StubModel(123), "test webhook", avatar="someavatar.png", reason="why not"
        )
        assert returned is webhook

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="why not")
        rest_client._entity_factory.deserialize_incoming_webhook.assert_called_once_with({"id": "456"})

    async def test_create_webhook_without_optionals(self, rest_client):
        webhook = StubModel(456)
        expected_route = routes.POST_CHANNEL_WEBHOOKS.compile(channel=123)
        expected_json = {"name": "test webhook"}
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_incoming_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.create_webhook(StubModel(123), "test webhook") is webhook
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_incoming_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook(self, rest_client):
        webhook = StubModel(123)
        expected_route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=123, token="token")
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.fetch_webhook(StubModel(123), token="token") is webhook
        rest_client._request.assert_awaited_once_with(expected_route, auth=None)
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook_without_token(self, rest_client):
        webhook = StubModel(123)
        expected_route = routes.GET_WEBHOOK.compile(webhook=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.fetch_webhook(StubModel(123)) is webhook
        rest_client._request.assert_awaited_once_with(expected_route, auth=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_channel_webhooks(self, rest_client):
        webhook1 = StubModel(456)
        webhook2 = StubModel(789)
        expected_route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_webhook = mock.Mock(side_effect=[webhook1, webhook2])

        assert await rest_client.fetch_channel_webhooks(StubModel(123)) == [webhook1, webhook2]
        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_webhook.call_count == 2
        rest_client._entity_factory.deserialize_webhook.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_channel_webhooks_ignores_unrecognised_webhook_type(self, rest_client):
        webhook1 = StubModel(456)
        expected_route = routes.GET_CHANNEL_WEBHOOKS.compile(channel=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_webhook = mock.Mock(
            side_effect=[errors.UnrecognisedEntityError("yeet"), webhook1]
        )

        assert await rest_client.fetch_channel_webhooks(StubModel(123)) == [webhook1]
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_webhook.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_guild_webhooks(self, rest_client):
        webhook1 = StubModel(456)
        webhook2 = StubModel(789)
        expected_route = routes.GET_GUILD_WEBHOOKS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_webhook = mock.Mock(side_effect=[webhook1, webhook2])

        assert await rest_client.fetch_guild_webhooks(StubModel(123)) == [webhook1, webhook2]
        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_webhook.call_count == 2
        rest_client._entity_factory.deserialize_webhook.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_guild_webhooks_ignores_unrecognised_webhook_types(self, rest_client):
        webhook1 = StubModel(456)
        expected_route = routes.GET_GUILD_WEBHOOKS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_webhook = mock.Mock(
            side_effect=[errors.UnrecognisedEntityError("meow meow"), webhook1]
        )

        assert await rest_client.fetch_guild_webhooks(StubModel(123)) == [webhook1]
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_webhook.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_edit_webhook(self, rest_client):
        webhook = StubModel(456)
        expected_route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(webhook=123, token="token")
        expected_json = {"name": "some other name", "channel": "789", "avatar": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        returned = await rest_client.edit_webhook(
            StubModel(123),
            token="token",
            name="some other name",
            avatar=None,
            channel=StubModel(789),
            reason="some smart reason to do this",
        )
        assert returned is webhook

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason="some smart reason to do this", auth=None
        )
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_edit_webhook_without_token(self, rest_client):
        webhook = StubModel(456)
        expected_route = routes.PATCH_WEBHOOK.compile(webhook=123)
        expected_json = {}
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        returned = await rest_client.edit_webhook(StubModel(123))
        assert returned is webhook

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason=undefined.UNDEFINED, auth=undefined.UNDEFINED
        )
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_edit_webhook_when_avatar_is_file(self, rest_client, file_resource_patch):
        webhook = StubModel(456)
        expected_route = routes.PATCH_WEBHOOK.compile(webhook=123)
        expected_json = {"avatar": "some data"}
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.edit_webhook(StubModel(123), avatar="someavatar.png") is webhook

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason=undefined.UNDEFINED, auth=undefined.UNDEFINED
        )
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_delete_webhook(self, rest_client):
        expected_route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(webhook=123, token="token")
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})

        await rest_client.delete_webhook(StubModel(123), token="token")
        rest_client._request.assert_awaited_once_with(expected_route, auth=None)

    async def test_delete_webhook_without_token(self, rest_client):
        expected_route = routes.DELETE_WEBHOOK.compile(webhook=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})

        await rest_client.delete_webhook(StubModel(123))
        rest_client._request.assert_awaited_once_with(expected_route, auth=undefined.UNDEFINED)

    @pytest.mark.parametrize(
        ("webhook", "avatar_url"),
        [
            (mock.Mock(webhooks.ExecutableWebhook, webhook_id=432), files.URL("https://website.com/davfsa_logo")),
            (432, "https://website.com/davfsa_logo"),
        ],
    )
    async def test_execute_webhook_when_form(self, rest_client, webhook, avatar_url):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=432, token="hi, im a token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

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
            tts=True,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=120,
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
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
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_form, query={"wait": "true"}, auth=None
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_execute_webhook_when_form_and_thread(self, rest_client):
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=432, token="hi, im a token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.execute_webhook(
            432, "hi, im a token", content="new content", thread=StubModel(1234543123)
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            component=undefined.UNDEFINED,
            components=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )
        mock_form.add_field.assert_called_once_with(
            "payload_json", b'{"testing":"ensure_in_test"}', content_type="application/json"
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_form, query={"wait": "true", "thread_id": "1234543123"}, auth=None
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_execute_webhook_when_no_form(self, rest_client):
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=432, token="hi, im a token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.execute_webhook(
            432, "hi, im a token", content="new content", thread=StubModel(2134312123)
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            component=undefined.UNDEFINED,
            components=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"testing": "ensure_in_test"},
            query={"wait": "true", "thread_id": "2134312123"},
            auth=None,
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_execute_webhook_when_thread_and_no_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_WEBHOOK_WITH_TOKEN.compile(webhook=432, token="hi, im a token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

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
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"testing": "ensure_in_test", "username": "davfsa", "avatar_url": "https://website.com/davfsa_logo"},
            query={"wait": "true"},
            auth=None,
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    @pytest.mark.parametrize("webhook", [mock.Mock(webhooks.ExecutableWebhook, webhook_id=432), 432])
    async def test_fetch_webhook_message(self, rest_client, webhook):
        message_obj = object()
        expected_route = routes.GET_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_message = mock.Mock(return_value=message_obj)

        assert await rest_client.fetch_webhook_message(webhook, "hi, im a token", StubModel(456)) is message_obj

        rest_client._request.assert_awaited_once_with(expected_route, auth=None, query={})
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook_message_when_thread(self, rest_client):
        message_obj = object()
        expected_route = routes.GET_WEBHOOK_MESSAGE.compile(webhook=43234312, token="hi, im a token", message=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_message = mock.Mock(return_value=message_obj)

        result = await rest_client.fetch_webhook_message(
            43234312, "hi, im a token", StubModel(456), thread=StubModel(54123123)
        )

        assert result is message_obj
        rest_client._request.assert_awaited_once_with(expected_route, auth=None, query={"thread_id": "54123123"})
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"id": "456"})

    @pytest.mark.parametrize("webhook", [mock.Mock(webhooks.ExecutableWebhook, webhook_id=432), 432])
    async def test_edit_webhook_message_when_form(self, rest_client, webhook):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=456)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_webhook_message(
            webhook,
            "hi, im a token",
            StubModel(456),
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
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
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
        rest_client._request.assert_awaited_once_with(expected_route, form_builder=mock_form, query={}, auth=None)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_webhook_message_when_form_and_thread(self, rest_client):
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=12354123, token="hi, im a token", message=456)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_webhook_message(
            12354123, "hi, im a token", StubModel(456), content="new content", thread=StubModel(123543123)
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
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
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_form, query={"thread_id": "123543123"}, auth=None
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_webhook_message_when_no_form(self, rest_client: rest_api.RESTClient):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=456)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_webhook_message(
            432,
            "hi, im a token",
            StubModel(456),
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
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
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
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"testing": "ensure_in_test"}, query={}, auth=None
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_webhook_message_when_thread_and_no_form(self, rest_client: rest_api.RESTClient):
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_WEBHOOK_MESSAGE.compile(webhook=432, token="hi, im a token", message=456)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_webhook_message(
            432, "hi, im a token", StubModel(456), content="new content", thread=StubModel(2346523432)
        )
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
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
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"testing": "ensure_in_test"}, query={"thread_id": "2346523432"}, auth=None
        )
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    @pytest.mark.parametrize("webhook", [mock.Mock(webhooks.ExecutableWebhook, webhook_id=123), 123])
    async def test_delete_webhook_message(self, rest_client, webhook):
        expected_route = routes.DELETE_WEBHOOK_MESSAGE.compile(webhook=123, token="token", message=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_webhook_message(webhook, "token", StubModel(456))

        rest_client._request.assert_awaited_once_with(expected_route, auth=None, query={})

    async def test_delete_webhook_message_when_thread(self, rest_client):
        expected_route = routes.DELETE_WEBHOOK_MESSAGE.compile(webhook=123, token="token", message=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_webhook_message(123, "token", StubModel(456), thread=StubModel(432123))

        rest_client._request.assert_awaited_once_with(expected_route, auth=None, query={"thread_id": "432123"})

    async def test_fetch_gateway_url(self, rest_client):
        expected_route = routes.GET_GATEWAY.compile()
        rest_client._request = mock.AsyncMock(return_value={"url": "wss://some.url"})

        assert await rest_client.fetch_gateway_url() == "wss://some.url"

        rest_client._request.assert_awaited_once_with(expected_route, auth=None)

    async def test_fetch_gateway_bot(self, rest_client):
        bot = StubModel(123)
        expected_route = routes.GET_GATEWAY_BOT.compile()
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_gateway_bot_info = mock.Mock(return_value=bot)

        assert await rest_client.fetch_gateway_bot_info() is bot

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_gateway_bot_info.assert_called_once_with({"id": "123"})

    async def test_fetch_invite(self, rest_client):
        return_invite = StubModel()
        input_invite = StubModel()
        input_invite.code = "Jx4cNGG"
        expected_route = routes.GET_INVITE.compile(invite_code="Jx4cNGG")
        rest_client._request = mock.AsyncMock(return_value={"code": "Jx4cNGG"})
        rest_client._entity_factory.deserialize_invite = mock.Mock(return_value=return_invite)

        assert await rest_client.fetch_invite(input_invite, with_counts=True, with_expiration=False) == return_invite
        rest_client._request.assert_awaited_once_with(
            expected_route, query={"with_counts": "true", "with_expiration": "false"}
        )
        rest_client._entity_factory.deserialize_invite.assert_called_once_with({"code": "Jx4cNGG"})

    async def test_delete_invite(self, rest_client):
        input_invite = StubModel()
        input_invite.code = "Jx4cNGG"
        expected_route = routes.DELETE_INVITE.compile(invite_code="Jx4cNGG")
        rest_client._request = mock.AsyncMock(return_value={"ok": "NO"})

        result = await rest_client.delete_invite(input_invite)

        assert result is rest_client._entity_factory.deserialize_invite.return_value

        rest_client._entity_factory.deserialize_invite.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_my_user(self, rest_client):
        user = StubModel(123)
        expected_route = routes.GET_MY_USER.compile()
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.fetch_my_user() is user

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user(self, rest_client):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username"}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username") is user

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_avatar_is_None(self, rest_client):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "avatar": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username", avatar=None) is user

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_avatar_is_file(self, rest_client, file_resource_patch):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "avatar": "some data"}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username", avatar="someavatar.png") is user

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_banner_is_None(self, rest_client):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "banner": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username", banner=None) is user

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_banner_is_file(self, rest_client, file_resource_patch):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "banner": "some data"}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username", banner="somebanner.png") is user

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_fetch_my_connections(self, rest_client):
        connection1 = StubModel(123)
        connection2 = StubModel(456)
        expected_route = routes.GET_MY_CONNECTIONS.compile()
        rest_client._request = mock.AsyncMock(return_value=[{"id": "123"}, {"id": "456"}])
        rest_client._entity_factory.deserialize_own_connection = mock.Mock(side_effect=[connection1, connection2])

        assert await rest_client.fetch_my_connections() == [connection1, connection2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_own_connection.call_count == 2
        rest_client._entity_factory.deserialize_own_connection.assert_has_calls(
            [mock.call({"id": "123"}), mock.call({"id": "456"})]
        )

    async def test_leave_guild(self, rest_client):
        expected_route = routes.DELETE_MY_GUILD.compile(guild=123)
        rest_client._request = mock.AsyncMock()

        await rest_client.leave_guild(StubModel(123))

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_create_dm_channel(self, rest_client, mock_cache):
        dm_channel = StubModel(43234)
        user = StubModel(123)
        expected_route = routes.POST_MY_CHANNELS.compile()
        expected_json = {"recipient_id": "123"}
        rest_client._request = mock.AsyncMock(return_value={"id": "43234"})
        rest_client._entity_factory.deserialize_dm = mock.Mock(return_value=dm_channel)

        assert await rest_client.create_dm_channel(user) == dm_channel

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_dm.assert_called_once_with({"id": "43234"})
        mock_cache.set_dm_channel_id.assert_called_once_with(user, dm_channel.id)

    async def test_create_dm_channel_when_cacheless(self, rest_client, mock_cache):
        rest_client._cache = None
        dm_channel = StubModel(43234)
        expected_route = routes.POST_MY_CHANNELS.compile()
        expected_json = {"recipient_id": "123"}
        rest_client._request = mock.AsyncMock(return_value={"id": "43234"})
        rest_client._entity_factory.deserialize_dm = mock.Mock(return_value=dm_channel)

        assert await rest_client.create_dm_channel(StubModel(123)) == dm_channel

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_dm.assert_called_once_with({"id": "43234"})
        mock_cache.set_dm_channel_id.assert_not_called()

    async def test_fetch_application(self, rest_client):
        application = StubModel(123)
        expected_route = routes.GET_MY_APPLICATION.compile()
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_application = mock.Mock(return_value=application)

        assert await rest_client.fetch_application() is application

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_application.assert_called_once_with({"id": "123"})

    async def test_fetch_authorization(self, rest_client):
        expected_route = routes.GET_MY_AUTHORIZATION.compile()
        rest_client._request = mock.AsyncMock(return_value={"application": {}})

        result = await rest_client.fetch_authorization()

        assert result is rest_client._entity_factory.deserialize_authorization_information.return_value

        rest_client._entity_factory.deserialize_authorization_information.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_authorize_client_credentials_token(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": "43212123123123"})

        with mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form):
            await rest_client.authorize_client_credentials_token(65234123, "4312312", scopes=["scope1", "scope2"])

        mock_url_encoded_form.add_field.assert_has_calls(
            [mock.call("grant_type", "client_credentials"), mock.call("scope", "scope1 scope2")]
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NjUyMzQxMjM6NDMxMjMxMg=="
        )
        rest_client._entity_factory.deserialize_partial_token.assert_called_once_with(rest_client._request.return_value)

    async def test_authorize_access_token_without_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form):
            result = await rest_client.authorize_access_token(65234, "43123", "a.code", "htt:redirect//me")

        mock_url_encoded_form.add_field.assert_has_calls(
            [
                mock.call("grant_type", "authorization_code"),
                mock.call("code", "a.code"),
                mock.call("redirect_uri", "htt:redirect//me"),
            ]
        )
        assert result is rest_client._entity_factory.deserialize_authorization_token.return_value
        rest_client._entity_factory.deserialize_authorization_token.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NjUyMzQ6NDMxMjM="
        )

    async def test_authorize_access_token_with_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form):
            result = await rest_client.authorize_access_token(12343, "1235555", "a.codee", "htt:redirect//mee")

        mock_url_encoded_form.add_field.assert_has_calls(
            [
                mock.call("grant_type", "authorization_code"),
                mock.call("code", "a.codee"),
                mock.call("redirect_uri", "htt:redirect//mee"),
            ]
        )
        assert result is rest_client._entity_factory.deserialize_authorization_token.return_value
        rest_client._entity_factory.deserialize_authorization_token.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic MTIzNDM6MTIzNTU1NQ=="
        )

    async def test_refresh_access_token_without_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form):
            result = await rest_client.refresh_access_token(454123, "123123", "a.codet")

        mock_url_encoded_form.add_field.assert_has_calls(
            [mock.call("grant_type", "refresh_token"), mock.call("refresh_token", "a.codet")]
        )
        assert result is rest_client._entity_factory.deserialize_authorization_token.return_value
        rest_client._entity_factory.deserialize_authorization_token.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NDU0MTIzOjEyMzEyMw=="
        )

    async def test_refresh_access_token_with_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form):
            result = await rest_client.refresh_access_token(54123, "312312", "a.codett", scopes=["1", "3", "scope43"])

        mock_url_encoded_form.add_field.assert_has_calls(
            [
                mock.call("grant_type", "refresh_token"),
                mock.call("refresh_token", "a.codett"),
                mock.call("scope", "1 3 scope43"),
            ]
        )
        assert result is rest_client._entity_factory.deserialize_authorization_token.return_value
        rest_client._entity_factory.deserialize_authorization_token.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NTQxMjM6MzEyMzEy"
        )

    async def test_revoke_access_token(self, rest_client):
        expected_route = routes.POST_TOKEN_REVOKE.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock()

        with mock.patch.object(data_binding, "URLEncodedFormBuilder", return_value=mock_url_encoded_form):
            await rest_client.revoke_access_token(54123, "123542", "not.a.token")

        mock_url_encoded_form.add_field.assert_called_once_with("token", "not.a.token")
        rest_client._request.assert_awaited_once_with(
            expected_route, form_builder=mock_url_encoded_form, auth="Basic NTQxMjM6MTIzNTQy"
        )

    async def test_add_user_to_guild(self, rest_client):
        member = StubModel(789)
        expected_route = routes.PUT_GUILD_MEMBER.compile(guild=123, user=456)
        expected_json = {
            "access_token": "token",
            "nick": "cool nick",
            "roles": ["234", "567"],
            "mute": True,
            "deaf": False,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})
        rest_client._entity_factory.deserialize_member = mock.Mock(return_value=member)

        returned = await rest_client.add_user_to_guild(
            "token",
            StubModel(123),
            StubModel(456),
            nickname="cool nick",
            roles=[StubModel(234), StubModel(567)],
            mute=True,
            deaf=False,
        )
        assert returned is member

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_member.assert_called_once_with({"id": "789"}, guild_id=123)

    async def test_add_user_to_guild_when_already_in_guild(self, rest_client):
        expected_route = routes.PUT_GUILD_MEMBER.compile(guild=123, user=456)
        expected_json = {"access_token": "token"}
        rest_client._request = mock.AsyncMock(return_value=None)
        rest_client._entity_factory.deserialize_member = mock.Mock()

        assert await rest_client.add_user_to_guild("token", StubModel(123), StubModel(456)) is None

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_member.assert_not_called()

    async def test_fetch_voice_regions(self, rest_client):
        voice_region1 = StubModel(123)
        voice_region2 = StubModel(456)
        expected_route = routes.GET_VOICE_REGIONS.compile()
        rest_client._request = mock.AsyncMock(return_value=[{"id": "123"}, {"id": "456"}])
        rest_client._entity_factory.deserialize_voice_region = mock.Mock(side_effect=[voice_region1, voice_region2])

        assert await rest_client.fetch_voice_regions() == [voice_region1, voice_region2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_voice_region.call_count == 2
        rest_client._entity_factory.deserialize_voice_region.assert_has_calls(
            [mock.call({"id": "123"}), mock.call({"id": "456"})]
        )

    async def test_fetch_user(self, rest_client):
        user = StubModel(456)
        expected_route = routes.GET_USER.compile(user=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_user = mock.Mock(return_value=user)

        assert await rest_client.fetch_user(StubModel(123)) is user

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_user.assert_called_once_with({"id": "456"})

    async def test_fetch_emoji(self, rest_client):
        emoji = StubModel(456)
        expected_route = routes.GET_GUILD_EMOJI.compile(emoji=456, guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(return_value=emoji)

        assert await rest_client.fetch_emoji(StubModel(123), StubModel(456)) is emoji

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_fetch_guild_emojis(self, rest_client):
        emoji1 = StubModel(456)
        emoji2 = StubModel(789)
        expected_route = routes.GET_GUILD_EMOJIS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(side_effect=[emoji1, emoji2])

        assert await rest_client.fetch_guild_emojis(StubModel(123)) == [emoji1, emoji2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_known_custom_emoji.call_count == 2
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_has_calls(
            [mock.call({"id": "456"}, guild_id=123), mock.call({"id": "789"}, guild_id=123)]
        )

    async def test_create_emoji(self, rest_client, file_resource_patch):
        emoji = StubModel(234)
        expected_route = routes.POST_GUILD_EMOJIS.compile(guild=123)
        expected_json = {"name": "rooYay", "image": "some data", "roles": ["456", "789"]}
        rest_client._request = mock.AsyncMock(return_value={"id": "234"})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(return_value=emoji)

        returned = await rest_client.create_emoji(
            StubModel(123), "rooYay", "rooYay.png", roles=[StubModel(456), StubModel(789)], reason="cause rooYay"
        )
        assert returned is emoji

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="cause rooYay")
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_called_once_with({"id": "234"}, guild_id=123)

    async def test_edit_emoji(self, rest_client):
        emoji = StubModel(234)
        expected_route = routes.PATCH_GUILD_EMOJI.compile(guild=123, emoji=456)
        expected_json = {"name": "rooYay2", "roles": ["789", "987"]}
        rest_client._request = mock.AsyncMock(return_value={"id": "234"})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(return_value=emoji)

        returned = await rest_client.edit_emoji(
            StubModel(123),
            StubModel(456),
            name="rooYay2",
            roles=[StubModel(789), StubModel(987)],
            reason="Because we have got the power",
        )
        assert returned is emoji

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason="Because we have got the power"
        )
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_called_once_with({"id": "234"}, guild_id=123)

    async def test_delete_emoji(self, rest_client):
        expected_route = routes.DELETE_GUILD_EMOJI.compile(guild=123, emoji=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_emoji(StubModel(123), StubModel(456), reason="testing")

        rest_client._request.assert_awaited_once_with(expected_route, reason="testing")

    async def test_fetch_application_emoji(self, rest_client):
        emoji = StubModel(456)
        expected_route = routes.GET_APPLICATION_EMOJI.compile(emoji=456, application=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(return_value=emoji)

        assert await rest_client.fetch_application_emoji(StubModel(123), StubModel(456)) is emoji

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_called_once_with({"id": "456"})

    async def test_fetch_application_emojis(self, rest_client):
        emoji1 = StubModel(456)
        emoji2 = StubModel(789)
        expected_route = routes.GET_APPLICATION_EMOJIS.compile(application=123)
        rest_client._request = mock.AsyncMock(return_value={"items": [{"id": "456"}, {"id": "789"}]})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(side_effect=[emoji1, emoji2])

        assert await rest_client.fetch_application_emojis(StubModel(123)) == [emoji1, emoji2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_known_custom_emoji.call_count == 2
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_create_application_emoji(self, rest_client, file_resource_patch):
        emoji = StubModel(234)
        expected_route = routes.POST_APPLICATION_EMOJIS.compile(application=123)
        expected_json = {"name": "rooYay", "image": "some data"}
        rest_client._request = mock.AsyncMock(return_value={"id": "234"})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(return_value=emoji)

        returned = await rest_client.create_application_emoji(StubModel(123), "rooYay", "rooYay.png")
        assert returned is emoji

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_called_once_with({"id": "234"})

    async def test_edit_application_emoji(self, rest_client):
        emoji = StubModel(234)
        expected_route = routes.PATCH_APPLICATION_EMOJI.compile(application=123, emoji=456)
        expected_json = {"name": "rooYay2"}
        rest_client._request = mock.AsyncMock(return_value={"id": "234"})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(return_value=emoji)

        returned = await rest_client.edit_application_emoji(StubModel(123), StubModel(456), name="rooYay2")
        assert returned is emoji

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_known_custom_emoji.assert_called_once_with({"id": "234"})

    async def test_delete_application_emoji(self, rest_client):
        expected_route = routes.DELETE_APPLICATION_EMOJI.compile(application=123, emoji=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_application_emoji(StubModel(123), StubModel(456))

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_sticker_packs(self, rest_client):
        pack1 = object()
        pack2 = object()
        pack3 = object()
        expected_route = routes.GET_STICKER_PACKS.compile()
        rest_client._request = mock.AsyncMock(
            return_value={"sticker_packs": [{"id": "123"}, {"id": "456"}, {"id": "789"}]}
        )
        rest_client._entity_factory.deserialize_sticker_pack = mock.Mock(side_effect=[pack1, pack2, pack3])

        assert await rest_client.fetch_available_sticker_packs() == [pack1, pack2, pack3]

        rest_client._request.assert_awaited_once_with(expected_route, auth=None)
        rest_client._entity_factory.deserialize_sticker_pack.assert_has_calls(
            [mock.call({"id": "123"}), mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_sticker_when_guild_sticker(self, rest_client):
        expected_route = routes.GET_STICKER.compile(sticker=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "123", "guild_id": "456"})
        rest_client._entity_factory.deserialize_guild_sticker = mock.Mock()

        returned = await rest_client.fetch_sticker(StubModel(123))
        assert returned is rest_client._entity_factory.deserialize_guild_sticker.return_value

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_guild_sticker.assert_called_once_with({"id": "123", "guild_id": "456"})

    async def test_fetch_sticker_when_standard_sticker(self, rest_client):
        expected_route = routes.GET_STICKER.compile(sticker=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_standard_sticker = mock.Mock()

        returned = await rest_client.fetch_sticker(StubModel(123))
        assert returned is rest_client._entity_factory.deserialize_standard_sticker.return_value

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_standard_sticker.assert_called_once_with({"id": "123"})

    async def test_fetch_guild_stickers(self, rest_client):
        sticker1 = object()
        sticker2 = object()
        sticker3 = object()
        expected_route = routes.GET_GUILD_STICKERS.compile(guild=987)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "123"}, {"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_guild_sticker = mock.Mock(side_effect=[sticker1, sticker2, sticker3])

        assert await rest_client.fetch_guild_stickers(StubModel(987)) == [sticker1, sticker2, sticker3]

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_guild_sticker.assert_has_calls(
            [mock.call({"id": "123"}), mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_guild_sticker(self, rest_client):
        expected_route = routes.GET_GUILD_STICKER.compile(guild=456, sticker=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_guild_sticker = mock.Mock()

        returned = await rest_client.fetch_guild_sticker(StubModel(456), StubModel(123))
        assert returned is rest_client._entity_factory.deserialize_guild_sticker.return_value

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_guild_sticker.assert_called_once_with({"id": "123"})

    async def test_create_sticker(self, rest_client):
        rest_client.create_sticker = mock.AsyncMock()
        file = object()

        sticker = await rest_client.create_sticker(
            90210, "NewSticker", "funny", file, description="A sticker", reason="blah blah blah"
        )
        assert sticker is rest_client.create_sticker.return_value

        rest_client.create_sticker.assert_awaited_once_with(
            90210, "NewSticker", "funny", file, description="A sticker", reason="blah blah blah"
        )

    async def test_edit_sticker(self, rest_client):
        expected_route = routes.PATCH_GUILD_STICKER.compile(guild=123, sticker=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_guild_sticker = mock.Mock()

        returned = await rest_client.edit_sticker(
            StubModel(123),
            StubModel(456),
            name="testing_sticker",
            description="blah",
            tag=":cry:",
            reason="i am bored and have too much time in my hands",
        )
        assert returned is rest_client._entity_factory.deserialize_guild_sticker.return_value

        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"name": "testing_sticker", "description": "blah", "tags": ":cry:"},
            reason="i am bored and have too much time in my hands",
        )
        rest_client._entity_factory.deserialize_guild_sticker.assert_called_once_with({"id": "456"})

    async def test_delete_sticker(self, rest_client):
        expected_route = routes.DELETE_GUILD_STICKER.compile(guild=123, sticker=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_sticker(
            StubModel(123), StubModel(456), reason="i am bored and have too much time in my hands"
        )

        rest_client._request.assert_awaited_once_with(
            expected_route, reason="i am bored and have too much time in my hands"
        )

    async def test_fetch_guild(self, rest_client):
        guild = StubModel(1234)
        expected_route = routes.GET_GUILD.compile(guild=123)
        expected_query = {"with_counts": "true"}
        rest_client._request = mock.AsyncMock(return_value={"id": "1234"})
        rest_client._entity_factory.deserialize_rest_guild = mock.Mock(return_value=guild)

        assert await rest_client.fetch_guild(StubModel(123)) is guild

        rest_client._request.assert_awaited_once_with(expected_route, query=expected_query)
        rest_client._entity_factory.deserialize_rest_guild.assert_called_once_with({"id": "1234"})

    async def test_fetch_guild_preview(self, rest_client):
        guild_preview = StubModel(1234)
        expected_route = routes.GET_GUILD_PREVIEW.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "1234"})
        rest_client._entity_factory.deserialize_guild_preview = mock.Mock(return_value=guild_preview)

        assert await rest_client.fetch_guild_preview(StubModel(123)) is guild_preview

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_guild_preview.assert_called_once_with({"id": "1234"})

    async def test_delete_guild(self, rest_client):
        expected_route = routes.DELETE_GUILD.compile(guild=123)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_guild(StubModel(123))

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_edit_guild(self, rest_client, file_resource):
        icon_resource = file_resource("icon data")
        splash_resource = file_resource("splash data")
        banner_resource = file_resource("banner data")
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {
            "name": "hikari",
            "verification_level": 3,
            "default_message_notifications": 1,
            "explicit_content_filter": 1,
            "afk_timeout": 60,
            "preferred_locale": "en-UK",
            "afk_channel_id": "456",
            "owner_id": "789",
            "system_channel_id": "789",
            "rules_channel_id": "987",
            "public_updates_channel_id": "654",
            "icon": "icon data",
            "splash": "splash data",
            "banner": "banner data",
            "features": ["COMMUNITY", "RAID_ALERTS_DISABLED"],
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})

        with mock.patch.object(files, "ensure_resource", side_effect=[icon_resource, splash_resource, banner_resource]):
            result = await rest_client.edit_guild(
                StubModel(123),
                name="hikari",
                verification_level=guilds.GuildVerificationLevel.HIGH,
                default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
                explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.MEMBERS_WITHOUT_ROLES,
                afk_channel=StubModel(456),
                afk_timeout=60,
                icon="icon.png",
                owner=StubModel(789),
                splash="splash.png",
                banner="banner.png",
                system_channel=StubModel(789),
                rules_channel=StubModel(987),
                public_updates_channel=(654),
                preferred_locale="en-UK",
                features=[guilds.GuildFeature.COMMUNITY, guilds.GuildFeature.RAID_ALERTS_DISABLED],
                reason="hikari best",
            )
            assert result is rest_client._entity_factory.deserialize_rest_guild.return_value

        rest_client._entity_factory.deserialize_rest_guild.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="hikari best")

    async def test_edit_guild_when_images_are_None(self, rest_client):
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {
            "name": "hikari",
            "verification_level": 3,
            "default_message_notifications": 1,
            "explicit_content_filter": 1,
            "afk_timeout": 60,
            "preferred_locale": "en-UK",
            "afk_channel_id": "456",
            "owner_id": "789",
            "system_channel_id": "789",
            "rules_channel_id": "987",
            "public_updates_channel_id": "654",
            "icon": None,
            "splash": None,
            "banner": None,
            "features": ["COMMUNITY", "RAID_ALERTS_DISABLED"],
        }
        rest_client._request = mock.AsyncMock(return_value={"ok": "NO"})

        result = await rest_client.edit_guild(
            StubModel(123),
            name="hikari",
            verification_level=guilds.GuildVerificationLevel.HIGH,
            default_message_notifications=guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS,
            explicit_content_filter_level=guilds.GuildExplicitContentFilterLevel.MEMBERS_WITHOUT_ROLES,
            afk_channel=StubModel(456),
            afk_timeout=60,
            icon=None,
            owner=StubModel(789),
            splash=None,
            banner=None,
            system_channel=StubModel(789),
            rules_channel=StubModel(987),
            public_updates_channel=(654),
            preferred_locale="en-UK",
            features=[guilds.GuildFeature.COMMUNITY, guilds.GuildFeature.RAID_ALERTS_DISABLED],
            reason="hikari best",
        )
        assert result is rest_client._entity_factory.deserialize_rest_guild.return_value

        rest_client._entity_factory.deserialize_rest_guild.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="hikari best")

    async def test_edit_guild_without_optionals(self, rest_client):
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {}
        rest_client._request = mock.AsyncMock(return_value={"id": "42"})

        result = await rest_client.edit_guild(StubModel(123))
        assert result is rest_client._entity_factory.deserialize_rest_guild.return_value

        rest_client._entity_factory.deserialize_rest_guild.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)

    async def test_fetch_guild_channels(self, rest_client):
        channel1 = StubModel(456)
        channel2 = StubModel(789)
        expected_route = routes.GET_GUILD_CHANNELS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_channel = mock.Mock(side_effect=[channel1, channel2])

        assert await rest_client.fetch_guild_channels(StubModel(123)) == [channel1, channel2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_channel.call_count == 2
        rest_client._entity_factory.deserialize_channel.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_guild_channels_ignores_unknown_channel_type(self, rest_client):
        channel1 = StubModel(456)
        expected_route = routes.GET_GUILD_CHANNELS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_channel = mock.Mock(
            side_effect=[errors.UnrecognisedEntityError("echelon"), channel1]
        )

        assert await rest_client.fetch_guild_channels(StubModel(123)) == [channel1]

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_channel.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_create_guild_text_channel(self, rest_client: rest.RESTClientImpl):
        guild = StubModel(123)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock()

        returned = await rest_client.create_guild_text_channel(
            guild,
            "general",
            position=1,
            topic="general chat",
            nsfw=False,
            rate_limit_per_user=60,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
            default_auto_archive_duration=123332,
        )
        assert returned is rest_client._entity_factory.deserialize_guild_text_channel.return_value

        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_TEXT,
            position=1,
            topic="general chat",
            nsfw=False,
            rate_limit_per_user=60,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
            default_auto_archive_duration=123332,
        )
        rest_client._entity_factory.deserialize_guild_text_channel.assert_called_once_with(
            rest_client._create_guild_channel.return_value
        )

    async def test_create_guild_news_channel(self, rest_client: rest.RESTClientImpl):
        guild = StubModel(123)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock()

        returned = await rest_client.create_guild_news_channel(
            guild,
            "general",
            position=1,
            topic="general news",
            nsfw=False,
            rate_limit_per_user=60,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
            default_auto_archive_duration=5445234,
        )
        assert returned is rest_client._entity_factory.deserialize_guild_news_channel.return_value

        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_NEWS,
            position=1,
            topic="general news",
            nsfw=False,
            rate_limit_per_user=60,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
            default_auto_archive_duration=5445234,
        )
        rest_client._entity_factory.deserialize_guild_news_channel.assert_called_once_with(
            rest_client._create_guild_channel.return_value
        )

    async def test_create_guild_forum_channel(self, rest_client: rest.RESTClientImpl):
        guild = StubModel(123)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        tag1 = StubModel(1203)
        tag2 = StubModel(1204)
        rest_client._create_guild_channel = mock.AsyncMock()

        returned = await rest_client.create_guild_forum_channel(
            guild,
            "help-center",
            position=1,
            topic="get help!",
            nsfw=False,
            rate_limit_per_user=60,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
            default_auto_archive_duration=5445234,
            default_thread_rate_limit_per_user=40,
            default_forum_layout=channels.ForumLayoutType.LIST_VIEW,
            default_sort_order=channels.ForumSortOrderType.LATEST_ACTIVITY,
            available_tags=[tag1, tag2],
            default_reaction_emoji="some reaction",
        )
        assert returned is rest_client._entity_factory.deserialize_guild_forum_channel.return_value

        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "help-center",
            channels.ChannelType.GUILD_FORUM,
            position=1,
            topic="get help!",
            nsfw=False,
            rate_limit_per_user=60,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
            default_auto_archive_duration=5445234,
            default_thread_rate_limit_per_user=40,
            default_forum_layout=channels.ForumLayoutType.LIST_VIEW,
            default_sort_order=channels.ForumSortOrderType.LATEST_ACTIVITY,
            available_tags=[tag1, tag2],
            default_reaction_emoji="some reaction",
        )
        rest_client._entity_factory.deserialize_guild_forum_channel.assert_called_once_with(
            rest_client._create_guild_channel.return_value
        )

    async def test_create_guild_voice_channel(self, rest_client: rest.RESTClientImpl):
        guild = StubModel(123)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock()

        returned = await rest_client.create_guild_voice_channel(
            guild,
            "general",
            position=1,
            user_limit=60,
            bitrate=64,
            video_quality_mode=channels.VideoQualityMode.FULL,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            region="ok boomer",
            reason="because we need one",
        )
        assert returned is rest_client._entity_factory.deserialize_guild_voice_channel.return_value

        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_VOICE,
            position=1,
            user_limit=60,
            bitrate=64,
            video_quality_mode=channels.VideoQualityMode.FULL,
            permission_overwrites=[overwrite1, overwrite2],
            region="ok boomer",
            category=category_channel,
            reason="because we need one",
        )
        rest_client._entity_factory.deserialize_guild_voice_channel.assert_called_once_with(
            rest_client._create_guild_channel.return_value
        )

    async def test_create_guild_stage_channel(self, rest_client: rest.RESTClientImpl):
        guild = StubModel(123)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock()

        returned = await rest_client.create_guild_stage_channel(
            guild,
            "general",
            position=1,
            user_limit=60,
            bitrate=64,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            region="Doge Moon",
            reason="When doge == 1$",
        )
        assert returned is rest_client._entity_factory.deserialize_guild_stage_channel.return_value

        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_STAGE,
            position=1,
            user_limit=60,
            bitrate=64,
            permission_overwrites=[overwrite1, overwrite2],
            region="Doge Moon",
            category=category_channel,
            reason="When doge == 1$",
        )
        rest_client._entity_factory.deserialize_guild_stage_channel.assert_called_once_with(
            rest_client._create_guild_channel.return_value
        )

    async def test_create_guild_category(self, rest_client: rest.RESTClientImpl):
        guild = StubModel(123)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock()

        returned = await rest_client.create_guild_category(
            guild, "general", position=1, permission_overwrites=[overwrite1, overwrite2], reason="because we need one"
        )
        assert returned is rest_client._entity_factory.deserialize_guild_category.return_value

        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_CATEGORY,
            position=1,
            permission_overwrites=[overwrite1, overwrite2],
            reason="because we need one",
        )
        rest_client._entity_factory.deserialize_guild_category.assert_called_once_with(
            rest_client._create_guild_channel.return_value
        )

    @pytest.mark.parametrize(
        ("emoji", "expected_emoji_id", "expected_emoji_name"), [(123, 123, None), ("emoji", None, "emoji")]
    )
    @pytest.mark.parametrize("default_auto_archive_duration", [12322, (datetime.timedelta(minutes=12322)), 12322.0])
    async def test__create_guild_channel(
        self, rest_client, default_auto_archive_duration, emoji, expected_emoji_id, expected_emoji_name
    ):
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        tag1 = StubModel(321)
        tag2 = StubModel(123)
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
            "parent_id": "321",
            "permission_overwrites": [{"id": "987"}, {"id": "654"}],
            "default_auto_archive_duration": 12322,
            "default_thread_rate_limit_per_user": 40,
            "default_forum_layout": 1,
            "default_sort_order": 0,
            "default_reaction_emoji": {"emoji_id": expected_emoji_id, "emoji_name": expected_emoji_name},
            "available_tags": [{"id": "321"}, {"id": "123"}],
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.serialize_permission_overwrite = mock.Mock(
            side_effect=[{"id": "987"}, {"id": "654"}]
        )
        rest_client._entity_factory.serialize_forum_tag = mock.Mock(side_effect=[{"id": "321"}, {"id": "123"}])

        returned = await rest_client._create_guild_channel(
            StubModel(123),
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
            category=StubModel(321),
            reason="we have got the power",
            default_auto_archive_duration=default_auto_archive_duration,
            default_thread_rate_limit_per_user=40,
            default_forum_layout=channels.ForumLayoutType.LIST_VIEW,
            default_sort_order=channels.ForumSortOrderType.LATEST_ACTIVITY,
            available_tags=[tag1, tag2],
            default_reaction_emoji=emoji,
        )
        assert returned is rest_client._request.return_value

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason="we have got the power"
        )
        assert rest_client._entity_factory.serialize_permission_overwrite.call_count == 2
        rest_client._entity_factory.serialize_permission_overwrite.assert_has_calls(
            [mock.call(overwrite1), mock.call(overwrite2)]
        )
        assert rest_client._entity_factory.serialize_forum_tag.call_count == 2
        rest_client._entity_factory.serialize_forum_tag.assert_has_calls([mock.call(tag1), mock.call(tag2)])

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(12322, 42069), (datetime.timedelta(minutes=12322), datetime.timedelta(seconds=42069)), (12322.0, 42069.4)],
    )
    async def test_create_message_thread(
        self,
        rest_client: rest.RESTClientImpl,
        auto_archive_duration: typing.Union[int, datetime.datetime, float],
        rate_limit_per_user: typing.Union[int, datetime.datetime, float],
    ):
        expected_route = routes.POST_MESSAGE_THREADS.compile(channel=123432, message=595959)
        expected_payload = {"name": "Sass alert!!!", "auto_archive_duration": 12322, "rate_limit_per_user": 42069}
        rest_client._request = mock.AsyncMock(return_value={"id": "54123123", "name": "dlksksldalksad"})
        rest_client._entity_factory.deserialize_guild_thread.return_value = mock.Mock(channels.GuildPublicThread)

        result = await rest_client.create_message_thread(
            StubModel(123432),
            StubModel(595959),
            "Sass alert!!!",
            auto_archive_duration=auto_archive_duration,
            rate_limit_per_user=rate_limit_per_user,
            reason="because we need one",
        )

        assert result is rest_client._entity_factory.deserialize_guild_thread.return_value
        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_payload, reason="because we need one"
        )
        rest_client._entity_factory.deserialize_guild_thread.assert_called_once_with(rest_client._request.return_value)

    async def test_create_message_thread_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_MESSAGE_THREADS.compile(channel=123432, message=595959)
        expected_payload = {"name": "Sass alert!!!", "auto_archive_duration": 1440}
        rest_client._request = mock.AsyncMock(return_value={"id": "54123123", "name": "dlksksldalksad"})
        rest_client._entity_factory.deserialize_guild_thread.return_value = mock.Mock(channels.GuildNewsThread)

        result = await rest_client.create_message_thread(StubModel(123432), StubModel(595959), "Sass alert!!!")

        assert result is rest_client._entity_factory.deserialize_guild_thread.return_value
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_guild_thread.assert_called_once_with(rest_client._request.return_value)

    async def test_create_message_thread_with_all_undefined(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_MESSAGE_THREADS.compile(channel=123432, message=595959)
        expected_payload = {"name": "Sass alert!!!"}
        rest_client._request = mock.AsyncMock(return_value={"id": "54123123", "name": "dlksksldalksad"})
        rest_client._entity_factory.deserialize_guild_thread.return_value = mock.Mock(channels.GuildNewsThread)

        result = await rest_client.create_message_thread(
            StubModel(123432), StubModel(595959), "Sass alert!!!", auto_archive_duration=undefined.UNDEFINED
        )

        assert result is rest_client._entity_factory.deserialize_guild_thread.return_value
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_guild_thread.assert_called_once_with(rest_client._request.return_value)

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(54123, 101), (datetime.timedelta(minutes=54123), datetime.timedelta(seconds=101)), (54123.0, 101.4)],
    )
    async def test_create_thread(
        self,
        rest_client: rest.RESTClientImpl,
        auto_archive_duration: typing.Union[int, datetime.datetime, float],
        rate_limit_per_user: typing.Union[int, datetime.datetime, float],
    ):
        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=321123)
        expected_payload = {
            "name": "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            "auto_archive_duration": 54123,
            "type": 10,
            "invitable": True,
            "rate_limit_per_user": 101,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "54123123", "name": "dlksksldalksad"})

        result = await rest_client.create_thread(
            StubModel(321123),
            channels.ChannelType.GUILD_NEWS_THREAD,
            "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            auto_archive_duration=auto_archive_duration,
            invitable=True,
            rate_limit_per_user=rate_limit_per_user,
            reason="think of the catgirls!!! >:3",
        )

        assert result is rest_client._entity_factory.deserialize_guild_thread.return_value
        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_payload, reason="think of the catgirls!!! >:3"
        )
        rest_client._entity_factory.deserialize_guild_thread.assert_called_once_with(rest_client._request.return_value)

    async def test_create_thread_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=321123)
        expected_payload = {
            "name": "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            "auto_archive_duration": 1440,
            "type": 12,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "54123123", "name": "dlksksldalksad"})

        result = await rest_client.create_thread(
            StubModel(321123),
            channels.ChannelType.GUILD_PRIVATE_THREAD,
            "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
        )

        assert result is rest_client._entity_factory.deserialize_guild_thread.return_value
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_guild_thread.assert_called_once_with(rest_client._request.return_value)

    async def test_create_thread_with_all_undefined(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=321123)
        expected_payload = {
            "name": "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            "type": 12,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "54123123", "name": "dlksksldalksad"})

        result = await rest_client.create_thread(
            StubModel(321123),
            channels.ChannelType.GUILD_PRIVATE_THREAD,
            "Something something send help, they're keeping the catgirls locked up at <REDACTED>",
            auto_archive_duration=undefined.UNDEFINED,
        )

        assert result is rest_client._entity_factory.deserialize_guild_thread.return_value
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_payload, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_guild_thread.assert_called_once_with(rest_client._request.return_value)

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(54123, 101), (datetime.timedelta(minutes=54123), datetime.timedelta(seconds=101)), (54123.0, 101.4)],
    )
    async def test_create_forum_post_when_no_form(
        self,
        rest_client: rest.RESTClientImpl,
        auto_archive_duration: typing.Union[int, datetime.datetime, float],
        rate_limit_per_user: typing.Union[int, datetime.datetime, float],
    ):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = data_binding.JSONObjectBuilder()

        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=321123)
        expected_payload = {
            "name": "Post with secret content!",
            "auto_archive_duration": 54123,
            "rate_limit_per_user": 101,
            "applied_tags": ["12220", "12201"],
            "message": mock_body,
        }
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"some": "message"})

        result = await rest_client.create_forum_post(
            StubModel(321123),
            "Post with secret content!",
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            sticker=132543,
            stickers=[654234, 123321],
            tts=True,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=54123,
            auto_archive_duration=auto_archive_duration,
            rate_limit_per_user=rate_limit_per_user,
            tags=[12220, 12201],
            reason="Secrets!!",
        )

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            sticker=132543,
            stickers=[654234, 123321],
            tts=True,
            mentions_everyone=False,
            mentions_reply=undefined.UNDEFINED,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=54123,
        )

        assert result is rest_client._entity_factory.deserialize_guild_public_thread.return_value
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_payload, reason="Secrets!!")
        rest_client._entity_factory.deserialize_guild_public_thread.assert_called_once_with(
            rest_client._request.return_value
        )

    @pytest.mark.parametrize(
        ("auto_archive_duration", "rate_limit_per_user"),
        [(54123, 101), (datetime.timedelta(minutes=54123), datetime.timedelta(seconds=101)), (54123.0, 101.4)],
    )
    async def test_create_forum_post_when_form(
        self,
        rest_client: rest.RESTClientImpl,
        auto_archive_duration: typing.Union[int, datetime.datetime, float],
        rate_limit_per_user: typing.Union[int, datetime.datetime, float],
    ):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = {"mock": "message body"}
        mock_form = mock.Mock()

        expected_route = routes.POST_CHANNEL_THREADS.compile(channel=321123)
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"some": "message"})

        result = await rest_client.create_forum_post(
            StubModel(321123),
            "Post with secret content!",
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            sticker=314542,
            stickers=[56234, 123312],
            tts=True,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
            flags=54123,
            auto_archive_duration=auto_archive_duration,
            rate_limit_per_user=rate_limit_per_user,
            tags=[12220, 12201],
            reason="Secrets!!",
        )

        rest_client._build_message_payload.assert_called_once_with(
            content="new content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
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

        assert result is rest_client._entity_factory.deserialize_guild_public_thread.return_value
        rest_client._request.assert_awaited_once_with(expected_route, form_builder=mock_form, reason="Secrets!!")
        rest_client._entity_factory.deserialize_guild_public_thread.assert_called_once_with(
            rest_client._request.return_value
        )

    async def test_join_thread(self, rest_client: rest.RESTClientImpl):
        rest_client._request = mock.AsyncMock()

        await rest_client.join_thread(StubModel(54123123))

        rest_client._request.assert_awaited_once_with(routes.PUT_MY_THREAD_MEMBER.compile(channel=54123123))

    async def test_add_thread_member(self, rest_client: rest.RESTClientImpl):
        rest_client._request = mock.AsyncMock()

        # why is 8 afraid of 6 and 7?
        await rest_client.add_thread_member(StubModel(789), StubModel(666))

        rest_client._request.assert_awaited_once_with(routes.PUT_THREAD_MEMBER.compile(channel=789, user=666))

    async def test_leave_thread(self, rest_client: rest.RESTClientImpl):
        rest_client._request = mock.AsyncMock()

        await rest_client.leave_thread(StubModel(54123123))

        rest_client._request.assert_awaited_once_with(routes.DELETE_MY_THREAD_MEMBER.compile(channel=54123123))

    async def test_remove_thread_member(self, rest_client: rest.RESTClientImpl):
        rest_client._request = mock.AsyncMock()

        await rest_client.remove_thread_member(StubModel(669), StubModel(421))

        rest_client._request.assert_awaited_once_with(routes.DELETE_THREAD_MEMBER.compile(channel=669, user=421))

    async def test_fetch_thread_member(self, rest_client: rest.RESTClientImpl):
        rest_client._request = mock.AsyncMock(return_value={"id": "9239292", "user_id": "949494"})

        result = await rest_client.fetch_thread_member(StubModel(55445454), StubModel(45454454))

        assert result is rest_client.entity_factory.deserialize_thread_member.return_value
        rest_client.entity_factory.deserialize_thread_member.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(routes.GET_THREAD_MEMBER.compile(channel=55445454, user=45454454))

    async def test_fetch_thread_members(self, rest_client: rest.RESTClientImpl):
        mock_payload_1 = mock.Mock()
        mock_payload_2 = mock.Mock()
        mock_payload_3 = mock.Mock()
        mock_member_1 = mock.Mock()
        mock_member_2 = mock.Mock()
        mock_member_3 = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value=[mock_payload_1, mock_payload_2, mock_payload_3])
        rest_client._entity_factory.deserialize_thread_member = mock.Mock(
            side_effect=[mock_member_1, mock_member_2, mock_member_3]
        )

        result = await rest_client.fetch_thread_members(StubModel(110101010101))

        assert result == [mock_member_1, mock_member_2, mock_member_3]
        rest_client._request.assert_awaited_once_with(routes.GET_THREAD_MEMBERS.compile(channel=110101010101))
        rest_client._entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_payload_1), mock.call(mock_payload_2), mock.call(mock_payload_3)]
        )

    async def test_fetch_active_threads(self, rest_client: rest.RESTClientImpl): ...

    async def test_reposition_channels(self, rest_client):
        expected_route = routes.PATCH_GUILD_CHANNELS.compile(guild=123)
        expected_json = [{"id": "456", "position": 1}, {"id": "789", "position": 2}]
        rest_client._request = mock.AsyncMock()

        await rest_client.reposition_channels(StubModel(123), {1: StubModel(456), 2: StubModel(789)})

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)

    async def test_fetch_member(self, rest_client):
        member = StubModel(789)
        expected_route = routes.GET_GUILD_MEMBER.compile(guild=123, user=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})
        rest_client._entity_factory.deserialize_member = mock.Mock(return_value=member)

        assert await rest_client.fetch_member(StubModel(123), StubModel(456)) == member

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_member.assert_called_once_with({"id": "789"}, guild_id=123)

    async def test_fetch_my_member(self, rest_client):
        expected_route = routes.GET_MY_GUILD_MEMBER.compile(guild=45123)
        rest_client._request = mock.AsyncMock(return_value={"id": "595995"})

        result = await rest_client.fetch_my_member(StubModel(45123))

        assert result is rest_client._entity_factory.deserialize_member.return_value
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=45123
        )

    async def test_search_members(self, rest_client):
        member = StubModel(645234123)
        expected_route = routes.GET_GUILD_MEMBERS_SEARCH.compile(guild=645234123)
        expected_query = {"query": "a name", "limit": "1000"}
        rest_client._request = mock.AsyncMock(return_value=[{"id": "764435"}])
        rest_client._entity_factory.deserialize_member = mock.Mock(return_value=member)

        assert await rest_client.search_members(StubModel(645234123), "a name") == [member]

        rest_client._entity_factory.deserialize_member.assert_called_once_with({"id": "764435"}, guild_id=645234123)
        rest_client._request.assert_awaited_once_with(expected_route, query=expected_query)

    async def test_edit_member(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        expected_json = {
            "nick": "test",
            "roles": ["654", "321"],
            "mute": True,
            "deaf": False,
            "channel_id": "987",
            "communication_disabled_until": "2021-10-18T07:18:11.554023+00:00",
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})
        mock_timestamp = datetime.datetime(2021, 10, 18, 7, 18, 11, 554023, tzinfo=datetime.timezone.utc)

        result = await rest_client.edit_member(
            StubModel(123),
            StubModel(456),
            nickname="test",
            roles=[StubModel(654), StubModel(321)],
            mute=True,
            deaf=False,
            voice_channel=StubModel(987),
            communication_disabled_until=mock_timestamp,
            reason="because i can",
        )
        assert result is rest_client._entity_factory.deserialize_member.return_value

        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=123
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_member_when_voice_channel_is_None(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        expected_json = {"nick": "test", "roles": ["654", "321"], "mute": True, "deaf": False, "channel_id": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        result = await rest_client.edit_member(
            StubModel(123),
            StubModel(456),
            nickname="test",
            roles=[StubModel(654), StubModel(321)],
            mute=True,
            deaf=False,
            voice_channel=None,
            reason="because i can",
        )
        assert result is rest_client._entity_factory.deserialize_member.return_value

        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=123
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_member_when_communication_disabled_until_is_None(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        expected_json = {"communication_disabled_until": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        result = await rest_client.edit_member(
            StubModel(123), StubModel(456), communication_disabled_until=None, reason="because i can"
        )
        assert result is rest_client._entity_factory.deserialize_member.return_value

        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=123
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_member_without_optionals(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        result = await rest_client.edit_member(StubModel(123), StubModel(456))
        assert result is rest_client._entity_factory.deserialize_member.return_value

        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=123
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)

    async def test_my_edit_member(self, rest_client):
        expected_route = routes.PATCH_MY_GUILD_MEMBER.compile(guild=123)
        expected_json = {"nick": "test"}
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        result = await rest_client.edit_my_member(StubModel(123), nickname="test", reason="because i can")
        assert result is rest_client._entity_factory.deserialize_member.return_value

        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=123
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_my_member_without_optionals(self, rest_client):
        expected_route = routes.PATCH_MY_GUILD_MEMBER.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        result = await rest_client.edit_my_member(StubModel(123))
        assert result is rest_client._entity_factory.deserialize_member.return_value

        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=123
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)

    async def test_add_role_to_member(self, rest_client):
        expected_route = routes.PUT_GUILD_MEMBER_ROLE.compile(guild=123, user=456, role=789)
        rest_client._request = mock.AsyncMock()

        await rest_client.add_role_to_member(StubModel(123), StubModel(456), StubModel(789), reason="because i can")

        rest_client._request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_remove_role_from_member(self, rest_client):
        expected_route = routes.DELETE_GUILD_MEMBER_ROLE.compile(guild=123, user=456, role=789)
        rest_client._request = mock.AsyncMock()

        await rest_client.remove_role_from_member(
            StubModel(123), StubModel(456), StubModel(789), reason="because i can"
        )

        rest_client._request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_kick_user(self, rest_client):
        expected_route = routes.DELETE_GUILD_MEMBER.compile(guild=123, user=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.kick_user(StubModel(123), StubModel(456), reason="because i can")

        rest_client._request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_ban_user(self, rest_client):
        expected_route = routes.PUT_GUILD_BAN.compile(guild=123, user=456)
        expected_json = {"delete_message_seconds": 604800}
        rest_client._request = mock.AsyncMock()

        await rest_client.ban_user(
            StubModel(123), StubModel(456), delete_message_seconds=604800, reason="because i can"
        )

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_unban_user(self, rest_client):
        expected_route = routes.DELETE_GUILD_BAN.compile(guild=123, user=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.unban_user(StubModel(123), StubModel(456), reason="because i can")

        rest_client._request.assert_awaited_once_with(expected_route, reason="because i can")

    async def test_fetch_ban(self, rest_client):
        ban = StubModel(789)
        expected_route = routes.GET_GUILD_BAN.compile(guild=123, user=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})
        rest_client._entity_factory.deserialize_guild_member_ban = mock.Mock(return_value=ban)

        assert await rest_client.fetch_ban(StubModel(123), StubModel(456)) == ban

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_guild_member_ban.assert_called_once_with({"id": "789"})

    async def test_fetch_role(self, rest_client):
        role = StubModel(456)
        expected_route = routes.GET_GUILD_ROLE.compile(guild=123, role=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_role = mock.Mock(return_value=role)

        assert await rest_client.fetch_role(StubModel(123), StubModel(456)) is role

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_fetch_roles(self, rest_client):
        role1 = StubModel(456)
        role2 = StubModel(789)
        expected_route = routes.GET_GUILD_ROLES.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_role = mock.Mock(side_effect=[role1, role2])

        assert await rest_client.fetch_roles(StubModel(123)) == [role1, role2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_role.call_count == 2
        rest_client._entity_factory.deserialize_role.assert_has_calls(
            [mock.call({"id": "456"}, guild_id=123), mock.call({"id": "789"}, guild_id=123)]
        )

    async def test_create_role(self, rest_client, file_resource_patch):
        expected_route = routes.POST_GUILD_ROLES.compile(guild=123)
        expected_json = {
            "name": "admin",
            "permissions": 8,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "icon": "some data",
            "mentionable": False,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})

        returned = await rest_client.create_role(
            StubModel(123),
            name="admin",
            permissions=permissions.Permissions.ADMINISTRATOR,
            color=colors.Color.from_int(12345),
            hoist=True,
            icon="icon.png",
            mentionable=False,
            reason="roles are cool",
        )
        assert returned is rest_client._entity_factory.deserialize_role.return_value

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="roles are cool")
        rest_client._entity_factory.deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_create_role_when_permissions_undefined(self, rest_client):
        role = StubModel(456)
        expected_route = routes.POST_GUILD_ROLES.compile(guild=123)
        expected_json = {
            "name": "admin",
            "permissions": 0,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "mentionable": False,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_role = mock.Mock(return_value=role)

        returned = await rest_client.create_role(
            StubModel(123),
            name="admin",
            color=colors.Color.from_int(12345),
            hoist=True,
            mentionable=False,
            reason="roles are cool",
        )
        assert returned is role

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="roles are cool")
        rest_client._entity_factory.deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_create_role_when_color_and_colour_specified(self, rest_client):
        with pytest.raises(TypeError, match=r"Can not specify 'color' and 'colour' together."):
            await rest_client.create_role(
                StubModel(123), color=colors.Color.from_int(12345), colour=colors.Color.from_int(12345)
            )

    async def test_create_role_when_icon_unicode_emoji_specified(self, rest_client):
        with pytest.raises(TypeError, match=r"Can not specify 'icon' and 'unicode_emoji' together."):
            await rest_client.create_role(StubModel(123), icon="icon.png", unicode_emoji="\N{OK HAND SIGN}")

    async def test_reposition_roles(self, rest_client):
        expected_route = routes.PATCH_GUILD_ROLES.compile(guild=123)
        expected_json = [{"id": "456", "position": 1}, {"id": "789", "position": 2}]
        rest_client._request = mock.AsyncMock()

        await rest_client.reposition_roles(StubModel(123), {1: StubModel(456), 2: StubModel(789)})

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)

    async def test_edit_role(self, rest_client, file_resource_patch):
        expected_route = routes.PATCH_GUILD_ROLE.compile(guild=123, role=789)
        expected_json = {
            "name": "admin",
            "permissions": 8,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "icon": "some data",
            "mentionable": False,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})

        returned = await rest_client.edit_role(
            StubModel(123),
            StubModel(789),
            name="admin",
            permissions=permissions.Permissions.ADMINISTRATOR,
            color=colors.Color.from_int(12345),
            hoist=True,
            icon="icon.png",
            mentionable=False,
            reason="roles are cool",
        )
        assert returned is rest_client._entity_factory.deserialize_role.return_value

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="roles are cool")
        rest_client._entity_factory.deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_edit_role_when_color_and_colour_specified(self, rest_client):
        with pytest.raises(TypeError, match=r"Can not specify 'color' and 'colour' together."):
            await rest_client.edit_role(
                StubModel(123), StubModel(456), color=colors.Color.from_int(12345), colour=colors.Color.from_int(12345)
            )

    async def test_edit_role_when_icon_and_unicode_emoji_specified(self, rest_client):
        with pytest.raises(TypeError, match=r"Can not specify 'icon' and 'unicode_emoji' together."):
            await rest_client.edit_role(
                StubModel(123), StubModel(456), icon="icon.png", unicode_emoji="\N{OK HAND SIGN}"
            )

    async def test_delete_role(self, rest_client):
        expected_route = routes.DELETE_GUILD_ROLE.compile(guild=123, role=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_role(StubModel(123), StubModel(456))

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_estimate_guild_prune_count(self, rest_client):
        expected_route = routes.GET_GUILD_PRUNE.compile(guild=123)
        expected_query = {"days": "1"}
        rest_client._request = mock.AsyncMock(return_value={"pruned": "69"})

        assert await rest_client.estimate_guild_prune_count(StubModel(123), days=1) == 69
        rest_client._request.assert_awaited_once_with(expected_route, query=expected_query)

    async def test_estimate_guild_prune_count_with_include_roles(self, rest_client):
        expected_route = routes.GET_GUILD_PRUNE.compile(guild=123)
        expected_query = {"days": "1", "include_roles": "456,678"}
        rest_client._request = mock.AsyncMock(return_value={"pruned": "69"})

        returned = await rest_client.estimate_guild_prune_count(
            StubModel(123), days=1, include_roles=[StubModel(456), StubModel(678)]
        )
        assert returned == 69

        rest_client._request.assert_awaited_once_with(expected_route, query=expected_query)

    async def test_begin_guild_prune(self, rest_client):
        expected_route = routes.POST_GUILD_PRUNE.compile(guild=123)
        expected_json = {"days": 1, "compute_prune_count": True, "include_roles": ["456", "678"]}
        rest_client._request = mock.AsyncMock(return_value={"pruned": "69"})

        returned = await rest_client.begin_guild_prune(
            StubModel(123),
            days=1,
            compute_prune_count=True,
            include_roles=[StubModel(456), StubModel(678)],
            reason="cause inactive people bad",
        )
        assert returned == 69

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason="cause inactive people bad"
        )

    async def test_fetch_guild_voice_regions(self, rest_client):
        voice_region1 = StubModel(456)
        voice_region2 = StubModel(789)
        expected_route = routes.GET_GUILD_VOICE_REGIONS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_voice_region = mock.Mock(side_effect=[voice_region1, voice_region2])

        assert await rest_client.fetch_guild_voice_regions(StubModel(123)) == [voice_region1, voice_region2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_voice_region.call_count == 2
        rest_client._entity_factory.deserialize_voice_region.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_guild_invites(self, rest_client):
        invite1 = StubModel(456)
        invite2 = StubModel(789)
        expected_route = routes.GET_GUILD_INVITES.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_invite_with_metadata = mock.Mock(side_effect=[invite1, invite2])

        assert await rest_client.fetch_guild_invites(StubModel(123)) == [invite1, invite2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_invite_with_metadata.call_count == 2
        rest_client._entity_factory.deserialize_invite_with_metadata.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

    async def test_fetch_integrations(self, rest_client):
        integration1 = StubModel(456)
        integration2 = StubModel(789)
        expected_route = routes.GET_GUILD_INTEGRATIONS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_integration = mock.Mock(side_effect=[integration1, integration2])

        assert await rest_client.fetch_integrations(StubModel(123)) == [integration1, integration2]

        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_integration.call_count == 2
        rest_client._entity_factory.deserialize_integration.assert_has_calls(
            [mock.call({"id": "456"}, guild_id=123), mock.call({"id": "789"}, guild_id=123)]
        )

    async def test_fetch_widget(self, rest_client):
        widget = StubModel(789)
        expected_route = routes.GET_GUILD_WIDGET.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})
        rest_client._entity_factory.deserialize_guild_widget = mock.Mock(return_value=widget)

        assert await rest_client.fetch_widget(StubModel(123)) == widget

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_guild_widget.assert_called_once_with({"id": "789"})

    async def test_edit_widget(self, rest_client):
        widget = StubModel(456)
        expected_route = routes.PATCH_GUILD_WIDGET.compile(guild=123)
        expected_json = {"enabled": True, "channel": "456"}
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_guild_widget = mock.Mock(return_value=widget)

        returned = await rest_client.edit_widget(
            StubModel(123), channel=StubModel(456), enabled=True, reason="this should have been enabled"
        )
        assert returned is widget

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason="this should have been enabled"
        )
        rest_client._entity_factory.deserialize_guild_widget.assert_called_once_with({"id": "456"})

    async def test_edit_widget_when_channel_is_None(self, rest_client):
        widget = StubModel(456)
        expected_route = routes.PATCH_GUILD_WIDGET.compile(guild=123)
        expected_json = {"enabled": True, "channel": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_guild_widget = mock.Mock(return_value=widget)

        returned = await rest_client.edit_widget(
            StubModel(123), channel=None, enabled=True, reason="this should have been enabled"
        )
        assert returned is widget

        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason="this should have been enabled"
        )
        rest_client._entity_factory.deserialize_guild_widget.assert_called_once_with({"id": "456"})

    async def test_edit_widget_without_optionals(self, rest_client):
        widget = StubModel(456)
        expected_route = routes.PATCH_GUILD_WIDGET.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_guild_widget = mock.Mock(return_value=widget)

        assert await rest_client.edit_widget(StubModel(123)) == widget

        rest_client._request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_guild_widget.assert_called_once_with({"id": "456"})

    async def test_fetch_welcome_screen(self, rest_client):
        rest_client._request = mock.AsyncMock(return_value={"haha": "funny"})
        expected_route = routes.GET_GUILD_WELCOME_SCREEN.compile(guild=52341231)

        result = await rest_client.fetch_welcome_screen(StubModel(52341231))
        assert result is rest_client._entity_factory.deserialize_welcome_screen.return_value

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_welcome_screen.assert_called_once_with(
            rest_client._request.return_value
        )

    async def test_edit_welcome_screen_with_optional_kwargs(self, rest_client):
        mock_channel = object()
        rest_client._request = mock.AsyncMock(return_value={"go": "home", "you're": "drunk"})
        expected_route = routes.PATCH_GUILD_WELCOME_SCREEN.compile(guild=54123564)

        result = await rest_client.edit_welcome_screen(
            StubModel(54123564), description="blam blam", enabled=True, channels=[mock_channel]
        )
        assert result is rest_client._entity_factory.deserialize_welcome_screen.return_value

        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "description": "blam blam",
                "enabled": True,
                "welcome_channels": [rest_client._entity_factory.serialize_welcome_channel.return_value],
            },
        )
        rest_client._entity_factory.deserialize_welcome_screen.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._entity_factory.serialize_welcome_channel.assert_called_once_with(mock_channel)

    async def test_edit_welcome_screen_with_null_kwargs(self, rest_client):
        rest_client._request = mock.AsyncMock(return_value={"go": "go", "power": "rangers"})
        expected_route = routes.PATCH_GUILD_WELCOME_SCREEN.compile(guild=54123564)

        result = await rest_client.edit_welcome_screen(StubModel(54123564), description=None, channels=None)
        assert result is rest_client._entity_factory.deserialize_welcome_screen.return_value

        rest_client._request.assert_awaited_once_with(
            expected_route, json={"description": None, "welcome_channels": None}
        )
        rest_client._entity_factory.deserialize_welcome_screen.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._entity_factory.serialize_welcome_channel.assert_not_called()

    async def test_edit_welcome_screen_without_optional_kwargs(self, rest_client):
        rest_client._request = mock.AsyncMock(return_value={"screen": "NBO"})
        expected_route = routes.PATCH_GUILD_WELCOME_SCREEN.compile(guild=54123564)

        result = await rest_client.edit_welcome_screen(StubModel(54123564))
        assert result is rest_client._entity_factory.deserialize_welcome_screen.return_value

        rest_client._request.assert_awaited_once_with(expected_route, json={})
        rest_client._entity_factory.deserialize_welcome_screen.assert_called_once_with(
            rest_client._request.return_value
        )

    async def test_fetch_vanity_url(self, rest_client):
        vanity_url = StubModel(789)
        expected_route = routes.GET_GUILD_VANITY_URL.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})
        rest_client._entity_factory.deserialize_vanity_url = mock.Mock(return_value=vanity_url)

        assert await rest_client.fetch_vanity_url(StubModel(123)) == vanity_url

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_vanity_url.assert_called_once_with({"id": "789"})

    async def test_fetch_template(self, rest_client):
        expected_route = routes.GET_TEMPLATE.compile(template="kodfskoijsfikoiok")
        rest_client._request = mock.AsyncMock(return_value={"code": "KSDAOKSDKIO"})

        result = await rest_client.fetch_template("kodfskoijsfikoiok")
        assert result is rest_client._entity_factory.deserialize_template.return_value

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "KSDAOKSDKIO"})

    async def test_fetch_guild_templates(self, rest_client):
        expected_route = routes.GET_GUILD_TEMPLATES.compile(guild=43123123)
        rest_client._request = mock.AsyncMock(return_value=[{"code": "jirefu98ai90w"}])

        result = await rest_client.fetch_guild_templates(StubModel(43123123))
        assert result == [rest_client._entity_factory.deserialize_template.return_value]

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "jirefu98ai90w"})

    async def test_sync_guild_template(self, rest_client):
        expected_route = routes.PUT_GUILD_TEMPLATE.compile(guild=431231, template="oeroeoeoeoeo")
        rest_client._request = mock.AsyncMock(return_value={"code": "ldsaosdokskdoa"})

        result = await rest_client.sync_guild_template(StubModel(431231), template="oeroeoeoeoeo")
        assert result is rest_client._entity_factory.deserialize_template.return_value

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "ldsaosdokskdoa"})

    async def test_create_guild_from_template_without_icon(self, rest_client):
        expected_route = routes.POST_TEMPLATE.compile(template="odkkdkdkd")
        rest_client._request = mock.AsyncMock(return_value={"id": "543123123"})

        result = await rest_client.create_guild_from_template("odkkdkdkd", "ok a name")
        assert result is rest_client._entity_factory.deserialize_rest_guild.return_value

        rest_client._request.assert_awaited_once_with(expected_route, json={"name": "ok a name"})
        rest_client._entity_factory.deserialize_rest_guild.assert_called_once_with({"id": "543123123"})

    async def test_create_guild_from_template_with_icon(self, rest_client, file_resource):
        expected_route = routes.POST_TEMPLATE.compile(template="odkkdkdkd")
        rest_client._request = mock.AsyncMock(return_value={"id": "543123123"})
        icon_resource = file_resource("icon data")

        with mock.patch.object(files, "ensure_resource", return_value=icon_resource):
            result = await rest_client.create_guild_from_template("odkkdkdkd", "ok a name", icon="icon.png")
            assert result is rest_client._entity_factory.deserialize_rest_guild.return_value

        rest_client._request.assert_awaited_once_with(expected_route, json={"name": "ok a name", "icon": "icon data"})
        rest_client._entity_factory.deserialize_rest_guild.assert_called_once_with({"id": "543123123"})

    async def test_create_template_without_description(self, rest_client):
        expected_routes = routes.POST_GUILD_TEMPLATES.compile(guild=1235432)
        rest_client._request = mock.AsyncMock(return_value={"code": "94949sdfkds"})

        result = await rest_client.create_template(StubModel(1235432), "OKOKOK")
        assert result is rest_client._entity_factory.deserialize_template.return_value

        rest_client._request.assert_awaited_once_with(expected_routes, json={"name": "OKOKOK"})
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "94949sdfkds"})

    async def test_create_template_with_description(self, rest_client):
        expected_route = routes.POST_GUILD_TEMPLATES.compile(guild=4123123)
        rest_client._request = mock.AsyncMock(return_value={"code": "76345345"})

        result = await rest_client.create_template(StubModel(4123123), "33", description="43123123")
        assert result is rest_client._entity_factory.deserialize_template.return_value

        rest_client._request.assert_awaited_once_with(expected_route, json={"name": "33", "description": "43123123"})
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "76345345"})

    async def test_edit_template_without_optionals(self, rest_client):
        expected_route = routes.PATCH_GUILD_TEMPLATE.compile(guild=3412312, template="oeodsosda")
        rest_client._request = mock.AsyncMock(return_value={"code": "9493293ikiwopop"})

        result = await rest_client.edit_template(StubModel(3412312), "oeodsosda")
        assert result is rest_client._entity_factory.deserialize_template.return_value

        rest_client._request.assert_awaited_once_with(expected_route, json={})
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "9493293ikiwopop"})

    async def test_edit_template_with_optionals(self, rest_client):
        expected_route = routes.PATCH_GUILD_TEMPLATE.compile(guild=34123122, template="oeodsosda2")
        rest_client._request = mock.AsyncMock(return_value={"code": "9493293ikiwopop"})

        result = await rest_client.edit_template(
            StubModel(34123122), "oeodsosda2", name="new name", description="i'm lazy"
        )
        assert result is rest_client._entity_factory.deserialize_template.return_value

        rest_client._request.assert_awaited_once_with(
            expected_route, json={"name": "new name", "description": "i'm lazy"}
        )
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "9493293ikiwopop"})

    async def test_delete_template(self, rest_client):
        expected_route = routes.DELETE_GUILD_TEMPLATE.compile(guild=3123123, template="eoiesri9er99")
        rest_client._request = mock.AsyncMock(return_value={"code": "oeoekfgkdkf"})

        result = await rest_client.delete_template(StubModel(3123123), "eoiesri9er99")
        assert result is rest_client._entity_factory.deserialize_template.return_value

        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_template.assert_called_once_with({"code": "oeoekfgkdkf"})

    async def test_fetch_application_command_with_guild(self, rest_client):
        expected_route = routes.GET_APPLICATION_GUILD_COMMAND.compile(application=32154, guild=5312312, command=42123)
        rest_client._request = mock.AsyncMock(return_value={"id": "424242"})

        result = await rest_client.fetch_application_command(StubModel(32154), StubModel(42123), StubModel(5312312))

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=5312312
        )

    async def test_fetch_application_command_without_guild(self, rest_client):
        expected_route = routes.GET_APPLICATION_COMMAND.compile(application=32154, command=42123)
        rest_client._request = mock.AsyncMock(return_value={"id": "424242"})

        result = await rest_client.fetch_application_command(StubModel(32154), StubModel(42123))

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=None
        )

    async def test_fetch_application_commands_with_guild(self, rest_client):
        expected_route = routes.GET_APPLICATION_GUILD_COMMANDS.compile(application=54123, guild=7623423)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "34512312"}])

        result = await rest_client.fetch_application_commands(StubModel(54123), StubModel(7623423))

        assert result == [rest_client._entity_factory.deserialize_command.return_value]
        rest_client._request.assert_awaited_once_with(expected_route, query={"with_localizations": "true"})
        rest_client._entity_factory.deserialize_command.assert_called_once_with({"id": "34512312"}, guild_id=7623423)

    async def test_fetch_application_commands_without_guild(self, rest_client):
        expected_route = routes.GET_APPLICATION_COMMANDS.compile(application=54123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "34512312"}])

        result = await rest_client.fetch_application_commands(StubModel(54123))

        assert result == [rest_client._entity_factory.deserialize_command.return_value]
        rest_client._request.assert_awaited_once_with(expected_route, query={"with_localizations": "true"})
        rest_client._entity_factory.deserialize_command.assert_called_once_with({"id": "34512312"}, guild_id=None)

    async def test_fetch_application_commands_ignores_unknown_command_types(self, rest_client):
        mock_command = mock.Mock()
        expected_route = routes.GET_APPLICATION_GUILD_COMMANDS.compile(application=54123, guild=432234)
        rest_client._entity_factory.deserialize_command.side_effect = [
            errors.UnrecognisedEntityError("eep"),
            mock_command,
        ]
        rest_client._request = mock.AsyncMock(return_value=[{"id": "541234"}, {"id": "553234"}])

        result = await rest_client.fetch_application_commands(StubModel(54123), StubModel(432234))

        assert result == [mock_command]
        rest_client._request.assert_awaited_once_with(expected_route, query={"with_localizations": "true"})
        rest_client._entity_factory.deserialize_command.assert_has_calls(
            [mock.call({"id": "541234"}, guild_id=432234), mock.call({"id": "553234"}, guild_id=432234)]
        )

    async def test__create_application_command_with_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_APPLICATION_GUILD_COMMAND.compile(application=4332123, guild=653452134)
        rest_client._request = mock.AsyncMock(return_value={"id": "29393939"})
        mock_option = object()

        result = await rest_client._create_application_command(
            application=StubModel(4332123),
            type=100,
            name="okokok",
            description="not ok anymore",
            guild=StubModel(653452134),
            options=[mock_option],
            default_member_permissions=permissions.Permissions.ADMINISTRATOR,
            dm_enabled=False,
            nsfw=True,
            integration_types=[applications.ApplicationIntegrationType.GUILD_INSTALL],
            contexts=[
                applications.ApplicationInstallationContextType.GUILD,
                applications.ApplicationInstallationContextType.BOT_DM,
            ],
        )

        assert result is rest_client._request.return_value
        rest_client._entity_factory.serialize_command_option.assert_called_once_with(mock_option)
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "type": 100,
                "name": "okokok",
                "description": "not ok anymore",
                "options": [rest_client._entity_factory.serialize_command_option.return_value],
                "default_member_permissions": 8,
                "dm_permission": False,
                "nsfw": True,
                "integration_types": [0],
                "contexts": [0, 1],
            },
        )

    async def test_create_application_command_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_APPLICATION_COMMAND.compile(application=4332123)
        rest_client._request = mock.AsyncMock(return_value={"id": "29393939"})

        result = await rest_client._create_application_command(
            application=StubModel(4332123), type=100, name="okokok", description="not ok anymore"
        )

        assert result is rest_client._request.return_value
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"type": 100, "name": "okokok", "description": "not ok anymore"}
        )

    async def test__create_application_command_standardizes_default_member_permissions(
        self, rest_client: rest.RESTClientImpl
    ):
        expected_route = routes.POST_APPLICATION_COMMAND.compile(application=4332123)
        rest_client._request = mock.AsyncMock(return_value={"id": "29393939"})

        result = await rest_client._create_application_command(
            application=StubModel(4332123),
            type=100,
            name="okokok",
            description="not ok anymore",
            default_member_permissions=permissions.Permissions.NONE,
        )

        assert result is rest_client._request.return_value
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"type": 100, "name": "okokok", "description": "not ok anymore", "default_member_permissions": None},
        )

    async def test_create_slash_command(self, rest_client: rest.RESTClientImpl):
        rest_client._create_application_command = mock.AsyncMock()
        mock_options = object()
        mock_application = StubModel(4332123)
        mock_guild = StubModel(123123123)

        result = await rest_client.create_slash_command(
            mock_application,
            "okokok",
            "not ok anymore",
            guild=mock_guild,
            options=mock_options,
            name_localizations={locales.Locale.TR: "hhh"},
            description_localizations={locales.Locale.TR: "jello"},
            default_member_permissions=permissions.Permissions.ADMINISTRATOR,
            dm_enabled=False,
            nsfw=True,
            integration_types=[applications.ApplicationIntegrationType.GUILD_INSTALL],
            contexts=[
                applications.ApplicationInstallationContextType.GUILD,
                applications.ApplicationInstallationContextType.BOT_DM,
            ],
        )

        assert result is rest_client._entity_factory.deserialize_slash_command.return_value
        rest_client._entity_factory.deserialize_slash_command.assert_called_once_with(
            rest_client._create_application_command.return_value, guild_id=123123123
        )
        rest_client._create_application_command.assert_awaited_once_with(
            application=mock_application,
            type=commands.CommandType.SLASH,
            name="okokok",
            description="not ok anymore",
            guild=mock_guild,
            options=mock_options,
            name_localizations={"tr": "hhh"},
            description_localizations={"tr": "jello"},
            default_member_permissions=permissions.Permissions.ADMINISTRATOR,
            dm_enabled=False,
            nsfw=True,
            integration_types=[applications.ApplicationIntegrationType.GUILD_INSTALL],
            contexts=[
                applications.ApplicationInstallationContextType.GUILD,
                applications.ApplicationInstallationContextType.BOT_DM,
            ],
        )

    async def test_create_context_menu_command(self, rest_client: rest.RESTClientImpl):
        rest_client._create_application_command = mock.AsyncMock()
        mock_application = StubModel(4332123)
        mock_guild = StubModel(123123123)

        result = await rest_client.create_context_menu_command(
            mock_application,
            commands.CommandType.USER,
            "okokok",
            guild=mock_guild,
            default_member_permissions=permissions.Permissions.ADMINISTRATOR,
            dm_enabled=False,
            nsfw=True,
            name_localizations={locales.Locale.TR: "hhh"},
            integration_types=[applications.ApplicationIntegrationType.GUILD_INSTALL],
            contexts=[
                applications.ApplicationInstallationContextType.GUILD,
                applications.ApplicationInstallationContextType.BOT_DM,
            ],
        )

        assert result is rest_client._entity_factory.deserialize_context_menu_command.return_value
        rest_client._entity_factory.deserialize_context_menu_command.assert_called_once_with(
            rest_client._create_application_command.return_value, guild_id=123123123
        )
        rest_client._create_application_command.assert_awaited_once_with(
            application=mock_application,
            type=commands.CommandType.USER,
            name="okokok",
            guild=mock_guild,
            default_member_permissions=permissions.Permissions.ADMINISTRATOR,
            dm_enabled=False,
            nsfw=True,
            name_localizations={"tr": "hhh"},
            integration_types=[applications.ApplicationIntegrationType.GUILD_INSTALL],
            contexts=[
                applications.ApplicationInstallationContextType.GUILD,
                applications.ApplicationInstallationContextType.BOT_DM,
            ],
        )

    async def test_set_application_commands_with_guild(self, rest_client):
        expected_route = routes.PUT_APPLICATION_GUILD_COMMANDS.compile(application=4321231, guild=6543234)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "9459329932"}])
        mock_command_builder = mock.Mock()

        result = await rest_client.set_application_commands(
            StubModel(4321231), [mock_command_builder], StubModel(6543234)
        )

        assert result == [rest_client._entity_factory.deserialize_command.return_value]
        rest_client._entity_factory.deserialize_command.assert_called_once_with({"id": "9459329932"}, guild_id=6543234)
        rest_client._request.assert_awaited_once_with(expected_route, json=[mock_command_builder.build.return_value])
        mock_command_builder.build.assert_called_once_with(rest_client._entity_factory)

    async def test_set_application_commands_without_guild(self, rest_client):
        expected_route = routes.PUT_APPLICATION_COMMANDS.compile(application=4321231)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "9459329932"}])
        mock_command_builder = mock.Mock()

        result = await rest_client.set_application_commands(StubModel(4321231), [mock_command_builder])

        assert result == [rest_client._entity_factory.deserialize_command.return_value]
        rest_client._entity_factory.deserialize_command.assert_called_once_with({"id": "9459329932"}, guild_id=None)
        rest_client._request.assert_awaited_once_with(expected_route, json=[mock_command_builder.build.return_value])
        mock_command_builder.build.assert_called_once_with(rest_client._entity_factory)

    async def test_set_application_commands_without_guild_handles_unknown_command_types(self, rest_client):
        mock_command = mock.Mock()
        expected_route = routes.PUT_APPLICATION_GUILD_COMMANDS.compile(application=532123123, guild=453123)
        rest_client._entity_factory.deserialize_command.side_effect = [
            errors.UnrecognisedEntityError("meow"),
            mock_command,
        ]
        rest_client._request = mock.AsyncMock(return_value=[{"id": "435765"}, {"id": "4949493933"}])
        mock_command_builder = mock.Mock()

        result = await rest_client.set_application_commands(
            StubModel(532123123), [mock_command_builder], StubModel(453123)
        )

        assert result == [mock_command]
        rest_client._entity_factory.deserialize_command.assert_has_calls(
            [mock.call({"id": "435765"}, guild_id=453123), mock.call({"id": "4949493933"}, guild_id=453123)]
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=[mock_command_builder.build.return_value])
        mock_command_builder.build.assert_called_once_with(rest_client._entity_factory)

    async def test_edit_application_command_with_optionals(self, rest_client):
        expected_route = routes.PATCH_APPLICATION_GUILD_COMMAND.compile(
            application=1235432, guild=54123, command=3451231
        )
        rest_client._request = mock.AsyncMock(return_value={"id": "94594994"})
        mock_option = object()

        result = await rest_client.edit_application_command(
            StubModel(1235432),
            StubModel(3451231),
            StubModel(54123),
            name="ok sis",
            description="cancelled",
            options=[mock_option],
            default_member_permissions=permissions.Permissions.BAN_MEMBERS,
            dm_enabled=True,
            contexts=[applications.ApplicationInstallationContextType.GUILD],
        )

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=54123
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "name": "ok sis",
                "description": "cancelled",
                "options": [rest_client._entity_factory.serialize_command_option.return_value],
                "default_member_permissions": 4,
                "dm_permission": True,
                "contexts": [0],
            },
        )
        rest_client._entity_factory.serialize_command_option.assert_called_once_with(mock_option)

    async def test_edit_application_command_without_optionals(self, rest_client):
        expected_route = routes.PATCH_APPLICATION_COMMAND.compile(application=1235432, command=3451231)
        rest_client._request = mock.AsyncMock(return_value={"id": "94594994"})

        result = await rest_client.edit_application_command(StubModel(1235432), StubModel(3451231))

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=None
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={})

    async def test_edit_application_command_standardizes_default_member_permissions(
        self, rest_client: rest.RESTClientImpl
    ):
        expected_route = routes.PATCH_APPLICATION_COMMAND.compile(application=1235432, command=3451231)
        rest_client._request = mock.AsyncMock(return_value={"id": "94594994"})

        result = await rest_client.edit_application_command(
            StubModel(1235432), StubModel(3451231), default_member_permissions=permissions.Permissions.NONE
        )

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=None
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={"default_member_permissions": None})

    async def test_delete_application_command_with_guild(self, rest_client):
        expected_route = routes.DELETE_APPLICATION_GUILD_COMMAND.compile(
            application=312312, command=65234323, guild=5421312
        )
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_application_command(StubModel(312312), StubModel(65234323), StubModel(5421312))

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_application_command_without_guild(self, rest_client):
        expected_route = routes.DELETE_APPLICATION_COMMAND.compile(application=312312, command=65234323)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_application_command(StubModel(312312), StubModel(65234323))

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_application_guild_commands_permissions(self, rest_client):
        expected_route = routes.GET_APPLICATION_GUILD_COMMANDS_PERMISSIONS.compile(application=321431, guild=54123)
        mock_command_payload = object()
        rest_client._request = mock.AsyncMock(return_value=[mock_command_payload])

        result = await rest_client.fetch_application_guild_commands_permissions(321431, 54123)

        assert result == [rest_client._entity_factory.deserialize_guild_command_permissions.return_value]
        rest_client._entity_factory.deserialize_guild_command_permissions.assert_called_once_with(mock_command_payload)
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_application_command_permissions(self, rest_client):
        expected_route = routes.GET_APPLICATION_COMMAND_PERMISSIONS.compile(
            application=543421, guild=123321321, command=543123
        )
        mock_command_payload = {"id": "9393939393"}
        rest_client._request = mock.AsyncMock(return_value=mock_command_payload)

        result = await rest_client.fetch_application_command_permissions(543421, 123321321, 543123)

        assert result is rest_client._entity_factory.deserialize_guild_command_permissions.return_value
        rest_client._entity_factory.deserialize_guild_command_permissions.assert_called_once_with(mock_command_payload)
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_set_application_command_permissions(self, rest_client):
        route = routes.PUT_APPLICATION_COMMAND_PERMISSIONS.compile(application=2321, guild=431, command=666666)
        mock_permission = object()
        mock_command_payload = {"id": "29292929"}
        rest_client._request = mock.AsyncMock(return_value=mock_command_payload)

        result = await rest_client.set_application_command_permissions(2321, 431, 666666, [mock_permission])

        assert result is rest_client._entity_factory.deserialize_guild_command_permissions.return_value
        rest_client._entity_factory.deserialize_guild_command_permissions.assert_called_once_with(mock_command_payload)
        rest_client._request.assert_awaited_once_with(
            route, json={"permissions": [rest_client._entity_factory.serialize_command_permission.return_value]}
        )

    async def test_fetch_interaction_response(self, rest_client):
        expected_route = routes.GET_INTERACTION_RESPONSE.compile(webhook=1235432, token="go homo or go gnomo")
        rest_client._request = mock.AsyncMock(return_value={"id": "94949494949"})

        result = await rest_client.fetch_interaction_response(StubModel(1235432), "go homo or go gnomo")

        assert result is rest_client._entity_factory.deserialize_message.return_value
        rest_client._entity_factory.deserialize_message.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route, auth=None)

    async def test_create_interaction_response_when_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=432, token="some token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock()

        await rest_client.create_interaction_response(
            StubModel(432),
            "some token",
            1,
            "some content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )

        rest_client._build_message_payload.assert_called_once_with(
            content="some content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )
        mock_form.add_field.assert_called_once_with(
            "payload_json", b'{"type":1,"data":{"testing":"ensure_in_test"}}', content_type="application/json"
        )
        rest_client._request.assert_awaited_once_with(expected_route, form_builder=mock_form, auth=None)

    async def test_create_interaction_response_when_no_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=432, token="some token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock()

        await rest_client.create_interaction_response(
            StubModel(432),
            "some token",
            1,
            "some content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )

        rest_client._build_message_payload.assert_called_once_with(
            content="some content",
            attachment=attachment_obj,
            attachments=[attachment_obj2],
            component=component_obj,
            components=[component_obj2],
            embed=embed_obj,
            embeds=[embed_obj2],
            tts=True,
            flags=120,
            mentions_everyone=False,
            user_mentions=[9876],
            role_mentions=[1234],
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"type": 1, "data": {"testing": "ensure_in_test"}}, auth=None
        )

    async def test_edit_interaction_response_when_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_form = mock.Mock()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_INTERACTION_RESPONSE.compile(webhook=432, token="some token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, mock_form))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_interaction_response(
            StubModel(432),
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
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
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
        rest_client._request.assert_awaited_once_with(expected_route, form_builder=mock_form, auth=None)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_edit_interaction_response_when_no_form(self, rest_client):
        attachment_obj = object()
        attachment_obj2 = object()
        component_obj = object()
        component_obj2 = object()
        embed_obj = object()
        embed_obj2 = object()
        mock_body = data_binding.JSONObjectBuilder()
        mock_body.put("testing", "ensure_in_test")
        expected_route = routes.PATCH_INTERACTION_RESPONSE.compile(webhook=432, token="some token")
        rest_client._build_message_payload = mock.Mock(return_value=(mock_body, None))
        rest_client._request = mock.AsyncMock(return_value={"message_id": 123})

        returned = await rest_client.edit_interaction_response(
            StubModel(432),
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
        assert returned is rest_client._entity_factory.deserialize_message.return_value

        rest_client._build_message_payload.assert_called_once_with(
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
        rest_client._request.assert_awaited_once_with(expected_route, json={"testing": "ensure_in_test"}, auth=None)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"message_id": 123})

    async def test_delete_interaction_response(self, rest_client):
        expected_route = routes.DELETE_INTERACTION_RESPONSE.compile(webhook=1235431, token="go homo now")
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_interaction_response(StubModel(1235431), "go homo now")

        rest_client._request.assert_awaited_once_with(expected_route, auth=None)

    async def test_create_autocomplete_response(self, rest_client):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=1235431, token="snek")
        rest_client._request = mock.AsyncMock()

        choices = [
            special_endpoints.AutocompleteChoiceBuilder(name="c", value="d"),
            special_endpoints.AutocompleteChoiceBuilder(name="eee", value="fff"),
        ]
        await rest_client.create_autocomplete_response(StubModel(1235431), "snek", choices)

        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"type": 8, "data": {"choices": [{"name": "c", "value": "d"}, {"name": "eee", "value": "fff"}]}},
            auth=None,
        )

    async def test_create_autocomplete_response_for_deprecated_command_choices(self, rest_client):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=1235431, token="snek")
        rest_client._request = mock.AsyncMock()

        choices = [commands.CommandChoice(name="a", value="b"), commands.CommandChoice(name="foo", value="bar")]
        await rest_client.create_autocomplete_response(StubModel(1235431), "snek", choices)

        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"type": 8, "data": {"choices": [{"name": "a", "value": "b"}, {"name": "foo", "value": "bar"}]}},
            auth=None,
        )

    async def test_create_modal_response(self, rest_client):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=1235431, token="snek")
        rest_client._request = mock.AsyncMock()
        component = mock.Mock()

        await rest_client.create_modal_response(
            StubModel(1235431), "snek", title="title", custom_id="idd", component=component
        )

        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "type": 9,
                "data": {"title": "title", "custom_id": "idd", "components": [component.build.return_value]},
            },
            auth=None,
        )

    async def test_create_modal_response_with_plural_args(self, rest_client):
        expected_route = routes.POST_INTERACTION_RESPONSE.compile(interaction=1235431, token="snek")
        rest_client._request = mock.AsyncMock()
        component = mock.Mock()

        await rest_client.create_modal_response(
            StubModel(1235431), "snek", title="title", custom_id="idd", components=[component]
        )

        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "type": 9,
                "data": {"title": "title", "custom_id": "idd", "components": [component.build.return_value]},
            },
            auth=None,
        )

    async def test_create_modal_response_when_both_component_and_components_passed(self, rest_client):
        with pytest.raises(ValueError, match="Must specify exactly only one of 'component' or 'components'"):
            await rest_client.create_modal_response(
                StubModel(1235431), "snek", title="title", custom_id="idd", component="not none", components=[]
            )

    async def test_fetch_scheduled_event(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.GET_GUILD_SCHEDULED_EVENT.compile(guild=453123, scheduled_event=222332323)
        rest_client._request = mock.AsyncMock(return_value={"id": "4949494949"})

        result = await rest_client.fetch_scheduled_event(StubModel(453123), StubModel(222332323))

        assert result is rest_client._entity_factory.deserialize_scheduled_event.return_value
        rest_client._entity_factory.deserialize_scheduled_event.assert_called_once_with({"id": "4949494949"})
        rest_client._request.assert_awaited_once_with(expected_route, query={"with_user_count": "true"})

    async def test_fetch_scheduled_events(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.GET_GUILD_SCHEDULED_EVENTS.compile(guild=65234123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "494920234", "type": "1"}])

        result = await rest_client.fetch_scheduled_events(StubModel(65234123))

        assert result == [rest_client._entity_factory.deserialize_scheduled_event.return_value]
        rest_client._entity_factory.deserialize_scheduled_event.assert_called_once_with(
            {"id": "494920234", "type": "1"}
        )
        rest_client._request.assert_awaited_once_with(expected_route, query={"with_user_count": "true"})

    async def test_fetch_scheduled_events_handles_unrecognised_events(self, rest_client: rest.RESTClientImpl):
        mock_event = mock.Mock()
        rest_client._entity_factory.deserialize_scheduled_event.side_effect = [
            errors.UnrecognisedEntityError("evil laugh"),
            mock_event,
        ]
        expected_route = routes.GET_GUILD_SCHEDULED_EVENTS.compile(guild=65234123)
        rest_client._request = mock.AsyncMock(
            return_value=[{"id": "432234", "type": "1"}, {"id": "4939394", "type": "494949"}]
        )

        result = await rest_client.fetch_scheduled_events(StubModel(65234123))

        assert result == [mock_event]
        rest_client._entity_factory.deserialize_scheduled_event.assert_has_calls(
            [mock.call({"id": "432234", "type": "1"}), mock.call({"id": "4939394", "type": "494949"})]
        )
        rest_client._request.assert_awaited_once_with(expected_route, query={"with_user_count": "true"})

    async def test_create_stage_event(self, rest_client: rest.RESTClientImpl, file_resource_patch):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=123321)
        rest_client._request = mock.AsyncMock(return_value={"id": "494949", "name": "MEOsdasdWWWWW"})

        result = await rest_client.create_stage_event(
            StubModel(123321),
            StubModel(7654345),
            "boob man",
            datetime.datetime(2001, 1, 1, 17, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            description="o",
            end_time=datetime.datetime(2002, 2, 2, 17, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            image="tksksk.txt",
            privacy_level=654134,
            reason="bye bye",
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_stage_event.return_value
        rest_client._entity_factory.deserialize_scheduled_stage_event.assert_called_once_with(
            {"id": "494949", "name": "MEOsdasdWWWWW"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "channel_id": "7654345",
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

    async def test_create_stage_event_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=234432234)
        rest_client._request = mock.AsyncMock(return_value={"id": "494949", "name": "MEOWWWWW"})

        result = await rest_client.create_stage_event(
            StubModel(234432234),
            StubModel(654234432),
            "boob man",
            datetime.datetime(2021, 3, 11, 17, 42, 41, 891222, tzinfo=datetime.timezone.utc),
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_stage_event.return_value
        rest_client._entity_factory.deserialize_scheduled_stage_event.assert_called_once_with(
            {"id": "494949", "name": "MEOWWWWW"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "channel_id": "654234432",
                "name": "boob man",
                "entity_type": scheduled_events.ScheduledEventType.STAGE_INSTANCE,
                "privacy_level": scheduled_events.EventPrivacyLevel.GUILD_ONLY,
                "scheduled_start_time": "2021-03-11T17:42:41.891222+00:00",
            },
            reason=undefined.UNDEFINED,
        )

    async def test_create_voice_event(self, rest_client: rest.RESTClientImpl, file_resource_patch):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=76234123)
        rest_client._request = mock.AsyncMock(return_value={"id": "494942342439", "name": "MEOW"})

        result = await rest_client.create_voice_event(
            StubModel(76234123),
            StubModel(65243123),
            "boom man",
            datetime.datetime(2021, 3, 9, 13, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            description="hhhhh",
            end_time=datetime.datetime(2069, 3, 9, 13, 1, 41, 891222, tzinfo=datetime.timezone.utc),
            image="meow.txt",
            privacy_level=6523123,
            reason="it was the {insert political part here}",
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_voice_event.return_value
        rest_client._entity_factory.deserialize_scheduled_voice_event.assert_called_once_with(
            {"id": "494942342439", "name": "MEOW"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "channel_id": "65243123",
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

    async def test_create_voice_event_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=76234123)
        rest_client._request = mock.AsyncMock(return_value={"id": "123321123", "name": "MEOW"})

        result = await rest_client.create_voice_event(
            StubModel(76234123),
            StubModel(65243123),
            "boom man",
            datetime.datetime(2021, 3, 9, 13, 42, 41, 891222, tzinfo=datetime.timezone.utc),
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_voice_event.return_value
        rest_client._entity_factory.deserialize_scheduled_voice_event.assert_called_once_with(
            {"id": "123321123", "name": "MEOW"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "channel_id": "65243123",
                "name": "boom man",
                "entity_type": scheduled_events.ScheduledEventType.VOICE,
                "privacy_level": scheduled_events.EventPrivacyLevel.GUILD_ONLY,
                "scheduled_start_time": "2021-03-09T13:42:41.891222+00:00",
            },
            reason=undefined.UNDEFINED,
        )

    async def test_create_external_event(self, rest_client: rest.RESTClientImpl, file_resource_patch):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=34232412)
        rest_client._request = mock.AsyncMock(return_value={"id": "494949", "name": "MerwwerEOW"})

        result = await rest_client.create_external_event(
            StubModel(34232412),
            "hi",
            "Outside",
            datetime.datetime(2021, 3, 6, 2, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 5, 6, 16, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            description="This is a description",
            image="icon.png",
            privacy_level=6454,
            reason="chairman meow",
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_external_event.return_value
        rest_client._entity_factory.deserialize_scheduled_external_event.assert_called_once_with(
            {"id": "494949", "name": "MerwwerEOW"}
        )
        rest_client._request.assert_awaited_once_with(
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

    async def test_create_external_event_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.POST_GUILD_SCHEDULED_EVENT.compile(guild=34232412)
        rest_client._request = mock.AsyncMock(return_value={"id": "494923443249", "name": "MEOW"})

        result = await rest_client.create_external_event(
            StubModel(34232412),
            "hi",
            "Outside",
            datetime.datetime(2021, 3, 6, 2, 42, 41, 891222, tzinfo=datetime.timezone.utc),
            datetime.datetime(2023, 5, 6, 16, 42, 41, 891222, tzinfo=datetime.timezone.utc),
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_external_event.return_value
        rest_client._entity_factory.deserialize_scheduled_external_event.assert_called_once_with(
            {"id": "494923443249", "name": "MEOW"}
        )
        rest_client._request.assert_awaited_once_with(
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

    async def test_edit_scheduled_event(self, rest_client: rest.RESTClientImpl, file_resource_patch):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=345543, scheduled_event=123321123)
        rest_client._request = mock.AsyncMock(return_value={"id": "494949", "name": "MEO43345W"})

        result = await rest_client.edit_scheduled_event(
            StubModel(345543),
            StubModel(123321123),
            channel=StubModel(45423423),
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

        assert result is rest_client._entity_factory.deserialize_scheduled_event.return_value
        rest_client._entity_factory.deserialize_scheduled_event.assert_called_once_with(
            {"id": "494949", "name": "MEO43345W"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "channel_id": "45423423",
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

    async def test_edit_scheduled_event_with_null_fields(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=345543, scheduled_event=123321123)
        rest_client._request = mock.AsyncMock(return_value={"id": "494949", "name": "ME222222OW"})

        result = await rest_client.edit_scheduled_event(
            StubModel(345543), StubModel(123321123), channel=None, description=None, end_time=None
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_event.return_value
        rest_client._entity_factory.deserialize_scheduled_event.assert_called_once_with(
            {"id": "494949", "name": "ME222222OW"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"channel_id": None, "description": None, "scheduled_end_time": None},
            reason=undefined.UNDEFINED,
        )

    async def test_edit_scheduled_event_without_optionals(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=345543, scheduled_event=123321123)
        rest_client._request = mock.AsyncMock(return_value={"id": "494123321949", "name": "MEOW"})

        result = await rest_client.edit_scheduled_event(StubModel(345543), StubModel(123321123))

        assert result is rest_client._entity_factory.deserialize_scheduled_event.return_value
        rest_client._entity_factory.deserialize_scheduled_event.assert_called_once_with(
            {"id": "494123321949", "name": "MEOW"}
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)

    async def test_edit_scheduled_event_when_changing_to_external(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=345543, scheduled_event=123321123)
        rest_client._request = mock.AsyncMock(return_value={"id": "49342344949", "name": "MEOW"})

        result = await rest_client.edit_scheduled_event(
            StubModel(345543),
            StubModel(123321123),
            entity_type=scheduled_events.ScheduledEventType.EXTERNAL,
            channel=StubModel(5461231),
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_event.return_value
        rest_client._entity_factory.deserialize_scheduled_event.assert_called_once_with(
            {"id": "49342344949", "name": "MEOW"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"channel_id": "5461231", "entity_type": scheduled_events.ScheduledEventType.EXTERNAL},
            reason=undefined.UNDEFINED,
        )

    async def test_edit_scheduled_event_when_changing_to_external_and_channel_id_not_explicitly_passed(
        self, rest_client: rest.RESTClientImpl
    ):
        expected_route = routes.PATCH_GUILD_SCHEDULED_EVENT.compile(guild=345543, scheduled_event=123321123)
        rest_client._request = mock.AsyncMock(return_value={"id": "494949", "name": "MEOW"})

        result = await rest_client.edit_scheduled_event(
            StubModel(345543), StubModel(123321123), entity_type=scheduled_events.ScheduledEventType.EXTERNAL
        )

        assert result is rest_client._entity_factory.deserialize_scheduled_event.return_value
        rest_client._entity_factory.deserialize_scheduled_event.assert_called_once_with(
            {"id": "494949", "name": "MEOW"}
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={"channel_id": None, "entity_type": scheduled_events.ScheduledEventType.EXTERNAL},
            reason=undefined.UNDEFINED,
        )

    async def test_delete_scheduled_event(self, rest_client: rest.RESTClientImpl):
        expected_route = routes.DELETE_GUILD_SCHEDULED_EVENT.compile(guild=54531123, scheduled_event=123321123321)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_scheduled_event(StubModel(54531123), StubModel(123321123321))

        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_stage_instance(self, rest_client):
        expected_route = routes.GET_STAGE_INSTANCE.compile(channel=123)
        mock_payload = {
            "id": "8406",
            "guild_id": "19703",
            "channel_id": "123",
            "topic": "ur mom",
            "privacy_level": 1,
            "discoverable_disabled": False,
        }
        rest_client._request = mock.AsyncMock(return_value=mock_payload)

        result = await rest_client.fetch_stage_instance(channel=StubModel(123))

        assert result is rest_client._entity_factory.deserialize_stage_instance.return_value
        rest_client._request.assert_called_once_with(expected_route)
        rest_client._entity_factory.deserialize_stage_instance.assert_called_once_with(mock_payload)

    async def test_create_stage_instance(self, rest_client):
        expected_route = routes.POST_STAGE_INSTANCE.compile()
        expected_json = {"channel_id": "7334", "topic": "ur mom", "guild_scheduled_event_id": "3361203239"}
        mock_payload = {
            "id": "8406",
            "guild_id": "19703",
            "channel_id": "7334",
            "topic": "ur mom",
            "privacy_level": 2,
            "guild_scheduled_event_id": "3361203239",
            "discoverable_disabled": False,
        }
        rest_client._request = mock.AsyncMock(return_value=mock_payload)

        result = await rest_client.create_stage_instance(
            channel=StubModel(7334), topic="ur mom", scheduled_event_id=StubModel(3361203239)
        )

        assert result is rest_client._entity_factory.deserialize_stage_instance.return_value
        rest_client._request.assert_called_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_stage_instance.assert_called_once_with(mock_payload)

    async def test_edit_stage_instance(self, rest_client):
        expected_route = routes.PATCH_STAGE_INSTANCE.compile(channel=7334)
        expected_json = {"topic": "ur mom", "privacy_level": 2}
        mock_payload = {
            "id": "8406",
            "guild_id": "19703",
            "channel_id": "7334",
            "topic": "ur mom",
            "privacy_level": 2,
            "discoverable_disabled": False,
        }
        rest_client._request = mock.AsyncMock(return_value=mock_payload)

        result = await rest_client.edit_stage_instance(
            channel=StubModel(7334), topic="ur mom", privacy_level=stage_instances.StageInstancePrivacyLevel.GUILD_ONLY
        )

        assert result is rest_client._entity_factory.deserialize_stage_instance.return_value
        rest_client._request.assert_called_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_stage_instance.assert_called_once_with(mock_payload)

    async def test_delete_stage_instance(self, rest_client):
        expected_route = routes.DELETE_STAGE_INSTANCE.compile(channel=7334)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_stage_instance(channel=StubModel(7334))

        rest_client._request.assert_called_once_with(expected_route)
