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
import signal
import sys
import warnings

import mock
import pytest

from hikari import applications
from hikari import config
from hikari import errors
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari.impl import bot as bot_impl
from hikari.impl import cache as cache_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import event_manager as event_manager_impl
from hikari.impl import rest as rest_impl
from hikari.impl import shard as shard_impl
from hikari.impl import voice as voice_impl
from hikari.internal import aio
from hikari.internal import ux


class TestGatewayBot:
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
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "print_banner"))

        with stack:
            return bot_impl.GatewayBot(
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
        init_logging = stack.enter_context(mock.patch.object(ux, "init_logging"))
        print_banner = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "print_banner"))
        executor = object()
        cache_settings = object()
        http_settings = object()
        proxy_settings = object()
        intents = object()

        with stack:
            bot = bot_impl.GatewayBot(
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
        event_manager.assert_called_once_with(event_factory.return_value, intents, cache=cache.return_value)
        assert bot._entity_factory is entity_factory.return_value
        entity_factory.assert_called_once_with(bot)
        assert bot._event_factory is event_factory.return_value
        event_factory.assert_called_once_with(bot)
        assert bot._voice is voice.return_value
        voice.assert_called_once_with(bot)
        assert bot._rest is rest.return_value
        rest.assert_called_once_with(
            cache=bot._cache,
            entity_factory=bot._entity_factory,
            executor=executor,
            http_settings=bot._http_settings,
            max_rate_limit=200,
            proxy_settings=bot._proxy_settings,
            rest_url="somewhere.com",
            token="token",
            token_type=applications.TokenType.BOT,
        )

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
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "print_banner"))
        http_settings = stack.enter_context(mock.patch.object(config, "HTTPSettings"))
        proxy_settings = stack.enter_context(mock.patch.object(config, "ProxySettings"))
        cache_settings = stack.enter_context(mock.patch.object(config, "CacheSettings"))

        with stack:
            bot = bot_impl.GatewayBot("token", cache_settings=None, http_settings=None, proxy_settings=None)

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

    def test_get_me(self, bot, cache):
        assert bot.get_me() is cache.get_me.return_value

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

        with pytest.raises(errors.ComponentStateConflictError):
            bot._check_if_alive()

    def test_check_if_alive(self, bot):
        bot._is_alive = True

        bot._check_if_alive()

    @pytest.mark.asyncio()
    async def test_close_when_already_closed(self, bot, event_manager):
        bot._closing_event = None
        bot._closed_event = None
        bot._is_alive = True

        await bot.close()

        assert bot._is_alive is True

    @pytest.mark.asyncio()
    async def test_close_when_already_closing(self, bot, event_manager):
        bot._closing_event = object()
        bot._closed_event = mock.AsyncMock()
        bot._is_alive = True

        await bot.close()

        bot._closed_event.wait.assert_awaited_once_with()
        assert bot._is_alive is True

    @pytest.mark.asyncio()
    async def test_close(self, bot, event_manager, event_factory, rest, voice, cache):
        def null_call(arg):
            return arg

        class AwaitableMock:
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
        new_event = stack.enter_context(mock.patch.object(asyncio, "Event"))
        mock_future = mock.Mock()
        get_running_loop.return_value.create_future.return_value = mock_future

        event_manager.dispatch = mock.AsyncMock()
        rest.close = AwaitableMock()
        voice.close = AwaitableMock()
        bot._closing_event = closing_event = mock.Mock(is_set=mock.Mock(return_value=False))
        bot._closed_event = None
        bot._is_alive = True
        error = RuntimeError()
        shard0 = mock.Mock(id=0, close=AwaitableMock())
        shard1 = mock.Mock(id=1, close=AwaitableMock(error))
        shard2 = mock.Mock(id=2, close=AwaitableMock())
        bot._shards = {0: shard0, 1: shard1, 2: shard2}

        with stack:
            await bot.close()

        # Events and args
        closing_event.set.assert_called_once_with()
        assert bot._closing_event is None
        new_event.return_value.set.assert_called_once_with()
        assert bot._closed_event is None
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

    def test_dispatch(self, bot, event_manager):
        event = object()

        assert bot.dispatch(event) is event_manager.dispatch.return_value

        event_manager.dispatch.assert_called_once_with(event)

    def test_get_listeners(self, bot, event_manager):
        event = object()

        assert bot.get_listeners(event, polymorphic=False) is event_manager.get_listeners.return_value

        event_manager.get_listeners.assert_called_once_with(event, polymorphic=False)

    @pytest.mark.asyncio()
    async def test_join_when_not_until_close(self, bot, event_manager):
        shard0 = mock.Mock()
        shard1 = mock.Mock()
        shard2 = mock.Mock()
        bot._shards = {0: shard0, 1: shard1, 2: shard2}

        with mock.patch.object(aio, "first_completed") as first_completed:
            with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
                await bot.join(until_close=False)

        check_if_alive.assert_called_once_with()
        first_completed.assert_awaited_once_with(
            *(shard0.join.return_value, shard1.join.return_value, shard2.join.return_value)
        )

    @pytest.mark.asyncio()
    async def test_join_when_until_close(self, bot):
        shard0 = mock.Mock()
        shard1 = mock.Mock()
        shard2 = mock.Mock()
        bot._shards = {0: shard0, 1: shard1, 2: shard2}
        bot._closing_event = mock.Mock()

        with mock.patch.object(aio, "first_completed") as first_completed:
            with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
                await bot.join(until_close=True)

        check_if_alive.assert_called_once_with()
        first_completed.assert_awaited_once_with(
            *(
                shard0.join.return_value,
                shard1.join.return_value,
                shard2.join.return_value,
                bot._closing_event.wait(),
            )
        )

    def test_listen(self, bot, event_manager):
        event = object()

        assert bot.listen(event) is event_manager.listen.return_value

        event_manager.listen.assert_called_once_with(event)

    def test_print_banner(self, bot):
        with mock.patch.object(ux, "print_banner") as print_banner:
            bot.print_banner("testing", False, True)

        print_banner.assert_called_once_with("testing", False, True)

    def test_run_when_already_running(self, bot):
        bot._is_alive = True

        with pytest.raises(errors.ComponentStateConflictError):
            bot.run()

    def test_run_when_shard_ids_specified_without_shard_count(self, bot):
        with pytest.raises(TypeError, match=r"'shard_ids' must be passed with 'shard_count'"):
            bot.run(shard_ids={1})

    def test_run_with_asyncio_debug(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "close", new=mock.Mock()))
        loop = stack.enter_context(mock.patch.object(aio, "get_or_make_loop")).return_value

        with stack:
            bot.run(close_loop=False, asyncio_debug=True)

        loop.set_debug.assert_called_once_with(True)

    def test_run_with_coroutine_tracking_depth(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "close", new=mock.Mock()))
        stack.enter_context(mock.patch.object(aio, "get_or_make_loop"))
        coroutine_tracking_depth = stack.enter_context(
            mock.patch.object(sys, "set_coroutine_origin_tracking_depth", side_effect=AttributeError)
        )

        with stack:
            bot.run(close_loop=False, coroutine_tracking_depth=100)

        coroutine_tracking_depth.assert_called_once_with(100)

    def test_run_with_enable_signal_handlers(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "close", new=mock.Mock()))
        stack.enter_context(mock.patch.object(aio, "get_or_make_loop"))
        signal_function = stack.enter_context(
            mock.patch.object(signal, "signal", side_effect=[None, AttributeError, None, AttributeError])
        )

        with stack:
            bot.run(close_loop=False, enable_signal_handlers=True)

        # We have these twice because they will also be called on cleanup too
        expected_signals = [
            signal.Signals.SIGINT,
            signal.Signals.SIGTERM,
            signal.Signals.SIGINT,
            signal.Signals.SIGTERM,
        ]
        assert [signal_function.call_args_list[i][0][0] for i in range(signal_function.call_count)] == expected_signals

    @pytest.mark.parametrize("logging", [True, False])
    def test_run_with_propagate_interrupts(self, bot, logging):
        def raise_signal(*args, **kwargs):
            signal.raise_signal(signal.Signals.SIGTERM)

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=raise_signal))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "close", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl, "_LOGGER", isEnabledFor=mock.Mock(return_value=logging)))
        loop = stack.enter_context(mock.patch.object(aio, "get_or_make_loop")).return_value
        set_close_flag = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "_set_close_flag", new=mock.Mock()))
        run_coroutine_threadsafe = stack.enter_context(mock.patch.object(asyncio, "run_coroutine_threadsafe"))

        with stack:
            with pytest.raises(errors.HikariInterrupt, match=rf"(15, '{signal.strsignal(signal.Signals.SIGTERM)}')"):
                bot.run(close_loop=False, propagate_interrupts=True)

        run_coroutine_threadsafe.assert_called_once_with(set_close_flag.return_value, loop)
        set_close_flag.assert_called_once_with(signal.strsignal(signal.Signals.SIGTERM), 15)

    def test_run_with_close_passed_executor(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "close", new=mock.Mock()))
        stack.enter_context(mock.patch.object(aio, "get_or_make_loop"))
        executor = mock.Mock()
        bot._executor = executor

        with stack:
            bot.run(close_loop=False, close_passed_executor=True)

        executor.shutdown.assert_called_once_with(wait=True)
        assert bot._executor is None

    def test_run_with_close_loop(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "close", new=mock.Mock()))
        destroy_loop = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "_destroy_loop"))
        loop = stack.enter_context(mock.patch.object(aio, "get_or_make_loop")).return_value

        with stack:
            bot.run(close_loop=True)

        destroy_loop.assert_called_once_with(loop)

    def test_run(self, bot):
        activity = object()
        afk = object()
        check_for_updates = object()
        idle_since = object()
        ignore_session_start_limit = object()
        large_threshold = object()
        shard_ids = object()
        shard_count = object()
        status = object()

        stack = contextlib.ExitStack()
        start_function = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        join_function = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        close_function = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "close", new=mock.Mock()))
        loop = stack.enter_context(mock.patch.object(aio, "get_or_make_loop")).return_value

        with stack:
            bot.run(
                activity=activity,
                afk=afk,
                asyncio_debug=False,
                check_for_updates=check_for_updates,
                close_passed_executor=False,
                close_loop=False,
                coroutine_tracking_depth=None,
                enable_signal_handlers=False,
                idle_since=idle_since,
                ignore_session_start_limit=ignore_session_start_limit,
                large_threshold=large_threshold,
                propagate_interrupts=False,
                shard_ids=shard_ids,
                shard_count=shard_count,
                status=status,
            )

        loop.run_until_complete.assert_has_calls(
            [
                mock.call(start_function.return_value),
                mock.call(join_function.return_value),
                mock.call(close_function.return_value),
            ]
        )
        start_function.assert_called_once_with(
            activity=activity,
            afk=afk,
            check_for_updates=check_for_updates,
            idle_since=idle_since,
            ignore_session_start_limit=ignore_session_start_limit,
            large_threshold=large_threshold,
            shard_ids=shard_ids,
            shard_count=shard_count,
            status=status,
        )

    @pytest.mark.asyncio()
    async def test_start_when_shard_ids_specified_without_shard_count(self, bot):
        with pytest.raises(TypeError, match=r"'shard_ids' must be passed with 'shard_count'"):
            await bot.start(shard_ids={1})

    @pytest.mark.asyncio()
    async def test_start_when_already_running(self, bot):
        bot._is_alive = True

        with pytest.raises(errors.ComponentStateConflictError):
            await bot.start()

    @pytest.mark.skip("TODO")
    def test_start(self, bot):
        ...

    def test_stream(self, bot):
        event_type = object()

        with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
            bot.stream(event_type, timeout=100, limit=400)

        check_if_alive.assert_called_once_with()
        bot._event_manager.stream.assert_called_once_with(event_type, timeout=100, limit=400)

    def test_subscribe(self, bot):
        event_type = object()
        callback = object()

        bot.subscribe(event_type, callback)

        bot._event_manager.subscribe.assert_called_once_with(event_type, callback)

    def test_unsubscribe(self, bot):
        event_type = object()
        callback = object()

        bot.unsubscribe(event_type, callback)

        bot._event_manager.unsubscribe.assert_called_once_with(event_type, callback)

    @pytest.mark.asyncio()
    async def test_wait_for(self, bot):
        event_type = object()
        predicate = object()
        bot._event_manager.wait_for = mock.AsyncMock()

        with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
            await bot.wait_for(event_type, timeout=100, predicate=predicate)

        check_if_alive.assert_called_once_with()
        bot._event_manager.wait_for.assert_awaited_once_with(event_type, timeout=100, predicate=predicate)

    def test_get_shard_when_not_present(self, bot):
        shard = mock.Mock(shard_count=96)
        bot._shards = {96: shard}

        with mock.patch.object(snowflakes, "calculate_shard_id", return_value=0) as calculate_shard_id:
            with pytest.raises(
                RuntimeError, match=r"Guild 702763150025556029 isn't covered by any of the shards in this client"
            ):
                bot._get_shard(702763150025556029)

        calculate_shard_id.assert_called_once_with(96, 702763150025556029)

    def test_get_shard(self, bot):
        shard = mock.Mock(shard_count=96)
        bot._shards = {96: shard}

        with mock.patch.object(snowflakes, "calculate_shard_id", return_value=96) as calculate_shard_id:
            assert bot._get_shard(702763150025556029) is shard

        calculate_shard_id.assert_called_once_with(96, 702763150025556029)

    @pytest.mark.asyncio()
    async def test_update_presence(self, bot):
        status = object()
        activity = object()
        idle_since = object()
        afk = object()

        shard0 = mock.Mock()
        shard1 = mock.Mock()
        shard2 = mock.Mock()
        bot._shards = {0: shard0, 1: shard1, 2: shard2}

        with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
            with mock.patch.object(aio, "all_of") as all_of:
                with mock.patch.object(bot_impl.GatewayBot, "_validate_activity") as validate_activity:
                    await bot.update_presence(status=status, activity=activity, idle_since=idle_since, afk=afk)

        check_if_alive.assert_called_once_with()
        validate_activity.assert_called_once_with(activity)
        all_of.assert_awaited_once_with(
            shard0.update_presence.return_value,
            shard1.update_presence.return_value,
            shard2.update_presence.return_value,
        )
        shard0.update_presence.assert_called_once_with(status=status, activity=activity, idle_since=idle_since, afk=afk)
        shard1.update_presence.assert_called_once_with(status=status, activity=activity, idle_since=idle_since, afk=afk)
        shard2.update_presence.assert_called_once_with(status=status, activity=activity, idle_since=idle_since, afk=afk)

    @pytest.mark.asyncio()
    async def test_update_voice_state(self, bot):
        shard = mock.Mock()
        shard.update_voice_state = mock.AsyncMock()

        with mock.patch.object(bot_impl.GatewayBot, "_get_shard", return_value=shard) as get_shard:
            with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
                await bot.update_voice_state(115590097100865541, 123, self_mute=True, self_deaf=False)

        check_if_alive.assert_called_once_with()
        get_shard.assert_called_once_with(115590097100865541)
        shard.update_voice_state.assert_awaited_once_with(
            guild=115590097100865541, channel=123, self_mute=True, self_deaf=False
        )

    @pytest.mark.asyncio()
    async def test_request_guild_members(self, bot):
        shard = mock.Mock(shard_count=3)
        shard.request_guild_members = mock.AsyncMock()

        with mock.patch.object(bot_impl.GatewayBot, "_get_shard", return_value=shard) as get_shard:
            with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
                await bot.request_guild_members(
                    115590097100865541,
                    include_presences=True,
                    query="indeed",
                    limit=42,
                    users=[123],
                    nonce="NONCE",
                )

        check_if_alive.assert_called_once_with()
        get_shard.assert_called_once_with(115590097100865541)
        shard.request_guild_members.assert_awaited_once_with(
            guild=115590097100865541,
            include_presences=True,
            query="indeed",
            limit=42,
            users=[123],
            nonce="NONCE",
        )

    @pytest.mark.asyncio()
    async def test_set_close_flag(self, bot):
        with mock.patch.object(bot_impl.GatewayBot, "close") as close:
            await bot._set_close_flag("Terminated", 15)

        close.assert_awaited_once_with()

    @pytest.mark.asyncio()
    async def test_start_one_shard(self, bot):
        activity = object()
        status = object()
        bot._shards = {}
        closing_event = mock.Mock()
        shard = mock.Mock()
        shard_obj = shard.return_value
        shard_obj.is_alive = True

        with mock.patch.object(aio, "first_completed", new=mock.AsyncMock()) as first_completed:
            with mock.patch.object(shard_impl, "GatewayShardImpl", new=shard):
                returned = await bot._start_one_shard(
                    activity=activity,
                    afk=True,
                    idle_since=None,
                    status=status,
                    large_threshold=1000,
                    shard_id=1,
                    shard_count=3,
                    url="https://some.website",
                    closing_event=closing_event,
                )

                assert returned is shard_obj

        shard.assert_called_once_with(
            http_settings=bot._http_settings,
            proxy_settings=bot._proxy_settings,
            event_manager=bot._event_manager,
            event_factory=bot._event_factory,
            intents=bot._intents,
            initial_activity=activity,
            initial_is_afk=True,
            initial_idle_since=None,
            initial_status=status,
            large_threshold=1000,
            shard_id=1,
            shard_count=3,
            token=bot._token,
            url="https://some.website",
        )
        assert bot._shards == {1: shard_obj}
        first_completed.assert_awaited_once_with(shard_obj.start.return_value, closing_event.wait.return_value)

    @pytest.mark.asyncio()
    async def test_start_one_shard_when_not_alive(self, bot):
        activity = object()
        status = object()
        bot._closing_event = mock.Mock()
        shard = mock.Mock()
        shard_obj = shard.return_value
        shard_obj.is_alive = False

        with mock.patch.object(aio, "first_completed", new=mock.AsyncMock()):
            with mock.patch.object(shard_impl, "GatewayShardImpl", new=shard):
                with pytest.raises(errors.GatewayError, match=r"shard 1 shut down immediately when starting"):
                    await bot._start_one_shard(
                        activity=activity,
                        afk=True,
                        idle_since=None,
                        status=status,
                        large_threshold=1000,
                        shard_id=1,
                        shard_count=3,
                        url="https://some.website",
                        closing_event=bot._closing_event,
                    )

    @pytest.mark.parametrize("activity", [undefined.UNDEFINED, None])
    def test_validate_activity_when_no_activity(self, bot, activity):
        with mock.patch.object(warnings, "warn") as warn:
            bot._validate_activity(activity)

        warn.assert_not_called()

    def test_validate_activity_when_type_is_custom(self, bot):
        activity = presences.Activity(name="test", type=presences.ActivityType.CUSTOM)

        with mock.patch.object(warnings, "warn") as warn:
            bot._validate_activity(activity)

        warn.assert_called_once_with(
            "The CUSTOM activity type is not supported by bots at the time of writing, and may therefore not have "
            "any effect if used.",
            category=errors.HikariWarning,
            stacklevel=3,
        )

    def test_validate_activity_when_type_is_streaming_but_no_url(self, bot):
        activity = presences.Activity(name="test", url=None, type=presences.ActivityType.STREAMING)

        with mock.patch.object(warnings, "warn") as warn:
            bot._validate_activity(activity)

        warn.assert_called_once_with(
            "The STREAMING activity type requires a 'url' parameter pointing to a valid Twitch or YouTube video "
            "URL to be specified on the activity for the presence update to have any effect.",
            category=errors.HikariWarning,
            stacklevel=3,
        )

    def test_validate_activity_when_no_warning(self, bot):
        activity = presences.Activity(name="test", type=presences.ActivityType.PLAYING)

        with mock.patch.object(warnings, "warn") as warn:
            bot._validate_activity(activity)

        warn.assert_not_called()
