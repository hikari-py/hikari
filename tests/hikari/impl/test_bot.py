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

import mock
import pytest

from hikari import config
from hikari import errors
from hikari.impl import bot as bot_impl
from hikari.impl import cache as cache_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import event_manager as event_manager_impl
from hikari.impl import rest as rest_impl
from hikari.impl import voice as voice_impl
from hikari.internal import aio
from hikari.internal import ux


class TestBotApp:
    @pytest.fixture()
    def cache(self):
        return mock.Mock()

    @pytest.fixture()
    def entity_factory(self):
        return mock.Mock()

    @pytest.fixture()
    def event_factory(self):
        return mock.Mock()

    @pytest.fixture()
    def event_manager(self):
        return mock.Mock()

    @pytest.fixture()
    def rest(self):
        return mock.Mock()

    @pytest.fixture()
    def voice(self):
        return mock.Mock()

    @pytest.fixture()
    def executor(self):
        return mock.Mock()

    @pytest.fixture()
    def intents(self):
        return mock.Mock()

    @pytest.fixture()
    def proxy_settings(self):
        return mock.Mock()

    @pytest.fixture()
    def http_settings(self):
        return mock.Mock()

    @pytest.fixture()
    def bot(
        self,
        cache,
        entity_factory,
        event_factory,
        event_manager,
        rest,
        voice,
        executor,
        intents,
        proxy_settings,
        http_settings,
    ):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(cache_impl, "CacheImpl", return_value=cache))
        stack.enter_context(mock.patch.object(entity_factory_impl, "EntityFactoryImpl", return_value=entity_factory))
        stack.enter_context(mock.patch.object(event_factory_impl, "EventFactoryImpl", return_value=event_factory))
        stack.enter_context(mock.patch.object(event_manager_impl, "EventManagerImpl", return_value=event_manager))
        stack.enter_context(mock.patch.object(voice_impl, "VoiceComponentImpl", return_value=voice))
        stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl", return_value=rest))
        stack.enter_context(mock.patch.object(rest_impl, "BasicLazyCachedTCPConnectorFactory"))
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(bot_impl.BotApp, "print_banner"))

        with stack:
            return bot_impl.BotApp(
                "token", executor=executor, http_settings=http_settings, proxy_settings=proxy_settings, intents=intents
            )

    def test_init(self):
        stack = contextlib.ExitStack()
        cache = stack.enter_context(mock.patch.object(cache_impl, "CacheImpl"))
        entity_factory = stack.enter_context(mock.patch.object(entity_factory_impl, "EntityFactoryImpl"))
        event_factory = stack.enter_context(mock.patch.object(event_factory_impl, "EventFactoryImpl"))
        event_manager = stack.enter_context(mock.patch.object(event_manager_impl, "EventManagerImpl"))
        voice = stack.enter_context(mock.patch.object(voice_impl, "VoiceComponentImpl"))
        rest = stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl"))
        connector_factory = stack.enter_context(mock.patch.object(rest_impl, "BasicLazyCachedTCPConnectorFactory"))
        init_logging = stack.enter_context(mock.patch.object(ux, "init_logging"))
        print_banner = stack.enter_context(mock.patch.object(bot_impl.BotApp, "print_banner"))
        executor = object()
        cache_settings = object()
        http_settings = object()
        proxy_settings = object()
        intents = object()

        with stack:
            bot = bot_impl.BotApp(
                "token",
                allow_color=False,
                banner="testing",
                executor=executor,
                force_color=True,
                cache_settings=cache_settings,
                http_settings=http_settings,
                intents=intents,
                logs="DEBUG",
                max_rate_limit=200,
                proxy_settings=proxy_settings,
                rest_url="somewhere.com",
            )

        assert bot._http_settings is http_settings
        assert bot._proxy_settings is proxy_settings
        assert bot._cache is cache.return_value
        cache.assert_called_once_with(bot, cache_settings)
        assert bot._event_manager is event_manager.return_value
        event_manager.assert_called_once_with(bot, cache=cache.return_value)
        assert bot._entity_factory is entity_factory.return_value
        entity_factory.assert_called_once_with(bot)
        assert bot._event_factory is event_factory.return_value
        event_factory.assert_called_once_with(bot)
        assert bot._voice is voice.return_value
        voice.assert_called_once_with(bot)
        assert bot._rest is rest.return_value
        rest.assert_called_once_with(
            connector_factory=connector_factory.return_value,
            connector_owner=True,
            entity_factory=bot._entity_factory,
            executor=executor,
            http_settings=bot._http_settings,
            max_rate_limit=200,
            proxy_settings=bot._proxy_settings,
            rest_url="somewhere.com",
            token="token",
        )
        connector_factory.assert_called_once_with(bot._http_settings)

        init_logging.assert_called_once_with("DEBUG", False, True)
        print_banner.assert_called_once_with("testing", False, True)

    def test_init_when_no_settings(self):
        stack = contextlib.ExitStack()
        cache = stack.enter_context(mock.patch.object(cache_impl, "CacheImpl"))
        stack.enter_context(mock.patch.object(entity_factory_impl, "EntityFactoryImpl"))
        stack.enter_context(mock.patch.object(event_factory_impl, "EventFactoryImpl"))
        stack.enter_context(mock.patch.object(event_manager_impl, "EventManagerImpl"))
        stack.enter_context(mock.patch.object(voice_impl, "VoiceComponentImpl"))
        stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl"))
        stack.enter_context(mock.patch.object(rest_impl, "BasicLazyCachedTCPConnectorFactory"))
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(bot_impl.BotApp, "print_banner"))
        http_settings = stack.enter_context(mock.patch.object(config, "HTTPSettings"))
        proxy_settings = stack.enter_context(mock.patch.object(config, "ProxySettings"))
        cache_settings = stack.enter_context(mock.patch.object(config, "CacheSettings"))

        with stack:
            bot = bot_impl.BotApp(
                "token",
                cache_settings=None,
                http_settings=None,
                proxy_settings=None,
            )

        assert bot._http_settings is http_settings.return_value
        http_settings.assert_called_once_with()
        assert bot._proxy_settings is proxy_settings.return_value
        proxy_settings.assert_called_once_with()
        cache.assert_called_once_with(bot, cache_settings.return_value)
        cache_settings.assert_called_once_with()

    def test_cache(self, bot, cache):
        assert bot.cache is cache

    def test_event_manager(self, bot, event_manager):
        assert bot.event_manager is event_manager

    def test_entity_factory(self, bot, entity_factory):
        assert bot.entity_factory is entity_factory

    def test_event_factory(self, bot, event_factory):
        assert bot.event_factory is event_factory

    def test_executor(self, bot, executor):
        assert bot.executor is executor

    def test_heartbeat_latencies(self, bot):
        bot._shards = {
            0: mock.Mock(id=0, heartbeat_latency=96),
            1: mock.Mock(id=1, heartbeat_latency=123),
            2: mock.Mock(id=2, heartbeat_latency=456),
        }

        assert bot.heartbeat_latencies == {0: 96, 1: 123, 2: 456}

    def test_heartbeat_latency(self, bot):
        bot._shards = {
            0: mock.Mock(heartbeat_latency=96),
            1: mock.Mock(heartbeat_latency=123),
            2: mock.Mock(heartbeat_latency=float("nan")),
        }

        assert bot.heartbeat_latency == 109.5

    def test_http_settings(self, bot, http_settings):
        assert bot.http_settings is http_settings

    def test_intents(self, bot, intents):
        assert bot.intents is intents

    def test_me(self, bot, cache):
        assert bot.me is cache.get_me.return_value

    def test_proxy_settings(self, bot, proxy_settings):
        assert bot.proxy_settings is proxy_settings

    def test_shard_count_when_no_shards(self, bot):
        bot._shards = {}

        assert bot.shard_count == 0

    def test_shard_count(self, bot):
        bot._shards = {0: mock.Mock(shard_count=96), 1: mock.Mock(shard_count=123)}

        assert bot.shard_count == 96

    def test_voice(self, bot, voice):
        assert bot.voice is voice

    def test_rest(self, bot, rest):
        assert bot.rest is rest

    def test_is_alive(self, bot):
        bot._is_alive = True

        assert bot.is_alive is True

    def test_check_if_alive_when_False(self, bot):
        bot._is_alive = False

        with pytest.raises(errors.ComponentNotRunningError):
            bot._check_if_alive()

    def test_check_if_alive(self, bot):
        bot._is_alive = True

        bot._check_if_alive()

    @pytest.mark.asyncio
    async def test_close_when_not_force(self, bot, event_manager):
        bot._closing_event = mock.Mock(is_set=mock.Mock(return_value=True))
        bot._closed = False
        bot._is_alive = True

        await bot.close(force=False)

        bot._closing_event.set.assert_called_once_with()
        assert bot._closed is False
        assert bot._is_alive is True

    @pytest.mark.asyncio
    async def test_close_when_already_closed(self, bot, event_manager):
        bot._closing_event = mock.Mock(is_set=mock.Mock(return_value=True))
        bot._closed = True
        bot._is_alive = True

        await bot.close(force=True)

        bot._closing_event.set.assert_called_once_with()
        assert bot._closed is True
        assert bot._is_alive is True

    @pytest.mark.asyncio
    async def test_close_when_force(self, bot, event_manager, event_factory, rest, voice, cache):
        def null_call(arg):
            return arg

        class AwaitMock:
            def __init__(self, error=None):
                self._awaited_count = 0
                self._error = error

            def __await__(self):
                if False:
                    yield  # Turns it into a generator

                self._awaited_count += 1

                if self._error:
                    raise self._error

            def __call__(self):
                return self

            def assert_awaited_once(self):
                assert self._awaited_count == 1

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(asyncio, "as_completed", side_effect=null_call))
        ensure_future = stack.enter_context(mock.patch.object(asyncio, "ensure_future", side_effect=null_call))
        get_running_loop = stack.enter_context(mock.patch.object(asyncio, "get_running_loop"))
        all_of = stack.enter_context(mock.patch.object(aio, "all_of", new=mock.AsyncMock()))

        event_manager.dispatch = mock.AsyncMock()
        rest.close = AwaitMock()
        voice.close = AwaitMock()
        bot._closing_event = mock.Mock(is_set=mock.Mock(return_value=False))
        bot._closed = False
        bot._is_alive = True
        error = RuntimeError()
        shard0 = mock.Mock(id=0, close=AwaitMock())
        shard1 = mock.Mock(id=1, close=AwaitMock(error=error))
        shard2 = mock.Mock(id=2, close=AwaitMock())
        bot._shards = {0: shard0, 1: shard1, 2: shard2}

        with stack:
            await bot.close(force=True)

        # Closing event and args
        bot._closing_event.set.assert_called_once_with()
        assert bot._closed is True
        assert bot._is_alive is False

        # Closing components
        ensure_future.assert_has_calls(
            [
                mock.call(rest.close()),
                mock.call(voice.close()),
                mock.call(shard0.close()),
                mock.call(shard1.close()),
                mock.call(shard2.close()),
            ],
            any_order=False,
        )

        rest.close.assert_awaited_once()
        voice.close.assert_awaited_once()
        shard0.close.assert_awaited_once()
        shard1.close.assert_awaited_once()
        shard2.close.assert_awaited_once()

        # Error handling
        get_running_loop.assert_called_once_with()
        get_running_loop.return_value.call_exception_handler.assert_called_once_with(
            {
                "message": "shard 1 raised an exception during shutdown",
                "future": shard1.close(),
                "exception": error,
            }
        )

        # Joining shards
        all_of.assert_awaited_once_with(*(shard0.join(), shard1.join(), shard2.join()), timeout=3)

        # Clear out maps
        assert bot._shards == {}
        cache.clear.assert_called_once_with()

        # Dispatching events in the right order
        event_manager.dispatch.assert_has_calls(
            [
                mock.call(event_factory.deserialize_stopping_event.return_value),
                mock.call(event_factory.deserialize_stopped_event.return_value),
            ],
            any_order=False,
        )
