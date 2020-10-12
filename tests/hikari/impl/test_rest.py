# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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

import aiohttp
import mock
import pytest

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
from hikari.impl import buckets
from hikari.impl import entity_factory
from hikari.impl import rest
from hikari.impl import special_endpoints
from hikari.internal import net
from hikari.internal import routes
from hikari.internal import ux
from tests.hikari import client_session_stub
from tests.hikari import hikari_test_helpers

######################################
# BasicLazyCachedTCPConnectorFactory #
######################################


@pytest.fixture()
def http_settings():
    return mock.Mock(spec_set=config.HTTPSettings)


@pytest.fixture()
def connector_factory(http_settings):
    return rest.BasicLazyCachedTCPConnectorFactory(http_settings)


class TestBasicLazyCachedTCPConnectorFactory:
    def test_acquire_when_connector_is_None(self, connector_factory, http_settings):
        connector_mock = object()
        connector_factory.connector = None

        with mock.patch.object(aiohttp, "TCPConnector", return_value=connector_mock) as tcp_connector:
            assert connector_factory.acquire() is connector_mock
            assert connector_factory.connector is connector_mock
        tcp_connector.assert_called_once_with(
            force_close=http_settings.force_close_transports,
            enable_cleanup_closed=http_settings.enable_cleanup_closed,
            limit=100,
            ssl_context=http_settings.ssl,
            ttl_dns_cache=10,
            use_dns_cache=True,
        )

    def test_acquire_when_connector_is_not_None(self, connector_factory):
        connector_mock = object()
        connector_factory.connector = connector_mock
        assert connector_factory.acquire() is connector_mock


@pytest.mark.asyncio
class TestBasicLazyCachedTCPConnectorFactoryAsync:
    async def test_close_when_connector_is_None(self, connector_factory):
        connector_factory.connector = None
        await connector_factory.close()

    async def test_close_when_connector_is_not_None(self, connector_factory):
        connector_mock = mock.Mock(close=mock.AsyncMock())
        connector_factory.connector = connector_mock

        await connector_factory.close()
        assert connector_factory.connector is None
        connector_mock.close.assert_awaited_once_with()


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
    def cache(self):
        return mock.Mock()

    @pytest.fixture()
    def executor(self):
        return mock.Mock()

    @pytest.fixture()
    def entity_factory(self):
        return mock.Mock()

    @pytest.fixture()
    def rest_provider(self, rest_client, cache, executor, entity_factory):
        return rest._RESTProvider(lambda: entity_factory, executor, lambda: cache, lambda: rest_client)

    def test_rest_property(self, rest_provider, rest_client):
        assert rest_provider.rest == rest_client

    def test_http_settings_property(self, rest_provider, rest_client):
        assert rest_provider.http_settings == rest_client.http_settings

    def test_proxy_settings_property(self, rest_provider, rest_client):
        assert rest_provider.proxy_settings == rest_client.proxy_settings

    def test_entity_factory_property(self, rest_provider, entity_factory):
        assert rest_provider.entity_factory == entity_factory

    def test_cache_property(self, rest_provider, cache):
        assert rest_provider.cache == cache

    def test_executor_property(self, rest_provider, executor):
        assert rest_provider.executor == executor

    def test_me_property(self, rest_provider, cache):
        assert rest_provider.me == cache.get_me()


###########
# RESTApp #
###########


@pytest.fixture()
def rest_app():
    return hikari_test_helpers.mock_class_namespace(rest.RESTApp, slots_=False)(
        connector_factory=mock.Mock(),
        connector_owner=False,
        executor=None,
        http_settings=mock.Mock(spec_set=config.HTTPSettings),
        max_rate_limit=float("inf"),
        proxy_settings=mock.Mock(spec_set=config.ProxySettings),
        url="https://some.url",
    )


