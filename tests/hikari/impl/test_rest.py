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
import asyncio
import contextlib
import datetime
import http

import mock
import pytest

from hikari import applications
from hikari import audit_logs
from hikari import channels
from hikari import colors
from hikari import config
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import guilds
from hikari import invites
from hikari import permissions
from hikari import snowflakes
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.api import rest as rest_api
from hikari.impl import buckets
from hikari.impl import entity_factory
from hikari.impl import rate_limits
from hikari.impl import rest
from hikari.impl import special_endpoints
from hikari.internal import data_binding
from hikari.internal import net
from hikari.internal import routes
from hikari.internal import time
from tests.hikari import hikari_test_helpers

#################
# _RESTProvider #
#################


class TestRestProvider:
    @pytest.fixture()
    def rest_client(self):
        class StubRestClient:
            http_settings = object()
            proxy_settings = object()

        return StubRestClient()

    @pytest.fixture()
    def executor(self):
        return mock.Mock()

    @pytest.fixture()
    def entity_factory(self):
        return mock.Mock()

    @pytest.fixture()
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


@pytest.mark.asyncio()
class TestClientCredentialsStrategy:
    @pytest.fixture()
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

    async def test_acquire_on_new_instance(self, mock_token):
        mock_rest = mock.Mock(authorize_client_credentials_token=mock.AsyncMock(return_value=mock_token))

        result = await rest.ClientCredentialsStrategy(client=54123123, client_secret="123123123").acquire(mock_rest)

        assert result == "Bearer okokok.fofofo.ddd"

        mock_rest.authorize_client_credentials_token.assert_awaited_once_with(
            client=54123123, client_secret="123123123", scopes=("applications.commands.update", "identify")
        )

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
        assert new_token == "Bearer okokok.fofofo.ddd"  # noqa S105: Possible Hardcoded password

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
        assert results == [
            "Bearer okokok.fofofo.ddd",
            "Bearer okokok.fofofo.ddd",
            "Bearer okokok.fofofo.ddd",
        ]

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
        assert new_token == "Bearer okokok.fofofo.ddd"  # noqa S105: Possible Hardcoded password

    async def test_acquire_uses_newly_cached_token_after_acquiring_lock(self):
        token = "abc.abc.abc"  # noqa S105: Possible Hardcoded password
        mock_rest = mock.AsyncMock()
        strategy = rest.ClientCredentialsStrategy(client=65123, client_secret="12354")

        async def hold_strategy():
            async with strategy._lock:
                await asyncio.sleep(hikari_test_helpers.REASONABLE_SLEEP_TIME)
                strategy._token = token
                strategy._expire_at = time.monotonic() + 600

        asyncio.create_task(hold_strategy())
        await asyncio.sleep(hikari_test_helpers.REASONABLE_SLEEP_TIME // 1000)
        result = await strategy.acquire(mock_rest)

        assert result == token

        mock_rest.authorize_client_credentials_token.assert_not_called()

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


###################
# _LiveAttributes #
###################


class Test_LiveAttributes:
    def test_build(self):
        stack = contextlib.ExitStack()
        create_tcp_connector = stack.enter_context(mock.patch.object(net, "create_tcp_connector"))
        create_client_session = stack.enter_context(mock.patch.object(net, "create_client_session"))
        bucket_manager = stack.enter_context(mock.patch.object(buckets, "RESTBucketManager"))
        manual_rate_limiter = stack.enter_context(mock.patch.object(rate_limits, "ManualRateLimiter"))
        stack.enter_context(mock.patch.object(asyncio, "get_running_loop"))
        mock_settings = object()
        mock_proxy_settings = mock.Mock()

        with stack:
            attributes = rest._LiveAttributes.build(123.321, mock_settings, mock_proxy_settings)

        assert isinstance(attributes, rest._LiveAttributes)
        assert attributes.is_closing is False
        assert attributes.buckets is bucket_manager.return_value
        assert attributes.client_session is create_client_session.return_value
        assert isinstance(attributes.closed_event, asyncio.Event)
        assert attributes.global_rate_limit is manual_rate_limiter.return_value
        assert attributes.tcp_connector is create_tcp_connector.return_value

        bucket_manager.assert_called_once_with(123.321)
        create_tcp_connector.assert_called_once_with(mock_settings)
        create_client_session.assert_called_once_with(
            connector=create_tcp_connector.return_value,
            connector_owner=False,
            http_settings=mock_settings,
            raise_for_status=False,
            trust_env=mock_proxy_settings.trust_env,
        )
        manual_rate_limiter.assert_called_once_with()

    def test_build_when_no_running_loop(self):
        with pytest.raises(RuntimeError):
            rest._LiveAttributes.build(123.321, object(), object())

    @pytest.mark.asyncio()
    async def test_close(self):
        attributes = rest._LiveAttributes(
            buckets=mock.Mock(),
            client_session=mock.AsyncMock(),
            closed_event=mock.Mock(),
            global_rate_limit=mock.Mock(),
            tcp_connector=mock.AsyncMock(),
        )

        await attributes.close()

        assert attributes.is_closing is True
        attributes.buckets.close.assert_called_once_with()
        attributes.client_session.close.assert_awaited_once_with()
        attributes.closed_event.set.assert_called_once_with()
        attributes.global_rate_limit.close.assert_called_once_with()
        attributes.tcp_connector.close.assert_awaited_once_with()

    def test_still_alive_when_alive(self):
        attributes = hikari_test_helpers.mock_class_namespace(rest._LiveAttributes, init_=False)()
        attributes.is_closing = False

        assert attributes.still_alive() is attributes

    def test_still_alive_when_closing(self):
        attributes = hikari_test_helpers.mock_class_namespace(rest._LiveAttributes, init_=False)()
        attributes.is_closing = True

        with pytest.raises(errors.ComponentStateConflictError):
            attributes.still_alive()


###########
# RESTApp #
###########


@pytest.fixture()
def rest_app():
    return hikari_test_helpers.mock_class_namespace(rest.RESTApp, slots_=False)(
        executor=None,
        http_settings=mock.Mock(spec_set=config.HTTPSettings),
        max_rate_limit=float("inf"),
        proxy_settings=mock.Mock(spec_set=config.ProxySettings),
        url="https://some.url",
    )


class TestRESTApp:
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
        mock_event_loop = object()
        rest_app._event_loop = mock_event_loop

        stack = contextlib.ExitStack()
        _entity_factory = stack.enter_context(mock.patch.object(entity_factory, "EntityFactoryImpl"))
        mock_client = stack.enter_context(mock.patch.object(rest, rest.RESTClientImpl.__qualname__))
        stack.enter_context(mock.patch.object(asyncio, "get_running_loop", return_value=mock_event_loop))

        with stack:
            rest_app.acquire(token="token", token_type="Type")

        mock_client.assert_called_once_with(
            cache=None,
            entity_factory=_entity_factory(),
            executor=rest_app._executor,
            http_settings=rest_app._http_settings,
            max_rate_limit=float("inf"),
            proxy_settings=rest_app._proxy_settings,
            token="token",
            token_type="Type",
            rest_url=rest_app._url,
        )

    def test_acquire_defaults_to_bearer_for_a_string_token(self, rest_app):
        mock_event_loop = object()
        rest_app._event_loop = mock_event_loop

        stack = contextlib.ExitStack()
        _entity_factory = stack.enter_context(mock.patch.object(entity_factory, "EntityFactoryImpl"))
        mock_client = stack.enter_context(mock.patch.object(rest, rest.RESTClientImpl.__qualname__))
        stack.enter_context(mock.patch.object(asyncio, "get_running_loop", return_value=mock_event_loop))

        with stack:
            rest_app.acquire(token="token")

        mock_client.assert_called_once_with(
            cache=None,
            entity_factory=_entity_factory(),
            executor=rest_app._executor,
            http_settings=rest_app._http_settings,
            max_rate_limit=float("inf"),
            proxy_settings=rest_app._proxy_settings,
            token="token",
            token_type=applications.TokenType.BEARER,
            rest_url=rest_app._url,
        )


##################
# RESTClientImpl #
##################


@pytest.fixture(scope="module")
def rest_client_class():
    return hikari_test_helpers.mock_class_namespace(rest.RESTClientImpl, slots_=False)


@pytest.fixture()
def live_attributes():
    attributes = mock.Mock(
        buckets=mock.Mock(acquire=mock.Mock(return_value=hikari_test_helpers.AsyncContextManagerMock())),
        global_rate_limit=mock.Mock(acquire=mock.AsyncMock()),
        close=mock.AsyncMock(),
    )
    attributes.still_alive.return_value = attributes
    return attributes


@pytest.fixture()
def mock_cache():
    return mock.Mock()


@pytest.fixture()
def rest_client(rest_client_class, live_attributes, mock_cache):
    obj = rest_client_class(
        cache=mock_cache,
        http_settings=mock.Mock(spec=config.HTTPSettings),
        max_rate_limit=float("inf"),
        proxy_settings=mock.Mock(spec=config.ProxySettings),
        token="some_token",
        token_type="tYpe",
        rest_url="https://some.where/api/v3",
        executor=mock.Mock(),
        entity_factory=mock.Mock(),
    )
    obj._live_attributes = live_attributes
    return obj


@pytest.fixture()
def file_resource():
    class Stream:
        def __init__(self, data):
            self.data = data

        async def data_uri(self):
            return self.data

        async def __aenter__(self):
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            exc_tb,
        ) -> None:
            pass

    class FileResource(files.Resource):
        filename = None
        url = None

        def __init__(self, stream_data):
            self._stream = Stream(data=stream_data)

        def stream(self, executor):
            return self._stream

    return FileResource


