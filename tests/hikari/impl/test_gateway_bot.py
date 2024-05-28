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
import asyncio
import contextlib
import sys
import warnings

import mock
import pytest

from hikari import applications
from hikari import errors
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari.impl import cache as cache_impl
from hikari.impl import config
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import event_manager as event_manager_impl
from hikari.impl import gateway_bot as bot_impl
from hikari.impl import rest as rest_impl
from hikari.impl import shard as shard_impl
from hikari.impl import voice as voice_impl
from hikari.internal import aio
from hikari.internal import signals
from hikari.internal import ux
from tests.hikari import hikari_test_helpers


@pytest.mark.parametrize("activity", [undefined.UNDEFINED, None])
def test_validate_activity_when_no_activity(activity):
    with mock.patch.object(warnings, "warn") as warn:
        bot_impl._validate_activity(activity)

    warn.assert_not_called()


def test_validate_activity_when_type_is_streaming_but_no_url():
    activity = presences.Activity(name="test", url=None, type=presences.ActivityType.STREAMING)

    with mock.patch.object(warnings, "warn") as warn:
        bot_impl._validate_activity(activity)

    warn.assert_called_once_with(
        "The STREAMING activity type requires a 'url' parameter pointing to a valid Twitch or YouTube video "
        "URL to be specified on the activity for the presence update to have any effect.",
        category=errors.HikariWarning,
        stacklevel=3,
    )


def test_validate_activity_when_no_warning():
    activity = presences.Activity(name="test", state="Hello!", type=presences.ActivityType.CUSTOM)

    with mock.patch.object(warnings, "warn") as warn:
        bot_impl._validate_activity(activity)

    warn.assert_not_called()