class TestRESTApp:
    def test__init__when_connector_factory_is_None(self):
        http_settings = object()

        with mock.patch.object(rest, "BasicLazyCachedTCPConnectorFactory") as factory:
            rest_app = rest.RESTApp(
                connector_factory=None,
                connector_owner=False,
                executor=None,
                http_settings=http_settings,
                max_rate_limit=float("inf"),
                proxy_settings=None,
                url=None,
            )

        factory.assert_called_once_with(http_settings)

        assert rest_app._connector_factory is factory()
        assert rest_app._connector_owner is True

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
            connector_factory=rest_app._connector_factory,
            connector_owner=rest_app._connector_owner,
            entity_factory=_entity_factory(),
            executor=rest_app._executor,
            http_settings=rest_app._http_settings,
            max_rate_limit=float("inf"),
            proxy_settings=rest_app._proxy_settings,
            token="token",
            token_type="Type",
            rest_url=rest_app._url,
        )

    def test_acquire_when_even_loop_not_set(self, rest_app):
        mock_event_loop = object()

        stack = contextlib.ExitStack()
        _entity_factory = stack.enter_context(mock.patch.object(entity_factory, "EntityFactoryImpl"))
        stack.enter_context(mock.patch.object(rest, rest.RESTClientImpl.__qualname__))
        stack.enter_context(mock.patch.object(asyncio, "get_running_loop", return_value=mock_event_loop))

        with stack:
            rest_app.acquire(token="token", token_type="Type")

        assert rest_app._event_loop is mock_event_loop

        # This is just to test the lambdas so it counts towards coverage
        assert _entity_factory.call_count == 1
        factory = _entity_factory.call_args_list[0][0][0]
        factory.entity_factory
        factory.cache
        factory.rest

    def test_acquire_when__event_loop_and_loop_do_not_equal(self, rest_app):
        rest_app._event_loop = object()
        with mock.patch.object(asyncio, "get_running_loop"):
            with pytest.raises(RuntimeError):
                rest_app.acquire(token="token", token_type="Type")

    def test___enter__(self, rest_app):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            rest_app.__enter__()

    def test___exit__(self, rest_app):
        try:
            rest_app.__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)


@pytest.mark.asyncio
class TestRESTAppAsync:
    async def test_close_when_connector_owner(self, rest_app):
        rest_app._connector_owner = True
        rest_app._connector_factory.close = mock.AsyncMock()
        await rest_app.close()
        rest_app._connector_factory.close.assert_awaited_once_with()

    async def test_close_when_not_connector_owner(self, rest_app):
        rest_app._connector_owner = False
        rest_app._connector_factory.close = mock.AsyncMock()
        await rest_app.close()
        rest_app._connector_factory.close.assert_not_awaited()

    async def test__aenter__(self, rest_app):
        rest_app.close = mock.AsyncMock()
        async with rest_app as returned:
            assert returned is rest_app

    async def test__aexit__(self, rest_app):
        rest_app.close = mock.AsyncMock()
        async with rest_app:
            pass
        rest_app.close.assert_awaited_once_with()


##################
# RESTClientImpl #
##################


@pytest.fixture(scope="module")
def rest_client_class():
    return hikari_test_helpers.mock_class_namespace(rest.RESTClientImpl, slots_=False)