@pytest.fixture()
def file_resource_patch(file_resource):
    resource = file_resource("some data")
    with mock.patch.object(files, "ensure_resource", return_value=resource):
        yield resource


class StubModel(snowflakes.Unique):
    id = None

    def __init__(self, id=0):
        self.id = snowflakes.Snowflake(id)


class TestRESTClientImpl:
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
        rest_client._live_attributes = attributes

        assert rest_client.is_alive is expected_result

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

    @pytest.mark.asyncio()
    async def test_close(self, rest_client):
        rest_client._live_attributes = mock_live_attributes = mock.AsyncMock()

        await rest_client.close()

        mock_live_attributes.close.assert_awaited_once_with()
        assert rest_client._live_attributes is None

    def test_start(self, rest_client):
        rest_client._live_attributes = None

        with mock.patch.object(rest._LiveAttributes, "build") as build:
            rest_client.start()

            build.assert_called_once_with(
                rest_client._max_rate_limit, rest_client.http_settings, rest_client.proxy_settings
            )
            assert rest_client._live_attributes is build.return_value

    def test_start_when_active(self, rest_client):
        rest_client._live_attributes = object()

        with pytest.raises(errors.ComponentStateConflictError):
            rest_client.start()

    def test__get_live_attributes_when_active(self, rest_client):
        mock_attributes = rest_client._live_attributes = object()

        assert rest_client._get_live_attributes() is mock_attributes

    def test__get_live_attributes_when_inactive(self, rest_client):
        rest_client._live_attributes = None

        with pytest.raises(errors.ComponentStateConflictError):
            rest_client._get_live_attributes()

    @pytest.mark.parametrize(  # noqa: PT014 - Duplicate test cases (false positive)
        ("emoji", "expected_return"),
        [
            (emojis.CustomEmoji(id=123, name="rooYay", is_animated=False), "rooYay:123"),
            ("👌", "👌"),
            ("\N{OK HAND SIGN}", "\N{OK HAND SIGN}"),
            (emojis.UnicodeEmoji("\N{OK HAND SIGN}"), "\N{OK HAND SIGN}"),
        ],
    )
    def test__transform_emoji_to_url_format(self, rest_client, emoji, expected_return):
        assert rest_client._transform_emoji_to_url_format(emoji, undefined.UNDEFINED) == expected_return

    def test__transform_emoji_to_url_format_with_id(self, rest_client):
        assert rest_client._transform_emoji_to_url_format("rooYay", 123) == "rooYay:123"

    @pytest.mark.parametrize(  # noqa: PT014 - Duplicate test cases (false positive)
        "emoji",
        [
            emojis.CustomEmoji(id=123, name="rooYay", is_animated=False),
            emojis.UnicodeEmoji("\N{OK HAND SIGN}"),
        ],
    )
    def test__transform_emoji_to_url_format_when_id_passed_with_emoji_object(self, rest_client, emoji):
        with pytest.raises(ValueError, match="emoji_id shouldn't be passed when an Emoji object is passed for emoji"):
            rest_client._transform_emoji_to_url_format(emoji, 123)

    def test__stringify_http_message_when_body_is_None(self, rest_client):
        headers = {"HEADER1": "value1", "HEADER2": "value2", "Authorization": "this will never see the light of day"}
        expected_return = "    HEADER1: value1\n    HEADER2: value2\n    Authorization: **REDACTED TOKEN**"
        assert rest_client._stringify_http_message(headers, None) == expected_return

    @pytest.mark.parametrize(("body", "expected"), [(bytes("hello :)", "ascii"), "hello :)"), (123, "123")])
    def test__stringify_http_message_when_body_is_not_None(self, rest_client, body, expected):
        headers = {"HEADER1": "value1", "HEADER2": "value2", "Authorization": "this will never see the light of day"}
        expected_return = (
            f"    HEADER1: value1\n    HEADER2: value2\n    Authorization: **REDACTED TOKEN**\n\n    {expected}"
        )
        assert rest_client._stringify_http_message(headers, body) == expected_return

    #######################
    # Non-async endpoints #
    #######################

    def test_trigger_typing(self, rest_client, live_attributes):
        channel = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "TypingIndicator", return_value=stub_iterator) as typing_indicator:
            assert rest_client.trigger_typing(channel) == stub_iterator

            typing_indicator.assert_called_once_with(
                request_call=rest_client._request, channel=channel, rest_closed_event=live_attributes.closed_event
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
        rest_client._transform_emoji_to_url_format = mock.Mock(return_value="rooYay:123")

        with mock.patch.object(special_endpoints, "ReactorIterator", return_value=stub_iterator) as iterator:
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

    def test_fetch_members(self, rest_client):
        guild = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "MemberIterator", return_value=stub_iterator) as iterator:
            assert rest_client.fetch_members(guild) == stub_iterator

            iterator.assert_called_once_with(
                entity_factory=rest_client._entity_factory,
                request_call=rest_client._request,
                guild=guild,
            )

    def test_kick_member(self, rest_client):
        assert rest_client.kick_member == rest_client.kick_user

    def test_ban_member(self, rest_client):
        assert rest_client.ban_member == rest_client.ban_user

    def test_unban_member(self, rest_client):
        assert rest_client.unban_member == rest_client.unban_user