class TestGatewayBot:
    @pytest.fixture
    def cache(self):
        return mock.Mock()

    @pytest.fixture
    def entity_factory(self):
        return mock.Mock()

    @pytest.fixture
    def event_factory(self):
        return mock.Mock()

    @pytest.fixture
    def event_manager(self):
        return mock.Mock()

    @pytest.fixture
    def rest(self):
        return mock.Mock()

    @pytest.fixture
    def voice(self):
        return mock.Mock()

    @pytest.fixture
    def executor(self):
        return mock.Mock()

    @pytest.fixture
    def intents(self):
        return mock.Mock()

    @pytest.fixture
    def proxy_settings(self):
        return mock.Mock()

    @pytest.fixture
    def http_settings(self):
        return mock.Mock()

    @pytest.fixture
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
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))

        with stack:
            return bot_impl.GatewayBot(
                "token",
                executor=executor,
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                intents=intents,
                max_retries=0,
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
        warn_if_not_optimized = stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))
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
                suppress_optimization_warning=True,
                executor=executor,
                force_color=True,
                cache_settings=cache_settings,
                http_settings=http_settings,
                intents=intents,
                auto_chunk_members=False,
                logs="DEBUG",
                max_rate_limit=200,
                max_retries=0,
                proxy_settings=proxy_settings,
                rest_url="somewhere.com",
            )

        assert bot._http_settings is http_settings
        assert bot._proxy_settings is proxy_settings
        assert bot._cache is cache.return_value
        cache.assert_called_once_with(bot, cache_settings)
        assert bot._event_manager is event_manager.return_value
        event_manager.assert_called_once_with(
            entity_factory.return_value,
            event_factory.return_value,
            intents,
            auto_chunk_members=False,
            cache=cache.return_value,
        )
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
            max_retries=0,
            proxy_settings=bot._proxy_settings,
            dumps=bot._dumps,
            loads=bot._loads,
            rest_url="somewhere.com",
            token="token",
            token_type=applications.TokenType.BOT,
        )

        init_logging.assert_called_once_with("DEBUG", False, True)
        print_banner.assert_called_once_with("testing", False, True)
        warn_if_not_optimized.assert_called_once_with(True)

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
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))
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

    def test_init_strips_token(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "print_banner"))
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))

        with stack:
            bot = bot_impl.GatewayBot(
                "\n\r token yeet \r\n", cache_settings=None, http_settings=None, proxy_settings=None
            )

        assert bot._token == "token yeet"

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

    @pytest.mark.parametrize(("closed_event", "expected"), [("something", True), (None, False)])
    def test_is_alive(self, bot, closed_event, expected):
        bot._closed_event = closed_event

        assert bot.is_alive is expected

    def test_check_if_alive(self, bot):
        bot._closed_event = object()

        bot._check_if_alive()

    def test_check_if_alive_when_False(self, bot):
        bot._closed_event = None

        with pytest.raises(errors.ComponentStateConflictError):
            bot._check_if_alive()

    @pytest.mark.asyncio
    async def test_close_when_already_closed(self, bot):
        bot._closed_event = mock.Mock()

        with pytest.raises(errors.ComponentStateConflictError):
            await bot.close()

    @pytest.mark.asyncio
    async def test_close_when_already_closing(self, bot):
        bot._closed_event = mock.Mock()
        bot._closing_event = mock.Mock(is_set=mock.Mock(return_value=True))

        with mock.patch.object(bot_impl.GatewayBot, "join") as join:
            await bot.close()

        join.assert_awaited_once_with()
        bot._closed_event.set.assert_not_called()

    @pytest.mark.asyncio
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
        mock_future = mock.Mock()
        get_running_loop.return_value.create_future.return_value = mock_future

        event_manager.dispatch = mock.AsyncMock()
        rest.close = AwaitableMock()
        voice.close = AwaitableMock()
        bot._closed_event = close_event = mock.Mock()
        bot._closing_event = closing_event = mock.Mock(is_set=mock.Mock(return_value=False))
        error = RuntimeError()
        shard0 = mock.Mock(id=0, close=AwaitableMock())
        shard1 = mock.Mock(id=1, close=AwaitableMock(error))
        shard2 = mock.Mock(id=2, close=AwaitableMock())
        bot._shards = {0: shard0, 1: shard1, 2: shard2}

        with stack:
            await bot.close()

        # Events and args
        close_event.set.assert_called_once_with()
        assert bot._closed_event is None

        closing_event.set.assert_called_once_with()
        assert bot._closing_event is None

        # Closing components
        ensure_future.assert_has_calls(
            [
                mock.call(voice.close()),
                mock.call(shard0.close()),
                mock.call(shard1.close()),
                mock.call(shard2.close()),
                mock.call(rest.close()),
            ]
        )

        rest.close.assert_awaited_once()
        voice.close.assert_awaited_once()
        shard0.close.assert_awaited_once()
        shard1.close.assert_awaited_once()
        shard2.close.assert_awaited_once()

        # Error handling
        get_running_loop.assert_called_once_with()
        get_running_loop.return_value.call_exception_handler.assert_called_once_with(
            {"message": "shard 1 raised an exception during shut down", "future": shard1.close(), "exception": error}
        )

        # Clear out maps
        assert bot._shards == {}
        cache.clear.assert_called_once_with()

        event_manager.dispatch.assert_has_calls(
            [
                mock.call(event_factory.deserialize_stopping_event.return_value),
                mock.call(event_factory.deserialize_stopped_event.return_value),
            ]
        )

    def test_dispatch(self, bot, event_manager):
        event = object()

        assert bot.dispatch(event) is event_manager.dispatch.return_value

        event_manager.dispatch.assert_called_once_with(event)

    def test_get_listeners(self, bot, event_manager):
        event = object()

        assert bot.get_listeners(event, polymorphic=False) is event_manager.get_listeners.return_value

        event_manager.get_listeners.assert_called_once_with(event, polymorphic=False)

    @pytest.mark.asyncio
    async def test_join(self, bot, event_manager):
        bot._closed_event = mock.AsyncMock()

        await bot.join()

        bot._closed_event.wait.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_join_when_not_running(self, bot, event_manager):
        bot._closed_event = None

        with pytest.raises(errors.ComponentStateConflictError):
            await bot.join()

    def test_listen(self, bot, event_manager):
        event = object()

        assert bot.listen(event) is event_manager.listen.return_value

        event_manager.listen.assert_called_once_with(event)

    def test_print_banner(self, bot):
        with mock.patch.object(ux, "print_banner") as print_banner:
            bot.print_banner("testing", False, True, extra_args={"test_key": "test_value"})

        print_banner.assert_called_once_with("testing", False, True, extra_args={"test_key": "test_value"})

    def test_run_when_already_running(self, bot):
        bot._closed_event = object()

        with pytest.raises(errors.ComponentStateConflictError):
            bot.run()

    def test_run_when_shard_ids_specified_without_shard_count(self, bot):
        with pytest.raises(TypeError, match=r"'shard_ids' must be passed with 'shard_count'"):
            bot.run(shard_ids={1})

    def test_run_with_asyncio_debug(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(
            mock.patch.object(signals, "handle_interrupts", return_value=hikari_test_helpers.ContextManagerMock())
        )
        loop = stack.enter_context(mock.patch.object(aio, "get_or_make_loop")).return_value

        with stack:
            bot.run(close_loop=False, asyncio_debug=True)

        loop.set_debug.assert_called_once_with(True)

    def test_run_with_coroutine_tracking_depth(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(
            mock.patch.object(signals, "handle_interrupts", return_value=hikari_test_helpers.ContextManagerMock())
        )
        stack.enter_context(mock.patch.object(aio, "get_or_make_loop"))
        coroutine_tracking_depth = stack.enter_context(
            mock.patch.object(sys, "set_coroutine_origin_tracking_depth", create=True, side_effect=AttributeError)
        )

        with stack:
            bot.run(close_loop=False, coroutine_tracking_depth=100)

        coroutine_tracking_depth.assert_called_once_with(100)

    def test_run_with_close_passed_executor(self, bot):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(
            mock.patch.object(signals, "handle_interrupts", return_value=hikari_test_helpers.ContextManagerMock())
        )
        stack.enter_context(mock.patch.object(aio, "get_or_make_loop"))
        executor = mock.Mock()
        bot._executor = executor

        with stack:
            bot.run(close_loop=False, close_passed_executor=True)

        executor.shutdown.assert_called_once_with(wait=True)
        assert bot._executor is None

    def test_run_when_close_loop(self, bot):
        stack = contextlib.ExitStack()
        logger = stack.enter_context(mock.patch.object(bot_impl, "_LOGGER"))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "start", new=mock.Mock()))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "join", new=mock.Mock()))
        stack.enter_context(
            mock.patch.object(signals, "handle_interrupts", return_value=hikari_test_helpers.ContextManagerMock())
        )
        destroy_loop = stack.enter_context(mock.patch.object(aio, "destroy_loop"))
        loop = stack.enter_context(mock.patch.object(aio, "get_or_make_loop")).return_value

        with stack:
            bot.run(close_loop=True)

        destroy_loop.assert_called_once_with(loop, logger)

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
        handle_interrupts = stack.enter_context(
            mock.patch.object(signals, "handle_interrupts", return_value=hikari_test_helpers.ContextManagerMock())
        )
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
            [mock.call(start_function.return_value), mock.call(join_function.return_value)]
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
        handle_interrupts.assert_called_once_with(enabled=False, loop=loop, propagate_interrupts=False)
        handle_interrupts.return_value.assert_used_once()

    @pytest.mark.asyncio
    async def test_start_when_shard_ids_specified_without_shard_count(self, bot):
        with pytest.raises(TypeError, match=r"'shard_ids' must be passed with 'shard_count'"):
            await bot.start(shard_ids=(1,))

    @pytest.mark.asyncio
    async def test_start_when_already_running(self, bot):
        bot._closed_event = object()

        with pytest.raises(errors.ComponentStateConflictError):
            await bot.start()

    @pytest.mark.asyncio
    async def test_start(self, bot, rest, voice, event_manager, event_factory, http_settings, proxy_settings):
        class MockSessionStartLimit:
            remaining = 10
            reset_at = "now"
            max_concurrency = 1

        class MockInfo:
            url = "yourmom.eu"
            shard_count = 2
            session_start_limit = MockSessionStartLimit()

        shard1 = mock.Mock()
        shard2 = mock.Mock()
        shards_iter = iter((shard1, shard2))

        mock_start_one_shard = mock.Mock()

        def _mock_start_one_shard(*args, **kwargs):
            bot._shards[kwargs["shard_id"]] = next(shards_iter)
            return mock_start_one_shard(*args, **kwargs)

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(bot_impl, "_validate_activity"))
        stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "_start_one_shard", new=_mock_start_one_shard))
        create_task = stack.enter_context(mock.patch.object(asyncio, "create_task"))
        gather = stack.enter_context(mock.patch.object(asyncio, "gather"))
        event = stack.enter_context(mock.patch.object(asyncio, "Event"))
        first_completed = stack.enter_context(
            mock.patch.object(aio, "first_completed", side_effect=[None, asyncio.TimeoutError, None])
        )
        check_for_updates = stack.enter_context(mock.patch.object(ux, "check_for_updates", new=mock.Mock()))

        event_manager.dispatch = mock.AsyncMock()
        rest.fetch_gateway_bot_info = mock.AsyncMock(return_value=MockInfo())

        with stack:
            await bot.start(
                check_for_updates=True,
                shard_ids=(2, 10),
                shard_count=20,
                activity="some activity",
                afk=True,
                idle_since="some idle since",
                status="some status",
                large_threshold=500,
            )

        check_for_updates.assert_called_once_with(http_settings, proxy_settings)
        create_task.assert_called_once_with(check_for_updates.return_value, name="check for package updates")
        rest.start.assert_called_once_with()
        voice.start.assert_called_once_with()

        assert event_manager.dispatch.call_count == 2
        event_manager.dispatch.assert_has_awaits(
            [
                mock.call(event_factory.deserialize_starting_event.return_value),
                mock.call(event_factory.deserialize_started_event.return_value),
            ]
        )

        assert gather.call_count == 2
        gather.assert_has_calls(
            [mock.call(mock_start_one_shard.return_value), mock.call(mock_start_one_shard.return_value)]
        )

        assert mock_start_one_shard.call_count == 2
        mock_start_one_shard.assert_has_calls(
            [
                mock.call(
                    bot,
                    activity="some activity",
                    afk=True,
                    idle_since="some idle since",
                    status="some status",
                    large_threshold=500,
                    shard_id=i,
                    shard_count=20,
                    url="yourmom.eu",
                )
                for i in (2, 10)
            ]
        )

        closing_event_closing_wait = event.return_value.wait.return_value
        assert first_completed.await_count == 3

        first_completed.assert_has_awaits(
            [
                # Shard 1
                mock.call(closing_event_closing_wait, gather.return_value),
                # Shard 2
                mock.call(closing_event_closing_wait, shard1.join.return_value, timeout=5),
                mock.call(closing_event_closing_wait, gather.return_value),
            ]
        )

    @pytest.mark.asyncio
    async def test_start_when_request_close_mid_startup(self, bot, rest, voice, event_manager, event_factory):
        class MockSessionStartLimit:
            remaining = 10
            reset_at = "now"
            max_concurrency = 1

        class MockInfo:
            url = "yourmom.eu"
            shard_count = 2
            session_start_limit = MockSessionStartLimit()

        # Assume that we already started one shard
        shard1 = mock.Mock()
        bot._shards = {"1": shard1}

        stack = contextlib.ExitStack()
        start_one_shard = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "_start_one_shard"))
        first_completed = stack.enter_context(mock.patch.object(aio, "first_completed"))
        event = stack.enter_context(
            mock.patch.object(asyncio, "Event", return_value=mock.Mock(is_set=mock.Mock(return_value=True)))
        )

        event_manager.dispatch = mock.AsyncMock()
        rest.fetch_gateway_bot_info = mock.AsyncMock(return_value=MockInfo())

        with stack:
            await bot.start(shard_ids=(2, 10), shard_count=20, check_for_updates=False)

        start_one_shard.assert_not_called()

        first_completed.assert_called_once_with(
            event.return_value.wait.return_value, shard1.join.return_value, timeout=5
        )

    @pytest.mark.asyncio
    async def test_start_when_shard_closed_mid_startup(self, bot, rest, voice, event_manager, event_factory):
        class MockSessionStartLimit:
            remaining = 10
            reset_at = "now"
            max_concurrency = 1

        class MockInfo:
            url = "yourmom.eu"
            shard_count = 2
            session_start_limit = MockSessionStartLimit()

        # Assume that we already started one shard
        shard1 = mock.Mock()
        bot._shards = {"1": shard1}

        stack = contextlib.ExitStack()
        start_one_shard = stack.enter_context(mock.patch.object(bot_impl.GatewayBot, "_start_one_shard"))
        first_completed = stack.enter_context(mock.patch.object(aio, "first_completed"))
        event = stack.enter_context(
            mock.patch.object(asyncio, "Event", return_value=mock.Mock(is_set=mock.Mock(return_value=False)))
        )
        stack.enter_context(pytest.raises(RuntimeError, match="One or more shards closed while starting"))

        event_manager.dispatch = mock.AsyncMock()
        rest.fetch_gateway_bot_info = mock.AsyncMock(return_value=MockInfo())

        with stack:
            await bot.start(shard_ids=(2, 10), shard_count=20, check_for_updates=False)

        start_one_shard.assert_not_called()

        first_completed.assert_called_once_with(
            event.return_value.wait.return_value, shard1.join.return_value, timeout=5
        )

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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
                with mock.patch.object(bot_impl, "_validate_activity") as validate_activity:
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_request_guild_members(self, bot):
        shard = mock.Mock(shard_count=3)
        shard.request_guild_members = mock.AsyncMock()

        with mock.patch.object(bot_impl.GatewayBot, "_get_shard", return_value=shard) as get_shard:
            with mock.patch.object(bot_impl.GatewayBot, "_check_if_alive") as check_if_alive:
                await bot.request_guild_members(
                    115590097100865541, include_presences=True, query="indeed", limit=42, users=[123], nonce="NONCE"
                )

        check_if_alive.assert_called_once_with()
        get_shard.assert_called_once_with(115590097100865541)
        shard.request_guild_members.assert_awaited_once_with(
            guild=115590097100865541, include_presences=True, query="indeed", limit=42, users=[123], nonce="NONCE"
        )

    @pytest.mark.asyncio
    async def test_start_one_shard(self, bot):
        activity = object()
        status = object()
        bot._shards = {}
        shard_obj = mock.Mock(is_alive=True, start=mock.AsyncMock())

        with mock.patch.object(shard_impl, "GatewayShardImpl", new=mock.Mock(return_value=shard_obj)) as shard:
            await bot._start_one_shard(
                activity=activity,
                afk=True,
                idle_since=None,
                status=status,
                large_threshold=1000,
                shard_id=1,
                shard_count=3,
                url="https://some.website",
            )

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
            loads=bot._loads,
            dumps=bot._dumps,
            token=bot._token,
            url="https://some.website",
        )
        shard_obj.start.assert_awaited_once_with()
        assert bot._shards == {1: shard_obj}

    @pytest.mark.asyncio
    async def test_start_one_shard_when_not_alive(self, bot):
        activity = object()
        status = object()
        bot._shards = {}
        shard_obj = mock.Mock(is_alive=False, start=mock.AsyncMock())

        with mock.patch.object(shard_impl, "GatewayShardImpl", return_value=shard_obj):
            with pytest.raises(RuntimeError, match=r"shard 1 shut down immediately when starting"):
                await bot._start_one_shard(
                    activity=activity,
                    afk=True,
                    idle_since=None,
                    status=status,
                    large_threshold=1000,
                    shard_id=1,
                    shard_count=3,
                    url="https://some.website",
                )

        assert bot._shards == {}
        shard_obj.close.assert_not_called()

    @pytest.mark.parametrize("is_alive", [True, False])
    @pytest.mark.asyncio
    async def test_start_one_shard_when_exception(self, bot, is_alive):
        activity = object()
        status = object()
        bot._shards = {}
        shard_obj = mock.Mock(
            is_alive=is_alive, start=mock.AsyncMock(side_effect=RuntimeError("exit in tests")), close=mock.AsyncMock()
        )

        with mock.patch.object(shard_impl, "GatewayShardImpl", return_value=shard_obj):
            with pytest.raises(RuntimeError, match=r"exit in tests"):
                await bot._start_one_shard(
                    activity=activity,
                    afk=True,
                    idle_since=None,
                    status=status,
                    large_threshold=1000,
                    shard_id=1,
                    shard_count=3,
                    url="https://some.website",
                )

        assert bot._shards == {}

        if is_alive:
            shard_obj.close.assert_awaited_once_with()
        else:
            shard_obj.close.assert_not_called()