@pytest.fixture()
def rest_client(rest_client_class):
    obj = rest_client_class(
        connector_factory=mock.Mock(),
        connector_owner=False,
        http_settings=mock.Mock(spec=config.HTTPSettings),
        max_rate_limit=float("inf"),
        proxy_settings=mock.Mock(spec=config.ProxySettings),
        token="some_token",
        token_type="tYpe",
        rest_url="https://some.where/api/v3",
        executor=mock.Mock(),
        entity_factory=mock.Mock(),
    )
    obj.buckets = mock.Mock()
    obj.global_rate_limit = mock.Mock()
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
    def test__init__passes_max_rate_limit(self):
        with mock.patch.object(buckets, "RESTBucketManager") as bucket:
            rest.RESTClientImpl(
                connector_factory=mock.Mock(),
                connector_owner=True,
                http_settings=mock.Mock(),
                max_rate_limit=float("inf"),
                proxy_settings=mock.Mock(),
                token=None,
                token_type=None,
                rest_url=None,
                executor=None,
                entity_factory=None,
            )

        bucket.assert_called_once_with(float("inf"))

    def test__init__when_token_is_None_sets_token_to_None(self):
        obj = rest.RESTClientImpl(
            connector_factory=mock.Mock(),
            connector_owner=True,
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

    def test__init__when_token_is_not_None_and_token_type_is_None_generates_token_with_default_type(self):
        obj = rest.RESTClientImpl(
            connector_factory=mock.Mock(),
            connector_owner=True,
            http_settings=mock.Mock(),
            max_rate_limit=float("inf"),
            proxy_settings=mock.Mock(),
            token="some_token",
            token_type=None,
            rest_url=None,
            executor=None,
            entity_factory=None,
        )
        assert obj._token == "Bot some_token"

    def test__init__when_token_and_token_type_is_not_None_generates_token_with_type(self):
        obj = rest.RESTClientImpl(
            connector_factory=mock.Mock(),
            connector_owner=True,
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

    def test__init__when_rest_url_is_None_generates_url_using_default_url(self):
        obj = rest.RESTClientImpl(
            connector_factory=mock.Mock(),
            connector_owner=True,
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
            connector_factory=mock.Mock(),
            connector_owner=True,
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

    def test_http_settings_property(self, rest_client):
        mock_http_settings = object()
        rest_client._http_settings = mock_http_settings
        assert rest_client.http_settings is mock_http_settings

    def test_proxy_settings(self, rest_client):
        mock_proxy_settings = object()
        rest_client._proxy_settings = mock_proxy_settings
        assert rest_client.proxy_settings is mock_proxy_settings

    def test__acquire_client_session_when_None(self, rest_client):
        client_session_mock = object()
        client_session_stub.closed = False
        connector_mock = mock.Mock()
        rest_client._connector_factory.acquire = mock.Mock(return_value=connector_mock)
        rest_client._http_settings.timeouts.total = 10
        rest_client._http_settings.timeouts.acquire_and_connect = 5
        rest_client._http_settings.timeouts.request_socket_read = 4
        rest_client._http_settings.timeouts.request_socket_connect = 1
        rest_client._proxy_settings.trust_env = False
        rest_client._client_session = None

        with mock.patch.object(aiohttp, "ClientSession", return_value=client_session_mock) as client_session:
            assert rest_client._acquire_client_session() is client_session_mock
            assert rest_client._client_session is client_session_mock
            client_session.assert_called_once_with(
                connector=connector_mock,
                connector_owner=False,
                raise_for_status=False,
                timeout=aiohttp.ClientTimeout(total=10, connect=5, sock_read=4, sock_connect=1),
                trust_env=False,
                version=aiohttp.HttpVersion11,
                ws_response_class=aiohttp.ClientWebSocketResponse,
            )

    def test__acquire_client_session_when_not_None_and_open(self, rest_client):
        client_session_mock = mock.Mock()
        client_session_mock.closed = False
        rest_client._client_session = client_session_mock

        assert rest_client._acquire_client_session() is client_session_mock

    def test__acquire_client_session_when_not_None_and_closed(self, rest_client):
        client_session_mock = mock.Mock()
        client_session_mock.closed = True
        rest_client._client_session = client_session_mock

        with pytest.raises(errors.HTTPClientClosedError):
            assert rest_client._acquire_client_session() is client_session_mock

    @pytest.mark.parametrize(
        ("function_input", "expected_output"),
        [
            ((True, True, True), {"parse": ["everyone", "users", "roles"]}),
            ((False, False, False), {"parse": []}),
            ((undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED), {"parse": []}),
            ((undefined.UNDEFINED, True, True), {"parse": ["roles", "users"]}),
            ((False, [123], [456]), {"parse": [], "users": ["123"], "roles": ["456"]}),
            (
                (True, [123, "123", 987], ["213", "456", 456]),
                {"parse": ["everyone"], "users": ["123", "987"], "roles": ["213", "456"]},
            ),
        ],
    )
    def test__generate_allowed_mentions(self, rest_client, function_input, expected_output):
        returned = rest_client._generate_allowed_mentions(*function_input)
        if returned is not undefined.UNDEFINED:
            for k in returned.keys():
                returned[k] = sorted(returned[k])

        if expected_output is not undefined.UNDEFINED:
            for k in expected_output.keys():
                expected_output[k] = sorted(expected_output[k])

        assert returned == expected_output

    @pytest.mark.parametrize(  # noqa: PT014 - Duplicate test cases (false positive)
        ("emoji", "expected_return"),
        [
            (emojis.CustomEmoji(id=123, name="rooYay", is_animated=False), "rooYay:123"),
            ("👌", "👌"),
            ("\N{OK HAND SIGN}", "\N{OK HAND SIGN}"),
            ("<:rooYay:123>", "rooYay:123"),
            ("<a:rooYay:123>", "rooYay:123"),
            ("rooYay:123", "rooYay:123"),
        ],
    )
    def test__transform_emoji_to_url_format(self, rest_client, emoji, expected_return):
        assert rest_client._transform_emoji_to_url_format(emoji) == expected_return

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

    def test_trigger_typing(self, rest_client):
        channel = StubModel(123)
        stub_iterator = mock.Mock()

        with mock.patch.object(special_endpoints, "TypingIndicator", return_value=stub_iterator) as typing_indicator:
            assert rest_client.trigger_typing(channel) == stub_iterator

            typing_indicator.assert_called_once_with(
                request_call=rest_client._request, channel=channel, rest_closed_event=rest_client._closed_event
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
            dict(before=1234, after=1234),
            dict(after=1234, around=1234),
            dict(before=1234, around=1234),
            dict(before=1234, after=1234, around=1234),
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
            returned == stub_iterator

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


@pytest.mark.asyncio
class TestRESTClientImplAsync:
    @pytest.fixture()
    def exit_exception(self):
        class ExitException(Exception):
            ...

        return ExitException

    async def test___aenter__and__aexit__(self, rest_client):
        with mock.patch.object(rest_client, "close") as close:
            async with rest_client as client:
                assert client is rest_client
                close.assert_not_called()

        close.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test__request_when_buckets_not_started(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client.buckets.is_started = False
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock(side_effect=exit_exception)):
            with pytest.raises(exit_exception):
                await rest_client._request(route)

            rest_client.buckets.start.assert_called_once()

    @hikari_test_helpers.timeout()
    async def test__request_when_buckets_started(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        rest_client.buckets.is_started = True
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock(side_effect=exit_exception)):
            with pytest.raises(exit_exception):
                await rest_client._request(route)

            rest_client.buckets.start.assert_not_called()

    @hikari_test_helpers.timeout()
    async def test__request_when__token_is_None(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        rest_client.buckets.is_started = True
        rest_client._token = None
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        rest_client._stringify_http_message = mock.Mock()
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            with pytest.raises(exit_exception):
                await rest_client._request(route)

            _, kwargs = mock_session.request.call_args_list[0]
            assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]

    @hikari_test_helpers.timeout()
    async def test__request_when__token_is_not_None(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        rest_client.buckets.is_started = True
        rest_client._token = "token"
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        rest_client._stringify_http_message = mock.Mock()
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            with pytest.raises(exit_exception):
                await rest_client._request(route)

        _, kwargs = mock_session.request.call_args_list[0]
        assert kwargs["headers"][rest._AUTHORIZATION_HEADER] == "token"

    @hikari_test_helpers.timeout()
    async def test__request_when_no_auth_passed(self, rest_client, exit_exception):
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=exit_exception))
        rest_client.buckets.is_started = True
        rest_client._token = "token"
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        rest_client._stringify_http_message = mock.Mock()
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            with pytest.raises(exit_exception):
                await rest_client._request(route, no_auth=True)

            _, kwargs = mock_session.request.call_args_list[0]
            assert rest._AUTHORIZATION_HEADER not in kwargs["headers"]

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_NO_CONTENT(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        rest_client.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        rest_client._stringify_http_message = mock.Mock()
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            assert (await rest_client._request(route)) is None

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_APPLICATION_JSON(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.OK
            content_type = rest._APPLICATION_JSON
            reason = "cause why not"
            headers = {"HEADER": "value", "HEADER": "value"}

            async def read(self):
                return '{"something": null}'

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        rest_client.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        rest_client._stringify_http_message = mock.Mock()
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            assert (await rest_client._request(route)) == {"something": None}

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_not_JSON(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.IM_USED
            content_type = "text/html"
            reason = "cause why not"
            real_url = "https://some.url"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        rest_client.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        rest_client._stringify_http_message = mock.Mock()
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            with pytest.raises(errors.HTTPError):
                await rest_client._request(route)

    @hikari_test_helpers.timeout()
    async def test__request_when_response_is_not_between_200_and_300(self, rest_client, exit_exception):
        class StubResponse:
            status = http.HTTPStatus.NOT_IMPLEMENTED
            content_type = "text/html"
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        rest_client.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        rest_client._handle_error_response = mock.AsyncMock(side_effect=exit_exception)
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        rest_client._stringify_http_message = mock.Mock()
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            with pytest.raises(exit_exception):
                await rest_client._request(route)

    @hikari_test_helpers.timeout()
    async def test__request_when_response__RetryRequest_gets_handled(self, rest_client, exit_exception):
        class StubResponse:
            status = http.HTTPStatus.USE_PROXY
            content_type = "text/html"
            reason = "cause why not"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(side_effect=[rest_client._RetryRequest, exit_exception]))
        rest_client.buckets.is_started = True
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)
        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
            with pytest.raises(exit_exception):
                await rest_client._request(route)

    @pytest.mark.parametrize("logger_level", [ux.TRACE, ux.TRACE + 10])
    @hikari_test_helpers.timeout()
    async def test__request_logger(self, rest_client, exit_exception, logger_level):
        class StubResponse:
            status = http.HTTPStatus.NO_CONTENT
            headers = {}
            reason = "cause why not"

            async def read(self):
                return None

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        mock_session = mock.AsyncMock(request=mock.AsyncMock(return_value=StubResponse()))
        rest_client.buckets.is_started = True
        rest_client._parse_ratelimits = mock.AsyncMock()
        rest_client._acquire_client_session = mock.Mock(return_value=mock_session)

        with mock.patch.object(
            rest, "_LOGGER", new=mock.Mock(getEffectiveLevel=mock.Mock(return_value=logger_level))
        ) as logger:
            with mock.patch.object(asyncio, "gather", new=mock.AsyncMock()):
                await rest_client._request(route)

        if logger_level > ux.TRACE:
            assert logger.log.call_count == 0
        else:
            assert logger.log.call_count == 2

    async def test__handle_error_response(self, rest_client, exit_exception):
        mock_response = mock.Mock()
        with mock.patch.object(net, "generate_error_response", return_value=exit_exception) as generate_error_response:
            with pytest.raises(exit_exception):
                await rest_client._handle_error_response(mock_response)

            generate_error_response.assert_called_once_with(mock_response)

    async def test__parse_ratelimits_when_not_ratelimited(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.OK
            headers = {rest._DATE_HEADER: "Thu, 02 Jul 2020 20:55:08 GMT"}

            json = mock.AsyncMock()

        response = StubResponse()
        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        await rest_client._parse_ratelimits(route, response)
        response.json.assert_not_called()

    async def test__parse_ratelimits_when_ratelimited(self, rest_client, exit_exception):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {rest._DATE_HEADER: "Thu, 02 Jul 2020 20:55:08 GMT"}

            async def json(self):
                raise exit_exception

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(exit_exception):
            await rest_client._parse_ratelimits(route, StubResponse())

    async def test__parse_ratelimits_when_unexpected_content_type(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = "text/html"
            headers = {rest._DATE_HEADER: "Thu, 02 Jul 2020 20:55:08 GMT"}
            real_url = "https://some.url"

            async def read(self):
                return "this is not json :)"

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(errors.HTTPResponseError):
            await rest_client._parse_ratelimits(route, StubResponse())

    async def test__parse_ratelimits_when_global_ratelimit(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {rest._DATE_HEADER: "Thu, 02 Jul 2020 20:55:08 GMT"}
            real_url = "https://some.url"

            async def json(self):
                return {"global": True, "retry_after": "2"}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(rest_client._RetryRequest):
            await rest_client._parse_ratelimits(route, StubResponse())

        rest_client.global_rate_limit.throttle.assert_called_once_with(0.002)

    async def test__parse_ratelimits_when_remaining_header_under_or_equal_to_0(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {
                rest._DATE_HEADER: "Thu, 02 Jul 2020 20:55:08 GMT",
                rest._X_RATELIMIT_REMAINING_HEADER: "0",
            }
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "2", "global": False}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(rest_client._RetryRequest):
            await rest_client._parse_ratelimits(route, StubResponse())

    async def test__parse_ratelimits_when_retry_after_is_close_enough(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {
                rest._DATE_HEADER: "Thu, 02 Jul 2020 20:55:08 GMT",
                rest._X_RATELIMIT_RESET_AFTER_HEADER: "0.002",
            }
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "2"}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(rest_client._RetryRequest):
            await rest_client._parse_ratelimits(route, StubResponse())

    async def test__parse_ratelimits_when_retry_after_is_not_close_enough(self, rest_client):
        class StubResponse:
            status = http.HTTPStatus.TOO_MANY_REQUESTS
            content_type = rest._APPLICATION_JSON
            headers = {
                rest._DATE_HEADER: "Thu, 02 Jul 2020 20:55:08 GMT",
                rest._X_RATELIMIT_RESET_AFTER_HEADER: "0.002",
            }
            real_url = "https://some.url"

            async def json(self):
                return {"retry_after": "4"}

        route = routes.Route("GET", "/something/{channel}/somewhere").compile(channel=123)
        with pytest.raises(errors.RateLimitedError):
            await rest_client._parse_ratelimits(route, StubResponse())

    async def test_close_when__client_session_is_None(self, rest_client):
        rest_client._client_session = None
        rest_client._connector_factory = mock.AsyncMock()
        rest_client.buckets = mock.Mock()

        await rest_client.close()

        rest_client.buckets.close.assert_called_once()

    async def test_close_when__client_session_is_not_None(self, rest_client):
        rest_client._client_session = mock.AsyncMock()
        rest_client._connector_factory = mock.AsyncMock()
        rest_client.buckets = mock.Mock()

        await rest_client.close()

        rest_client._client_session.close.assert_called_once()
        rest_client.buckets.close.assert_called_once()

    #############
    # Endpoints #
    #############

    async def test_fetch_channel(self, rest_client):
        expected_route = routes.GET_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload"})

        assert await rest_client.fetch_channel(StubModel(123)) == mock_object
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_channel.assert_called_once_with({"payload"})

    async def test_edit_channel(self, rest_client):
        expected_route = routes.PATCH_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload"})
        rest_client._entity_factory.serialize_permission_overwrite = mock.Mock(
            return_value={"type": "member", "allow": 1024, "deny": 8192, "id": "1235431"}
        )
        expected_json = {
            "name": "new name",
            "position": 1,
            "topic": "new topic",
            "nsfw": True,
            "bitrate": 10,
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
            reason="some reason :)",
        )

        assert result == mock_object
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="some reason :)")
        rest_client._entity_factory.deserialize_channel.assert_called_once_with({"payload"})

    async def test_edit_channel_without_optionals(self, rest_client):
        expected_route = routes.PATCH_CHANNEL.compile(channel=123)
        mock_object = mock.Mock()
        rest_client._entity_factory.deserialize_channel = mock.Mock(return_value=mock_object)
        rest_client._request = mock.AsyncMock(return_value={"payload"})

        assert await rest_client.edit_channel(StubModel(123)) == mock_object
        rest_client._request.assert_awaited_once_with(expected_route, json={}, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_channel.assert_called_once_with({"payload"})

    async def test_delete_channel(self, rest_client):
        expected_route = routes.DELETE_CHANNEL.compile(channel=123)
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_channel(StubModel(123))
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_edit_permission_overwrites(self, rest_client):
        target = StubModel(456)
        expected_route = routes.PATCH_CHANNEL_PERMISSIONS.compile(channel=123, overwrite=456)
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
        expected_route = routes.PATCH_CHANNEL_PERMISSIONS.compile(channel=123, overwrite=456)
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
        rest_client._request = mock.AsyncMock()
        expected_json = {
            "max_age": 60,
            "max_uses": 4,
            "temporary": True,
            "unique": True,
            "target_user_id": "456",
            "target_user_type": invites.TargetUserType.STREAM,
        }

        await rest_client.create_invite(
            StubModel(123),
            max_age=datetime.timedelta(minutes=1),
            max_uses=4,
            temporary=True,
            unique=True,
            target_user=StubModel(456),
            target_user_type=invites.TargetUserType.STREAM,
            reason="cause why not :)",
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

        assert await rest_client.fetch_message(StubModel(123), StubModel(456)) == message_obj
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_message.assert_called_once_with({"id": "456"})

    @pytest.mark.skip("TODO")
    async def test_create_message(self, rest_client):
        ...  # TODO: Implement

    async def test_create_message_when_attachment_and_attachments_given(self, rest_client):
        with pytest.raises(ValueError, match="You may only specify one of 'attachment' or 'attachments', not both"):
            await rest_client.create_message(StubModel(123), attachment=object(), attachments=object())

    async def test_create_crossposts(self, rest_client):
        expected_route = routes.POST_CHANNEL_CROSSPOST.compile(channel=444432, message=12353234)
        mock_message = object()
        rest_client._entity_factory.deserialize_message = mock.Mock(return_value=mock_message)
        rest_client._request = mock.AsyncMock(return_value={"id": "93939383883", "content": "foobar"})

        result = await rest_client.create_crossposts(StubModel(444432), StubModel(12353234))

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

        await rest_client.delete_reaction(StubModel(123), StubModel(456), "<:rooYay:123>", StubModel(789))
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
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        returned = await rest_client.create_webhook(
            StubModel(123), "test webhook", avatar="someavatar.png", reason="why not"
        )
        assert returned == webhook

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="why not")
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_create_webhook_without_optionals(self, rest_client):
        webhook = StubModel(456)
        expected_route = routes.POST_CHANNEL_WEBHOOKS.compile(channel=123)
        expected_json = {"name": "test webhook"}
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.create_webhook(StubModel(123), "test webhook") == webhook
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason=undefined.UNDEFINED)
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook(self, rest_client):
        webhook = StubModel(123)
        expected_route = routes.GET_WEBHOOK_WITH_TOKEN.compile(webhook=123, token="token")
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.fetch_webhook(StubModel(123), token="token") == webhook
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)
        rest_client._entity_factory.deserialize_webhook.assert_called_once_with({"id": "456"})

    async def test_fetch_webhook_without_token(self, rest_client):
        webhook = StubModel(123)
        expected_route = routes.GET_WEBHOOK.compile(webhook=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_webhook = mock.Mock(return_value=webhook)

        assert await rest_client.fetch_webhook(StubModel(123)) == webhook
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
        assert returned == webhook

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
        assert returned == webhook

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

        assert await rest_client.edit_webhook(StubModel(123), avatar="someavatar.png") == webhook

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

    async def test_fetch_gateway_url(self, rest_client):
        expected_route = routes.GET_GATEWAY.compile()
        rest_client._request = mock.AsyncMock(return_value={"url": "wss://some.url"})

        assert await rest_client.fetch_gateway_url() == "wss://some.url"
        rest_client._request.assert_awaited_once_with(expected_route, no_auth=True)

    async def test_fetch_gateway_bot(self, rest_client):
        bot = StubModel(123)
        expected_route = routes.GET_GATEWAY_BOT.compile()
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_gateway_bot = mock.Mock(return_value=bot)

        assert await rest_client.fetch_gateway_bot() == bot
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_gateway_bot.assert_called_once_with({"id": "123"})

    async def test_fetch_invite(self, rest_client):
        return_invite = StubModel()
        input_invite = StubModel()
        input_invite.code = "Jx4cNGG"
        expected_route = routes.GET_INVITE.compile(invite_code="Jx4cNGG")
        rest_client._request = mock.AsyncMock(return_value={"code": "Jx4cNGG"})
        rest_client._entity_factory.deserialize_invite = mock.Mock(return_value=return_invite)

        assert await rest_client.fetch_invite(input_invite) == return_invite
        rest_client._request.assert_awaited_once_with(expected_route, query={"with_counts": "true"})
        rest_client._entity_factory.deserialize_invite.assert_called_once_with({"code": "Jx4cNGG"})

    async def test_delete_invite(self, rest_client):
        input_invite = StubModel()
        input_invite.code = "Jx4cNGG"
        expected_route = routes.DELETE_INVITE.compile(invite_code="Jx4cNGG")
        rest_client._request = mock.AsyncMock()

        await rest_client.delete_invite(input_invite)
        rest_client._request.assert_awaited_once_with(expected_route)

    async def test_fetch_my_user(self, rest_client):
        user = StubModel(123)
        expected_route = routes.GET_MY_USER.compile()
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.fetch_my_user() == user
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user(self, rest_client):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username"}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username") == user
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_avatar_is_None(self, rest_client):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "avatar": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username", avatar=None) == user
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_my_user.assert_called_once_with({"id": "123"})

    async def test_edit_my_user_when_avatar_is_file(self, rest_client, file_resource_patch):
        user = StubModel(123)
        expected_route = routes.PATCH_MY_USER.compile()
        expected_json = {"username": "new username", "avatar": "some data"}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_my_user = mock.Mock(return_value=user)

        assert await rest_client.edit_my_user(username="new username", avatar="someavatar.png") == user

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

    async def test_create_dm_channel(self, rest_client):
        dm_channel = StubModel(123)
        expected_route = routes.POST_MY_CHANNELS.compile()
        expected_json = {"recipient_id": "123"}
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_dm = mock.Mock(return_value=dm_channel)

        assert await rest_client.create_dm_channel(StubModel(123)) == dm_channel
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json)
        rest_client._entity_factory.deserialize_dm.assert_called_once_with({"id": "123"})

    async def test_fetch_application(self, rest_client):
        application = StubModel(123)
        expected_route = routes.GET_MY_APPLICATION.compile()
        rest_client._request = mock.AsyncMock(return_value={"id": "123"})
        rest_client._entity_factory.deserialize_application = mock.Mock(return_value=application)

        assert await rest_client.fetch_application() == application
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_application.assert_called_once_with({"id": "123"})

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
        assert returned == member

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

        assert await rest_client.fetch_user(StubModel(123)) == user
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_user.assert_called_once_with({"id": "456"})

    async def test_fetch_emoji(self, rest_client):
        emoji = StubModel(456)
        expected_route = routes.GET_GUILD_EMOJI.compile(emoji=456, guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "456"})
        rest_client._entity_factory.deserialize_known_custom_emoji = mock.Mock(return_value=emoji)

        assert await rest_client.fetch_emoji(StubModel(123), StubModel(456)) == emoji
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
        assert returned == emoji

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
        assert returned == emoji

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

        assert await rest_client.fetch_guild(StubModel(123)) == guild
        rest_client._request.assert_awaited_once_with(expected_route, query=expected_query)
        rest_client._entity_factory.deserialize_rest_guild.assert_called_once_with({"id": "1234"})

    async def test_fetch_guild_preview(self, rest_client):
        guild_preview = StubModel(1234)
        expected_route = routes.GET_GUILD_PREVIEW.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "1234"})
        rest_client._entity_factory.deserialize_guild_preview = mock.Mock(return_value=guild_preview)

        assert await rest_client.fetch_guild_preview(StubModel(123)) == guild_preview
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
            "region": "europe",
            "verification": 3,
            "notifications": 1,
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
        rest_client._request = mock.AsyncMock()

        with mock.patch.object(files, "ensure_resource", side_effect=[icon_resource, splash_resource, banner_resource]):
            await rest_client.edit_guild(
                StubModel(123),
                name="hikari",
                region="europe",
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

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="hikari best")

    async def test_edit_guild_when_images_are_None(self, rest_client):
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {
            "name": "hikari",
            "region": "europe",
            "verification": 3,
            "notifications": 1,
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
        rest_client._request = mock.AsyncMock()

        await rest_client.edit_guild(
            StubModel(123),
            name="hikari",
            region="europe",
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

        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="hikari best")

    async def test_edit_guild_without_optionals(self, rest_client):
        expected_route = routes.PATCH_GUILD.compile(guild=123)
        expected_json = {}
        rest_client._request = mock.AsyncMock()

        await rest_client.edit_guild(StubModel(123))
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
        channel = StubModel(456)
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
        assert returned == channel
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
        channel = StubModel(456)
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
        assert returned == channel
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
        channel = StubModel(456)
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
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
        )
        assert returned == channel
        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_VOICE,
            position=1,
            user_limit=60,
            bitrate=64,
            permission_overwrites=[overwrite1, overwrite2],
            category=category_channel,
            reason="because we need one",
        )

    async def test_create_guild_category(self, rest_client):
        guild = StubModel(123)
        category = StubModel(456)
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
        assert returned == category
        rest_client._create_guild_channel.assert_awaited_once_with(
            guild,
            "general",
            channels.ChannelType.GUILD_CATEGORY,
            position=1,
            permission_overwrites=[overwrite1, overwrite2],
            reason="because we need one",
        )

    async def test__create_guild_channel(self, rest_client):
        channel = StubModel(456)
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
            category=StubModel(321),
            reason="we have got the power",
        )
        assert returned == channel
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

    async def test_edit_member(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        expected_json = {"nick": "test", "roles": ["654", "321"], "mute": True, "deaf": False, "channel_id": "987"}
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        await rest_client.edit_member(
            StubModel(123),
            StubModel(456),
            nick="test",
            roles=[StubModel(654), StubModel(321)],
            mute=True,
            deaf=False,
            voice_channel=StubModel(987),
            reason="because i can",
        )
        rest_client._request.assert_awaited_once_with(expected_route, json=expected_json, reason="because i can")

    async def test_edit_member_when_voice_channel_is_None(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        expected_json = {"nick": "test", "roles": ["654", "321"], "mute": True, "deaf": False, "channel_id": None}
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        await rest_client.edit_member(
            StubModel(123),
            StubModel(456),
            nick="test",
            roles=[StubModel(654), StubModel(321)],
            mute=True,
            deaf=False,
            voice_channel=None,
            reason="because i can",
        )
        rest_client._request.assert_awaited_once_with(
            expected_route,
            json=expected_json,
            reason="because i can",
        )

    async def test_edit_member_without_optionals(self, rest_client):
        expected_route = routes.PATCH_GUILD_MEMBER.compile(guild=123, user=456)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})

        await rest_client.edit_member(StubModel(123), StubModel(456))
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
        assert returned == role
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
        assert returned == role
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

        assert await rest_client.fetch_integrations(StubModel(123)) == [integration1, integration2]
        rest_client._request.assert_awaited_once_with(expected_route)
        assert rest_client._entity_factory.deserialize_integration.call_count == 2
        rest_client._entity_factory.deserialize_integration.assert_has_calls(
            [mock.call({"id": "456"}), mock.call({"id": "789"})]
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
        assert returned == widget
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
        assert returned == widget
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

    async def test_fetch_vanity_url(self, rest_client):
        vanity_url = StubModel(789)
        expected_route = routes.GET_GUILD_VANITY_URL.compile(guild=123)
        rest_client._request = mock.AsyncMock(return_value={"id": "789"})
        rest_client._entity_factory.deserialize_vanity_url = mock.Mock(return_value=vanity_url)

        assert await rest_client.fetch_vanity_url(StubModel(123)) == vanity_url
        rest_client._request.assert_awaited_once_with(expected_route)
        rest_client._entity_factory.deserialize_vanity_url.assert_called_once_with({"id": "789"})