@pytest.mark.asyncio()
class TestRESTClientImplAsync:
    @pytest.fixture()
    def exit_exception(self):
        class ExitException(Exception):
            ...

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
    async def test__request_with_strategy_token(self, rest_client, exit_exception, live_attributes):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        live_attributes.buckets.is_started = True
        rest_client._token = mock.Mock(rest_api.TokenStrategy, acquire=mock.AsyncMock(return_value="Bearer ok.ok.ok"))
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(exit_exception):
            await rest_client._request(route)

        _, kwargs = mock_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"
        assert live_attributes.still_alive.call_count == 3

    @hikari_test_helpers.timeout()
    async def test__request_retries_strategy_once(self, rest_client, exit_exception, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.UNAUTHORIZED
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value", "HEADER": "value"}

            async def read(self):
                return '{"something": null}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(
            request=hikari_test_helpers.CopyingAsyncMock(side_effect=[StubResponse(), exit_exception])
        )
        live_attributes.buckets.is_started = True
        rest_client._token = mock.Mock(
            rest_api.TokenStrategy, acquire=mock.AsyncMock(side_effect=["Bearer ok.ok.ok", "Bearer ok2.ok2.ok2"])
        )
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(exit_exception):
            await rest_client._request(route)

        _, kwargs = mock_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"
        _, kwargs = mock_session.request.call_args_list[1]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok2.ok2.ok2"
        assert live_attributes.still_alive.call_count == 6

    @hikari_test_helpers.timeout()
    async def test__request_raises_after_retry(self, rest_client, exit_exception, live_attributes):
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
        mock_session = mock.AsyncMock(
            request=hikari_test_helpers.CopyingAsyncMock(side_effect=[StubResponse(), StubResponse(), StubResponse()])
        )
        live_attributes.buckets.is_started = True
        rest_client._token = mock.Mock(
            rest_api.TokenStrategy, acquire=mock.AsyncMock(side_effect=["Bearer ok.ok.ok", "Bearer ok2.ok2.ok2"])
        )
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(errors.UnauthorizedError):
            await rest_client._request(route)

        _, kwargs = mock_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok.ok.ok"
        _, kwargs = mock_session.request.call_args_list[1]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "Bearer ok2.ok2.ok2"
        assert live_attributes.still_alive.call_count == 6

    @hikari_test_helpers.timeout()
    async def test__request_when__token_is_None(self, rest_client, exit_exception, live_attributes):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        live_attributes.buckets.is_started = True
        rest_client._token = None
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(exit_exception):
            await rest_client._request(route)

        _, kwargs = mock_session.request.call_args_list[0]
        assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]

    @hikari_test_helpers.timeout()
    async def test__request_when__token_is_not_None(self, rest_client, exit_exception, live_attributes):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        live_attributes.buckets.is_started = True
        rest_client._token = "token"
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(exit_exception):
            await rest_client._request(route)

        _, kwargs = mock_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "token"
        assert live_attributes.still_alive.call_count == 3

    @hikari_test_helpers.timeout()
    async def test__request_when_no_auth_passed(self, rest_client, exit_exception, live_attributes):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        live_attributes.buckets.is_started = True
        rest_client._token = "token"
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(exit_exception):
            await rest_client._request(route, no_auth=True)

        _, kwargs = mock_session.request.call_args_list[0]
        assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]
        live_attributes.buckets.acquire.assert_called_once_with(route)
        live_attributes.buckets.acquire.return_value.assert_used_once()
        live_attributes.global_rate_limit.acquire.assert_not_called()
        assert live_attributes.still_alive.call_count == 2

    @hikari_test_helpers.timeout()
    async def test__request_when_auth_passed(self, rest_client, exit_exception, live_attributes):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        live_attributes.buckets.is_started = True
        rest_client._token = "token"
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(exit_exception):
            await rest_client._request(route, auth="ooga booga")

        _, kwargs = mock_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "ooga booga"
        live_attributes.buckets.acquire.assert_called_once_with(route)
        live_attributes.buckets.acquire.return_value.assert_used_once()
        live_attributes.global_rate_limit.acquire.assert_awaited_once_with()
        assert live_attributes.still_alive.call_count == 3

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_NO_CONTENT(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        live_attributes.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        assert (await rest_client._request(route)) is None
        assert live_attributes.still_alive.call_count == 3

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_APPLICATION_JSON(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.OK
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value", "HEADER": "value"}

            async def read(self):
                return '{"something": null}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        live_attributes.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        assert (await rest_client._request(route)) == {"something": None}
        assert live_attributes.still_alive.call_count == 3

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_not_JSON(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.IM_USED
            content_type = "text/html"
            reason = "cause why not"
            real_url = "https://some.url"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        live_attributes.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(errors.HTTPError):
            await rest_client._request(route)

        assert live_attributes.still_alive.call_count == 3

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_not_between_200_and_300(
        self, rest_client, exit_exception, live_attributes
    ):
        class StubResponse:
            status = http.HTTPStatus.NOT_IMPLEMENTED
            content_type = "text/html"
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        live_attributes.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        rest_client._handle_error_response = mock.AsyncMock(side_effect=exit_exception)
        live_attributes.client_session = mock_session
        rest_client._stringify_http_message = mock.Mock()
        with pytest.raises(exit_exception):
            await rest_client._request(route)

        assert live_attributes.still_alive.call_count == 3

    @hikari_test_helpers.timeout()
    async def test__request_when_response__RetryRequest_gets_handled(
        self, rest_client, exit_exception, live_attributes
    ):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=[rest_client._RetryRequest, exit_exception]))
        live_attributes.buckets.is_started = True
        live_attributes.client_session = mock_session
        with pytest.raises(exit_exception):
            await rest_client._request(route)

        assert live_attributes.still_alive.call_count == 6

    @pytest.mark.parametrize("enabled", [True, False])
    @hikari_test_helpers.timeout()
    async def test__request_logger(self, rest_client, enabled, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            headers = {}
            reason = "cause why not"

            async def read(self):
                return None

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        live_attributes.buckets.is_started = True
        live_attributes.client_session = mock_session
        rest_client._parse_ratelimits = mock.AsyncMock()

        with mock.patch.object(rest, "_LOGGER", new=mock.Mock(isEnabledFor=mock.Mock(return_value=enabled))) as logger:
            await rest_client._request(route)

        if enabled:
            assert logger.log.call_count == 2
        else:
            assert logger.log.call_count == 0

        assert live_attributes.still_alive.call_count == 3

    async def test__handle_error_response(self, rest_client, exit_exception):
        mock_response = mock.Mock()
        with mock.patch.object(net, "generate_error_response", return_value=exit_exception) as generate_error_response:
            with pytest.raises(exit_exception):
                await rest_client._handle_error_response(mock_response)

            generate_error_response.assert_called_once_with(mock_response)

    async def test__parse_ratelimits_when_not_ratelimited(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.OK
            headers = {}

            json = mock.AsyncMock()

        response = StubResponse()
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        await rest_client._parse_ratelimits(route, response, live_attributes)
        response.json.assert_not_called()
        assert live_attributes.still_alive.call_count == 0

    async def test__parse_ratelimits_when_ratelimited(self, rest_client, exit_exception, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}

            async def json(self):
                raise exit_exception

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(exit_exception):
            await rest_client._parse_ratelimits(route, StubResponse(), live_attributes)

        assert live_attributes.still_alive.call_count == 0

    async def test__parse_ratelimits_when_unexpected_content_type(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = "text/html"
            headers = {}
            real_url = "https://some.url"

            async def read(self):
                return "this is not json :)"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(errors.HTTPResponseError):
            await rest_client._parse_ratelimits(route, StubResponse(), live_attributes)

        assert live_attributes.still_alive.call_count == 0

    async def test__parse_ratelimits_when_global_ratelimit(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def json(self):
                return {"global": True, "retry_after": "2"}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(rest_client._RetryRequest):
            await rest_client._parse_ratelimits(route, StubResponse(), live_attributes)

        live_attributes.global_rate_limit.throttle.assert_called_once_with(2.0)
        assert live_attributes.still_alive.call_count == 1

    async def test__parse_ratelimits_when_remaining_header_under_or_equal_to_0(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {
                rest._X_RATELIMIT_REMAINING_HEADER: "0",
            }
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "2", "global": False}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(rest_client._RetryRequest):
            await rest_client._parse_ratelimits(route, StubResponse(), live_attributes)

        assert live_attributes.still_alive.call_count == 0

    async def test__parse_ratelimits_when_retry_after_is_close_enough(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {
                rest._X_RATELIMIT_RESET_AFTER_HEADER: "0.002",
            }
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "0.002"}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(rest_client._RetryRequest):
            await rest_client._parse_ratelimits(route, StubResponse(), live_attributes)

        assert live_attributes.still_alive.call_count == 0

    async def test__parse_ratelimits_when_retry_after_is_not_close_enough(self, rest_client, live_attributes):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {}
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "4"}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(errors.RateLimitedError):
            await rest_client._parse_ratelimits(route, StubResponse(), live_attributes)

        assert live_attributes.still_alive.call_count == 0

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

    async def test_edit_channel(self, rest_client):
        expected_route = routes.PATCH_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload": "GO"})
        rest_client._entity_factory.serialize_permission_overwrite = mock.Mock(
            return_value={"type": "member", "allow": 1024, "deny": 8192, "id": "1235431"}
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

        result = await rest_client.delete_channel(StubModel(123))

        assert result is rest_client._entity_factory.deserialize_channel.return_value
        rest_client._entity_factory.deserialize_channel.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route)

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

    async def test_edit_permission_overwrites(self, rest_client):
        target = StubModel(456)
        expected_route = routes.PUT_CHANNEL_PERMISSIONS.compile(channel=123, overwrite=456)
        rest_client._request = mock.AsyncMock()
        expected_json = {"type": 1, "allow": 4, "deny": 1}

        await rest_client.edit_permission_overwrites(
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
            (
                users.UserImpl(
                    id=456,
                    app=object(),
                    avatar_hash="",
                    discriminator="",
                    flags=0,
                    username="",
                    is_bot=True,
                    is_system=True,
                ),
                channels.PermissionOverwriteType.MEMBER,
            ),
            (
                guilds.Role(
                    id=456,
                    app=object(),
                    color=None,
                    guild_id=123,
                    is_hoisted=True,
                    is_managed=False,
                    name="",
                    is_mentionable=True,
                    permissions=0,
                    position=0,
                    bot_id=None,
                    integration_id=None,
                    is_premium_subscriber_role=False,
                ),
                channels.PermissionOverwriteType.ROLE,
            ),
            (
                channels.PermissionOverwrite(type=channels.PermissionOverwriteType.MEMBER, id=456),
                channels.PermissionOverwriteType.MEMBER,
            ),
        ],
    )
    async def test_edit_permission_overwrites_when_target_undefined(self, rest_client, target, expected_type):
        expected_route = routes.PUT_CHANNEL_PERMISSIONS.compile(channel=123, overwrite=456)
        rest_client._request = mock.AsyncMock()
        expected_json = {"type": expected_type}

        await rest_client.edit_permission_overwrites(StubModel(123), target)
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)

    async def test_edit_permission_overwrites_when_cant_determine_target_type(self, rest_client):
        with pytest.raises(TypeError):
            await rest_client.edit_permission_overwrites(StubModel(123), StubModel(123))

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

    @pytest.mark.skip("TODO")
    async def test_create_message(self, rest_client):
        ...  # TODO: Implement

    async def test_create_message_when_attachment_and_attachments_given(self, rest_client):
        with pytest.raises(ValueError, match="You may only specify one of 'attachment' or 'attachments', not both"):
            await rest_client.create_message(StubModel(123), attachment=object(), attachments=object())

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

    @pytest.mark.skip("TODO")
    async def test_edit_message(self, rest_client):
        ...  # TODO: Implement

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

        await rest_client.delete_message(StubModel(123), StubModel(456))
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_messages(self, rest_client):
        messages = [StubModel(i) for i in range(200)]
        expected_route = routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=123)
        expected_json1 = {"messages": [str(i) for i in range(100)]}
        expected_json2 = {"messages": [str(i) for i in range(100, 200)]}

        rest_client._request = mock.AsyncMock()

        await rest_client.delete_messages(StubModel(123), *messages)

        assert rest_client._request.await_args_list == [
            mock.call(expected_route, json=expected_json1),
            mock.call(expected_route, json=expected_json2),
        ]

    async def test_delete_messages_when_one_message_left_in_chunk(self, rest_client):
        channel = StubModel(123)
        messages = [StubModel(i) for i in range(101)]
        message = messages[-1]
        expected_json = {"messages": [str(i) for i in range(100)]}

        rest_client._request = mock.AsyncMock()

        await rest_client.delete_messages(channel, *messages)

        assert rest_client._request.await_args_list == [
            mock.call(routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel), json=expected_json),
            mock.call(routes.DELETE_CHANNEL_MESSAGE.compile(channel=channel, message=message)),
        ]

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

        await rest_client.delete_messages(channel, messages, StubModel(444), StubModel(6523))

        rest_client._request.assert_has_awaits(
            [
                mock.call(
                    routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel),
                    json={"messages": [str(i) for i in range(100)]},
                ),
                mock.call(
                    routes.POST_DELETE_CHANNEL_MESSAGES_BULK.compile(channel=channel),
                    json={"messages": ["100", "444", "6523"]},
                ),
            ]
        )

    async def test_add_reaction(self, rest_client):
        expected_route = routes.PUT_MY_REACTION.compile(emoji="rooYay:123", channel=123, message=456)
        rest_client._request = mock.AsyncMock()
        rest_client._transform_emoji_to_url_format = mock.Mock(return_value="rooYay:123")

        await rest_client.add_reaction(StubModel(123), StubModel(456), "<:rooYay:123>")
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_my_reaction(self, rest_client):
        expected_route = routes.DELETE_MY_REACTION.compile(emoji="rooYay:123", channel=123, message=456)
        rest_client._request = mock.AsyncMock()
        rest_client._transform_emoji_to_url_format = mock.Mock(return_value="rooYay:123")

        await rest_client.delete_my_reaction(StubModel(123), StubModel(456), "<:rooYay:123>")
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_all_reactions_for_emoji(self, rest_client):
        expected_route = routes.DELETE_REACTION_EMOJI.compile(emoji="rooYay:123", channel=123, message=456)
        rest_client._request = mock.AsyncMock()
        rest_client._transform_emoji_to_url_format = mock.Mock(return_value="rooYay:123")

        await rest_client.delete_all_reactions_for_emoji(StubModel(123), StubModel(456), "<:rooYay:123>")
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_delete_reaction(self, rest_client):
        expected_route = routes.DELETE_REACTION_USER.compile(emoji="rooYay:123", channel=123, message=456, user=789)
        rest_client._request = mock.AsyncMock()
        rest_client._transform_emoji_to_url_format = mock.Mock(return_value="rooYay:123")

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
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook_without_token(self, rest_client):
        webhook = StubModel(123)
        expected_route = routes.GET_WEBHOOK.compile(webhook=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.fetch_webhook(StubModel(123)) is webhook
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=False)
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

    async def test_edit_webhook(self, rest_client):
        webhook = StubModel(456)
        expected_route = routes.PATCH_WEBHOOK_WITH_TOKEN.compile(webhook=123, token="token")
        expected_json = {
            "name": "some other name",
            "channel": "789",
            "avatar": None,
        }
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
            expected_route, json=expected_json, reason="some smart reason to do this", no_auth=True
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
            expected_route, json=expected_json, reason=undefined.UNDEFINED, no_auth=False
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
            expected_route, json=expected_json, reason=undefined.UNDEFINED, no_auth=False
        )
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_delete_webhook(self, rest_client):
        expected_route = routes.DELETE_WEBHOOK_WITH_TOKEN.compile(webhook=123, token="token")
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})

        await rest_client.delete_webhook(StubModel(123), token="token")
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)

    async def test_delete_webhook_without_token(self, rest_client):
        expected_route = routes.DELETE_WEBHOOK.compile(webhook=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})

        await rest_client.delete_webhook(StubModel(123))
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=False)

    @pytest.mark.skip("TODO")
    async def test_execute_webhook(self, rest_client):
        ...  # TODO: Implement

    async def test_execute_webhook_when_attachment_and_attachments_given(self, rest_client):
        with pytest.raises(ValueError, match="You may only specify one of 'attachment' or 'attachments', not both"):
            await rest_client.execute_webhook(StubModel(123), "token", attachment=object(), attachments=object())

    async def test_execute_webhook_when_embed_and_embeds_given(self, rest_client):
        with pytest.raises(ValueError, match="You may only specify one of 'embed' or 'embeds', not both"):
            await rest_client.execute_webhook(StubModel(123), "token", embed=object(), embeds=object())

    async def test_fetch_webhook_message(self, rest_client):
        message_obj = mock.Mock()
        expected_route = routes.GET_WEBHOOK_MESSAGE.compile(webhook=123, token="hi, im a token", message=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_message = mock.Mock(return_value=message_obj)

        assert await rest_client.fetch_webhook_message(StubModel(123), "hi, im a token", StubModel(456)) is message_obj
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"id": "456"})

    @pytest.mark.skip("TODO")
    async def test_edit_webhook_message(self, rest_client):
        ...  # TODO: Implement

    async def test_delete_webhook_message(self, rest_client):
        expected_route = routes.DELETE_WEBHOOK_MESSAGE.compile(webhook=123, token="token", message=456)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_webhook_message(StubModel(123), "token", StubModel(456))
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)

    async def test_fetch_gateway_url(self, rest_client):
        expected_route = routes.GET_GATEWAY.compile()
        rest_client._request = mock.AsyncMock(return_value={"url": "wss://some.url"})

        assert await rest_client.fetch_gateway_url() == "wss://some.url"
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)

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

        assert await rest_client.fetch_invite(input_invite) == return_invite
        rest_client._request.assert_awaited_once_with(
            expected_route, query={"with_counts": "true", "with_expiration": "true"}
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

        with mock.patch.object(data_binding, "URLEncodedForm", return_value=mock_url_encoded_form):
            await rest_client.authorize_client_credentials_token(65234123, "4312312", scopes=["scope1", "scope2"])

        mock_url_encoded_form.add_field.assert_has_calls(
            [mock.call("grant_type", "client_credentials"), mock.call("scope", "scope1 scope2")]
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form=mock_url_encoded_form, auth="Basic NjUyMzQxMjM6NDMxMjMxMg=="
        )
        rest_client._entity_factory.deserialize_partial_token.assert_called_once_with(rest_client._request.return_value)

    async def test_authorize_access_token_without_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedForm", return_value=mock_url_encoded_form):
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
            expected_route, form=mock_url_encoded_form, auth="Basic NjUyMzQ6NDMxMjM="
        )

    async def test_authorize_access_token_with_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedForm", return_value=mock_url_encoded_form):
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
            expected_route, form=mock_url_encoded_form, auth="Basic MTIzNDM6MTIzNTU1NQ=="
        )

    async def test_refresh_access_token_without_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedForm", return_value=mock_url_encoded_form):
            result = await rest_client.refresh_access_token(454123, "123123", "a.codet")

        mock_url_encoded_form.add_field.assert_has_calls(
            [
                mock.call("grant_type", "refresh_token"),
                mock.call("refresh_token", "a.codet"),
            ]
        )
        assert result is rest_client._entity_factory.deserialize_authorization_token.return_value
        rest_client._entity_factory.deserialize_authorization_token.assert_called_once_with(
            rest_client._request.return_value
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, form=mock_url_encoded_form, auth="Basic NDU0MTIzOjEyMzEyMw=="
        )

    async def test_refresh_access_token_with_scopes(self, rest_client):
        expected_route = routes.POST_TOKEN.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock(return_value={"access_token": 42})

        with mock.patch.object(data_binding, "URLEncodedForm", return_value=mock_url_encoded_form):
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
            expected_route, form=mock_url_encoded_form, auth="Basic NTQxMjM6MzEyMzEy"
        )

    async def test_revoke_access_token(self, rest_client):
        expected_route = routes.POST_TOKEN_REVOKE.compile()
        mock_url_encoded_form = mock.Mock()
        rest_client._request = mock.AsyncMock()

        with mock.patch.object(data_binding, "URLEncodedForm", return_value=mock_url_encoded_form):
            await rest_client.revoke_access_token(54123, "123542", "not.a.token")

        mock_url_encoded_form.add_field.assert_called_once_with("token", "not.a.token")
        rest_client._request.assert_awaited_once_with(
            expected_route, form=mock_url_encoded_form, auth="Basic NTQxMjM6MTIzNTQy"
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
            nick="cool nick",
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

        await rest_client.delete_emoji(StubModel(123), StubModel(456))
        rest_client._request.assert_awaited_once_with(expected_route)

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

    async def test_create_guild_text_channel(self, rest_client):
        guild = StubModel(123)
        channel = mock.Mock(channels.GuildTextChannel)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock(return_value=channel)

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
        )
        assert returned is channel
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
        )

    async def test_create_guild_news_channel(self, rest_client):
        guild = StubModel(123)
        channel = mock.Mock(spec_set=channels.GuildNewsChannel)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock(return_value=channel)

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
        )
        assert returned is channel
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
        )

    async def test_create_guild_voice_channel(self, rest_client):
        guild = StubModel(123)
        channel = mock.Mock(channels.GuildVoiceChannel)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock(return_value=channel)

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
        assert returned is channel
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

    async def test_create_guild_stage_channel(self, rest_client):
        guild = StubModel(123)
        channel = mock.Mock(channels.GuildStageChannel)
        category_channel = StubModel(789)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock(return_value=channel)

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
        assert returned is channel
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

    async def test_create_guild_category(self, rest_client):
        guild = StubModel(123)
        category = mock.Mock(spec_set=channels.GuildCategory)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
        rest_client._create_guild_channel = mock.AsyncMock(return_value=category)

        returned = await rest_client.create_guild_category(
            guild,
            "general",
            position=1,
            permission_overwrites=[overwrite1, overwrite2],
            reason="because we need one",
        )
        assert returned is category
        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_CATEGORY,
            position=1,
            permission_overwrites=[overwrite1, overwrite2],
            reason="because we need one",
        )

    async def test__create_guild_channel(self, rest_client):
        channel = mock.Mock(spec_set=channels.GuildChannel)
        overwrite1 = StubModel(987)
        overwrite2 = StubModel(654)
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
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=channel)
        rest_client._entity_factory.serialize_permission_overwrite = mock.Mock(
            side_effect=[{"id": "987"}, {"id": "654"}]
        )

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
        )
        assert returned is channel
        rest_client._request.assert_awaited_once_with(
            expected_route, json=expected_json, reason="we have got the power"
        )
        rest_client._entity_factory.deserialize_channel.assert_called_once_with({"id": "456"})
        assert rest_client._entity_factory.serialize_permission_overwrite.call_count == 2
        rest_client._entity_factory.serialize_permission_overwrite.assert_has_calls(
            [mock.call(overwrite1), mock.call(overwrite2)]
        )

    async def test_reposition_channels(self, rest_client):
        expected_route = routes.POST_GUILD_CHANNELS.compile(guild=123)
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
        expected_json = {"nick": "test", "roles": ["654", "321"], "mute": True, "deaf": False, "channel_id": "987"}
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        result = await rest_client.edit_member(
            StubModel(123),
            StubModel(456),
            nick="test",
            roles=[StubModel(654), StubModel(321)],
            mute=True,
            deaf=False,
            voice_channel=StubModel(987),
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
            nick="test",
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
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json=expected_json,
            reason="because i can",
        )

    async def test_edit_member_without_optionals(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        result = await rest_client.edit_member(StubModel(123), StubModel(456))

        assert result is rest_client._entity_factory.deserialize_member.return_value
        rest_client._entity_factory.deserialize_member.assert_called_once_with(
            rest_client._request.return_value, guild_id=123
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)

    async def test_edit_my_nick(self, rest_client):
        expected_route = routes.PATCH_MY_GUILD_NICKNAME.compile(guild=123)
        expected_json = {"nick": "hikari is the best"}
        rest_client._request = mock.AsyncMock()

        await rest_client.edit_my_nick(StubModel(123), "hikari is the best", reason="because its true")
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="because its true")

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
        expected_json = {"delete_message_days": 7, "reason": "because i can"}
        rest_client._request = mock.AsyncMock()

        await rest_client.ban_user(StubModel(123), StubModel(456), delete_message_days=7, reason="because i can")
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)

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

    async def test_fetch_bans(self, rest_client):
        ban1 = StubModel(456)
        ban2 = StubModel(789)
        expected_route = routes.GET_GUILD_BANS.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "456"}, {"id": "789"}])
        rest_client._entity_factory.deserialize_guild_member_ban = mock.Mock(side_effect=[ban1, ban2])

        assert await rest_client.fetch_bans(StubModel(123)) == [ban1, ban2]
        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_guild_member_ban.call_count == 2
        rest_client._entity_factory.deserialize_guild_member_ban.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
        )

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

    async def test_create_role(self, rest_client):
        role = StubModel(456)
        expected_route = routes.POST_GUILD_ROLES.compile(guild=123)
        expected_json = {
            "name": "admin",
            "permissions": 8,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "mentionable": False,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_role = mock.Mock(return_value=role)

        returned = await rest_client.create_role(
            StubModel(123),
            name="admin",
            permissions=permissions.Permissions.ADMINISTRATOR,
            color=colors.Color.from_int(12345),
            hoist=True,
            mentionable=False,
            reason="roles are cool",
        )
        assert returned is role
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
        with pytest.raises(TypeError):
            await rest_client.create_role(
                StubModel(123), color=colors.Color.from_int(12345), colour=colors.Color.from_int(12345)
            )

    async def test_reposition_roles(self, rest_client):
        expected_route = routes.POST_GUILD_ROLES.compile(guild=123)
        expected_json = [{"id": "456", "position": 1}, {"id": "789", "position": 2}]
        rest_client._request = mock.AsyncMock()

        await rest_client.reposition_roles(StubModel(123), {1: StubModel(456), 2: StubModel(789)})
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)

    async def test_edit_role(self, rest_client):
        role = StubModel(456)
        expected_route = routes.PATCH_GUILD_ROLE.compile(guild=123, role=789)
        expected_json = {
            "name": "admin",
            "permissions": 8,
            "color": colors.Color.from_int(12345),
            "hoist": True,
            "mentionable": False,
        }
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_role = mock.Mock(return_value=role)

        returned = await rest_client.edit_role(
            StubModel(123),
            StubModel(789),
            name="admin",
            permissions=permissions.Permissions.ADMINISTRATOR,
            color=colors.Color.from_int(12345),
            hoist=True,
            mentionable=False,
            reason="roles are cool",
        )
        assert returned is role
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="roles are cool")
        rest_client._entity_factory.deserialize_role.assert_called_once_with({"id": "456"}, guild_id=123)

    async def test_edit_role_when_color_and_colour_specified(self, rest_client):
        with pytest.raises(TypeError):
            await rest_client.edit_role(
                StubModel(123), StubModel(456), color=colors.Color.from_int(12345), colour=colors.Color.from_int(12345)
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

        assert await rest_client.fetch_integrations(StubModel(123)) == [
            integration1,
            integration2,
        ]
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
        expected_json = {
            "enabled": True,
            "channel": "456",
        }
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
        expected_json = {
            "enabled": True,
            "channel": None,
        }
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
            expected_route,
            json={
                "description": None,
                "welcome_channels": None,
            },
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

    def test_command_builder(self, rest_client):
        result = rest_client.command_builder("a name", "very very good")

        assert result.name == "a name"
        assert result.description == "very very good"
        assert isinstance(result, special_endpoints.CommandBuilder)

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
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_command.assert_called_once_with({"id": "34512312"}, guild_id=7623423)

    async def test_fetch_application_commands_without_guild(self, rest_client):
        expected_route = routes.GET_APPLICATION_COMMANDS.compile(application=54123)
        rest_client._request = mock.AsyncMock(return_value=[{"id": "34512312"}])

        result = await rest_client.fetch_application_commands(StubModel(54123))

        assert result == [rest_client._entity_factory.deserialize_command.return_value]
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_command.assert_called_once_with({"id": "34512312"}, guild_id=None)

    async def test_create_application_command_with_optionals(self, rest_client):
        expected_route = routes.POST_APPLICATION_GUILD_COMMAND.compile(application=4332123, guild=653452134)
        rest_client._request = mock.AsyncMock(return_value={"id": "29393939"})
        mock_option = object()

        result = await rest_client.create_application_command(
            StubModel(4332123), "okokok", "not ok anymore", StubModel(653452134), options=[mock_option]
        )

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._entity_factory.serialize_command_option.assert_called_once_with(mock_option)
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=653452134
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json={
                "name": "okokok",
                "description": "not ok anymore",
                "options": [rest_client._entity_factory.serialize_command_option.return_value],
            },
        )

    async def test_create_application_command_without_optionals(self, rest_client):
        expected_route = routes.POST_APPLICATION_COMMAND.compile(application=4332123)
        rest_client._request = mock.AsyncMock(return_value={"id": "29393939"})

        result = await rest_client.create_application_command(StubModel(4332123), "okokok", "not ok anymore")

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=None
        )
        rest_client._request.assert_awaited_once_with(
            expected_route, json={"name": "okokok", "description": "not ok anymore"}
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
            },
        )
        rest_client._entity_factory.serialize_command_option.assert_called_once_with(mock_option)

    async def test_edit_application_command_without_optionals(self, rest_client):
        expected_route = routes.PATCH_APPLICATION_COMMAND.compile(application=1235432, command=3451231)
        rest_client._request = mock.AsyncMock(return_value={"id": "94594994"})

        result = await rest_client.edit_application_command(
            StubModel(1235432),
            StubModel(3451231),
        )

        assert result is rest_client._entity_factory.deserialize_command.return_value
        rest_client._entity_factory.deserialize_command.assert_called_once_with(
            rest_client._request.return_value, guild_id=None
        )
        rest_client._request.assert_awaited_once_with(expected_route, json={})

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

    def test_interaction_deferred_builder(self, rest_client):
        result = rest_client.interaction_deferred_builder(5)

        assert result.type == 5
        assert isinstance(result, special_endpoints.InteractionDeferredBuilder)

    def test_interaction_message_builder(self, rest_client):
        result = rest_client.interaction_message_builder(4)

        assert result.type == 4
        assert isinstance(result, special_endpoints.InteractionMessageBuilder)

    async def test_fetch_interaction_response(self, rest_client):
        expected_route = routes.GET_INTERACTION_RESPONSE.compile(webhook=1235432, token="go homo or go gnomo")
        rest_client._request = mock.AsyncMock(return_value={"id": "94949494949"})

        result = await rest_client.fetch_interaction_response(StubModel(1235432), "go homo or go gnomo")

        assert result is rest_client._entity_factory.deserialize_message.return_value
        rest_client._entity_factory.deserialize_message.assert_called_once_with(rest_client._request.return_value)
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)

    @pytest.mark.skip("TODO")
    async def test_create_interaction_response_with_optionals(self, rest_client):
        ...

    @pytest.mark.skip("TODO")
    async def test_create_interaction_response_without_optionals(self, rest_client):
        ...

    @pytest.mark.skip("TODO: this basically dupes test_edit_webhook_message")
    async def test_edit_interaction_response_with_optionals(self, rest_client):
        ...

    @pytest.mark.skip("TODO: this basically dupes test_edit_webhook_message")
    async def test_edit_interaction_response_without_optionals(self, rest_client):
        ...

    async def test_delete_interaction_response(self, rest_client):
        expected_route = routes.DELETE_INTERACTION_RESPONSE.compile(webhook=1235431, token="go homo now")
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_interaction_response(StubModel(1235431), "go homo now")

        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)
