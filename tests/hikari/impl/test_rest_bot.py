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
import concurrent.futures
import contextlib
import sys

import mock
import pytest

from hikari import errors
from hikari.impl import config
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import interaction_server as interaction_server_impl
from hikari.impl import rest as rest_impl
from hikari.impl import rest_bot as rest_bot_impl
from hikari.internal import aio
from hikari.internal import signals
from hikari.internal import ux
from tests.hikari import hikari_test_helpers


class TestRESTBot:
    @pytest.fixture
    def mock_interaction_server(self):
        return mock.Mock(interaction_server_impl.InteractionServer)

    @pytest.fixture
    def mock_rest_client(self):
        return mock.Mock(rest_impl.RESTClientImpl)

    @pytest.fixture
    def mock_entity_factory(self):
        return mock.Mock(entity_factory_impl.EntityFactoryImpl)

    @pytest.fixture
    def mock_http_settings(self):
        return mock.Mock(config.HTTPSettings)

    @pytest.fixture
    def mock_proxy_settings(self):
        return mock.Mock(config.ProxySettings)

    @pytest.fixture
    def mock_executor(self):
        return mock.Mock(concurrent.futures.Executor)

    @pytest.fixture
    def mock_rest_bot(
        self,
        mock_interaction_server,
        mock_rest_client,
        mock_entity_factory,
        mock_http_settings,
        mock_proxy_settings,
        mock_executor,
    ):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))
        stack.enter_context(mock.patch.object(rest_bot_impl.RESTBot, "print_banner"))
        stack.enter_context(
            mock.patch.object(entity_factory_impl, "EntityFactoryImpl", return_value=mock_entity_factory)
        )
        stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl", return_value=mock_rest_client))
        stack.enter_context(
            mock.patch.object(interaction_server_impl, "InteractionServer", return_value=mock_interaction_server)
        )

        with stack:
            return hikari_test_helpers.mock_class_namespace(rest_bot_impl.RESTBot, slots_=False)(
                "token",
                http_settings=mock_http_settings,
                proxy_settings=mock_proxy_settings,
                executor=mock_executor,
                max_retries=0,
            )

    def test___init__(
        self, mock_http_settings, mock_proxy_settings, mock_entity_factory, mock_rest_client, mock_interaction_server
    ):
        cls = hikari_test_helpers.mock_class_namespace(rest_bot_impl.RESTBot, print_banner=mock.Mock())
        mock_executor = object()

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))
        stack.enter_context(mock.patch.object(rest_bot_impl.RESTBot, "print_banner"))
        stack.enter_context(
            mock.patch.object(entity_factory_impl, "EntityFactoryImpl", return_value=mock_entity_factory)
        )
        stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl", return_value=mock_rest_client))
        stack.enter_context(
            mock.patch.object(interaction_server_impl, "InteractionServer", return_value=mock_interaction_server)
        )

        with stack:
            result = cls(
                "token",
                "token_type",
                b"2123123123123132",
                allow_color=False,
                banner="a banner",
                suppress_optimization_warning=True,
                executor=mock_executor,
                force_color=True,
                http_settings=mock_http_settings,
                logs="ERROR",
                max_rate_limit=32123123,
                max_retries=0,
                proxy_settings=mock_proxy_settings,
                rest_url="hresresres",
            )

            ux.init_logging.assert_called_once_with("ERROR", False, True)
            ux.warn_if_not_optimized.assert_called_once_with(True)
            entity_factory_impl.EntityFactoryImpl.assert_called_once_with(result)
            rest_impl.RESTClientImpl.assert_called_once_with(
                cache=None,
                entity_factory=mock_entity_factory,
                executor=mock_executor,
                http_settings=mock_http_settings,
                max_rate_limit=32123123,
                max_retries=0,
                proxy_settings=mock_proxy_settings,
                rest_url="hresresres",
                token="token",
                token_type="token_type",
            )
            interaction_server_impl.InteractionServer.assert_called_once_with(
                entity_factory=mock_entity_factory, public_key=b"2123123123123132", rest_client=mock_rest_client
            )

        result.print_banner.assert_called_once_with("a banner", False, True)
        assert result.interaction_server is mock_interaction_server
        assert result.rest is mock_rest_client
        assert result.entity_factory is mock_entity_factory
        assert result.http_settings is mock_http_settings
        assert result.proxy_settings is mock_proxy_settings
        assert result.executor is mock_executor

    def test___init___parses_string_public_key(self):
        cls = hikari_test_helpers.mock_class_namespace(rest_bot_impl.RESTBot, print_banner=mock.Mock())

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))
        stack.enter_context(mock.patch.object(rest_bot_impl.RESTBot, "print_banner"))
        stack.enter_context(mock.patch.object(interaction_server_impl, "InteractionServer"))

        with stack:
            result = cls(object(), "token_type", "6f66646f646f646f6f")

            interaction_server_impl.InteractionServer.assert_called_once_with(
                entity_factory=result.entity_factory, public_key=b"ofdododoo", rest_client=result.rest
            )

    def test___init___strips_token(self):
        cls = hikari_test_helpers.mock_class_namespace(rest_bot_impl.RESTBot, print_banner=mock.Mock())

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))
        rest_client = stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl"))
        http_settings = stack.enter_context(mock.patch.object(config, "HTTPSettings"))
        proxy_settings = stack.enter_context(mock.patch.object(config, "ProxySettings"))
        stack.enter_context(mock.patch.object(interaction_server_impl, "InteractionServer"))

        with stack:
            result = cls("\n\r sddsa tokenoken \n", "token_type")

        rest_client.assert_called_once_with(
            cache=None,
            entity_factory=result.entity_factory,
            executor=None,
            http_settings=http_settings.return_value,
            max_rate_limit=300.0,
            max_retries=3,
            proxy_settings=proxy_settings.return_value,
            rest_url=None,
            token="sddsa tokenoken",
            token_type="token_type",
        )

    def test___init___generates_default_settings(self):
        cls = hikari_test_helpers.mock_class_namespace(rest_bot_impl.RESTBot, print_banner=mock.Mock())
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ux, "init_logging"))
        stack.enter_context(mock.patch.object(ux, "warn_if_not_optimized"))
        stack.enter_context(mock.patch.object(rest_bot_impl.RESTBot, "print_banner"))
        stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl"))
        stack.enter_context(mock.patch.object(config, "HTTPSettings"))
        stack.enter_context(mock.patch.object(config, "ProxySettings"))
        stack.enter_context(mock.patch.object(interaction_server_impl, "InteractionServer"))

        with stack:
            result = cls("token")

            rest_impl.RESTClientImpl.assert_called_once_with(
                cache=None,
                entity_factory=result.entity_factory,
                executor=None,
                http_settings=config.HTTPSettings.return_value,
                max_rate_limit=300.0,
                max_retries=3,
                proxy_settings=config.ProxySettings.return_value,
                rest_url=None,
                token="token",
                token_type="Bot",
            )

            config.HTTPSettings.assert_called_once()
            config.ProxySettings.assert_called_once()
            assert result.http_settings is config.HTTPSettings.return_value
            assert result.proxy_settings is config.ProxySettings.return_value

    @pytest.mark.parametrize(("close_event", "expected"), [(object(), True), (None, False)])
    def test_is_alive_property(self, mock_rest_bot, close_event, expected):
        mock_rest_bot._close_event = close_event
        assert mock_rest_bot.is_alive is expected

    def test_print_banner(self, mock_rest_bot):
        with mock.patch.object(ux, "print_banner") as print_banner:
            mock_rest_bot.print_banner("okokok", True, False, {"test_key": "test_value"})

            print_banner.assert_called_once_with("okokok", True, False, extra_args={"test_key": "test_value"})

    def test_add_shutdown_callback(self, mock_rest_bot: rest_bot_impl.RESTBot):
        callback = mock.Mock()
        mock_rest_bot.add_shutdown_callback(callback)

        assert callback in mock_rest_bot.on_shutdown

    def test_remove_shutdown_callback(self, mock_rest_bot: rest_bot_impl.RESTBot):
        callback = mock.Mock()
        mock_rest_bot.add_shutdown_callback(callback)

        mock_rest_bot.remove_shutdown_callback(callback)

        assert callback not in mock_rest_bot.on_shutdown

    def test_remove_shutdown_callback_when_not_present(self, mock_rest_bot: rest_bot_impl.RESTBot):
        callback = mock.Mock()

        with pytest.raises(ValueError, match=".*"):
            mock_rest_bot.remove_shutdown_callback(callback)

    def test_add_startup_callback(self, mock_rest_bot: rest_bot_impl.RESTBot):
        callback = mock.Mock()
        mock_rest_bot.add_startup_callback(callback)

        assert callback in mock_rest_bot.on_startup

    def test_remove_startup_callback(self, mock_rest_bot: rest_bot_impl.RESTBot):
        callback = mock.Mock()
        mock_rest_bot.add_startup_callback(callback)

        mock_rest_bot.remove_startup_callback(callback)

        assert callback not in mock_rest_bot.on_startup

    def test_remove_startup_callback_when_not_present(self, mock_rest_bot: rest_bot_impl.RESTBot):
        callback = mock.Mock()

        with pytest.raises(ValueError, match=".*"):
            mock_rest_bot.remove_startup_callback(callback)

    @pytest.mark.asyncio
    async def test_close(
        self, mock_rest_bot: rest_bot_impl.RESTBot, mock_interaction_server: mock.Mock, mock_rest_client: mock.Mock
    ):
        mock_shutdown_1 = mock.AsyncMock()
        mock_shutdown_2 = mock.AsyncMock()
        mock_rest_bot._close_event = close_event = mock.Mock()
        mock_interaction_server.close = mock.AsyncMock()
        mock_rest_bot._is_closing = False
        mock_rest_bot.add_shutdown_callback(mock_shutdown_1)
        mock_rest_bot.add_shutdown_callback(mock_shutdown_2)

        await mock_rest_bot.close()

        mock_interaction_server.close.assert_awaited_once()
        mock_rest_client.close.assert_awaited_once()
        close_event.set.assert_called_once()
        assert mock_rest_bot._is_closing is False
        mock_shutdown_1.assert_awaited_once_with(mock_rest_bot)
        mock_shutdown_2.assert_awaited_once_with(mock_rest_bot)

    @pytest.mark.asyncio
    async def test_close_when_shutdown_callback_raises(
        self, mock_rest_bot: rest_bot_impl.RESTBot, mock_interaction_server: mock.Mock, mock_rest_client: mock.Mock
    ):
        mock_error = KeyError("Too many catgirls")
        mock_shutdown_1 = mock.AsyncMock(side_effect=mock_error)
        mock_shutdown_2 = mock.AsyncMock()
        mock_rest_bot._close_event = close_event = mock.Mock()
        mock_interaction_server.close = mock.AsyncMock()
        mock_rest_bot._is_closing = False
        mock_rest_bot.add_shutdown_callback(mock_shutdown_1)
        mock_rest_bot.add_shutdown_callback(mock_shutdown_2)

        with pytest.raises(KeyError) as exc_info:
            await mock_rest_bot.close()

        assert exc_info.value is mock_error
        mock_interaction_server.close.assert_awaited_once()
        mock_rest_client.close.assert_awaited_once()
        close_event.set.assert_called_once()
        assert mock_rest_bot._is_closing is False
        mock_shutdown_1.assert_awaited_once_with(mock_rest_bot)
        mock_shutdown_2.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_when_is_closing(
        self, mock_rest_bot: rest_bot_impl.RESTBot, mock_interaction_server: mock.Mock, mock_rest_client: mock.Mock
    ):
        mock_shutdown_1 = mock.AsyncMock()
        mock_shutdown_2 = mock.AsyncMock()
        mock_rest_bot._close_event = mock.Mock()
        mock_interaction_server.close = mock.AsyncMock()
        mock_rest_bot._is_closing = True
        mock_rest_bot.join = mock.AsyncMock()
        mock_rest_bot.add_shutdown_callback(mock_shutdown_1)
        mock_rest_bot.add_shutdown_callback(mock_shutdown_2)

        await mock_rest_bot.close()

        mock_interaction_server.close.assert_not_called()
        mock_rest_client.close.assert_not_called()
        mock_rest_bot._close_event.set.assert_not_called()
        mock_rest_bot.join.assert_awaited_once()
        assert mock_rest_bot._is_closing is True
        mock_shutdown_1.assert_not_called()
        mock_shutdown_2.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_when_inactive(self, mock_rest_bot):
        with pytest.raises(errors.ComponentStateConflictError):
            await mock_rest_bot.close()

    @pytest.mark.asyncio
    async def test_join(self, mock_rest_bot):
        mock_rest_bot._close_event = mock.AsyncMock()

        await mock_rest_bot.join()

        mock_rest_bot._close_event.wait.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_join_when_not_alive(self, mock_rest_bot):
        with pytest.raises(errors.ComponentStateConflictError):
            await mock_rest_bot.join()

    @pytest.mark.asyncio
    async def test_on_interaction(self, mock_rest_bot, mock_interaction_server):
        mock_interaction_server.on_interaction = mock.AsyncMock()

        result = await mock_rest_bot.on_interaction(b"1", b"2", b"3")

        assert result is mock_interaction_server.on_interaction.return_value
        mock_interaction_server.on_interaction.assert_awaited_once_with(b"1", b"2", b"3")

    def test_run(self, mock_rest_bot):
        mock_socket = object()
        mock_context = object()
        mock_rest_bot._executor = None
        mock_rest_bot.start = mock.Mock()
        mock_rest_bot.join = mock.Mock()

        stack = contextlib.ExitStack()
        check_for_updates = stack.enter_context(mock.patch.object(ux, "check_for_updates"))
        handle_interrupts = stack.enter_context(
            mock.patch.object(signals, "handle_interrupts", return_value=hikari_test_helpers.ContextManagerMock())
        )
        get_or_make_loop = stack.enter_context(mock.patch.object(aio, "get_or_make_loop"))

        with stack:
            mock_rest_bot.run(
                asyncio_debug=False,
                backlog=321,
                check_for_updates=False,
                close_loop=False,
                close_passed_executor=False,
                coroutine_tracking_depth=32123,
                enable_signal_handlers=True,
                propagate_interrupts=True,
                host="192.168.1.102",
                path="pathathath",
                port=4554,
                reuse_address=True,
                reuse_port=False,
                shutdown_timeout=534.534,
                socket=mock_socket,
                ssl_context=mock_context,
            )

        check_for_updates.assert_not_called()
        handle_interrupts.assert_called_once_with(
            enabled=True, loop=get_or_make_loop.return_value, propagate_interrupts=True
        )
        handle_interrupts.return_value.assert_used_once()

        mock_rest_bot.start.assert_called_once_with(
            backlog=321,
            check_for_updates=False,
            host="192.168.1.102",
            path="pathathath",
            port=4554,
            reuse_address=True,
            reuse_port=False,
            socket=mock_socket,
            shutdown_timeout=534.534,
            ssl_context=mock_context,
        )
        mock_rest_bot.join.assert_called_once_with()

        assert get_or_make_loop.return_value.run_until_complete.call_count == 2
        get_or_make_loop.return_value.run_until_complete.assert_has_calls(
            [mock.call(mock_rest_bot.start.return_value), mock.call(mock_rest_bot.join.return_value)]
        )
        get_or_make_loop.return_value.close.assert_not_called()

    def test_run_when_close_loop(self, mock_rest_bot):
        mock_rest_bot.start = mock.Mock()
        mock_rest_bot.join = mock.Mock()

        with mock.patch.object(aio, "get_or_make_loop") as get_or_make_loop:
            with mock.patch.object(aio, "destroy_loop") as destroy_loop:
                mock_rest_bot.run(close_loop=True)

        destroy_loop.assert_called_once_with(get_or_make_loop.return_value, rest_bot_impl._LOGGER)

    def test_run_when_asyncio_debug(self, mock_rest_bot):
        mock_rest_bot.start = mock.Mock()
        mock_rest_bot.join = mock.Mock()

        with mock.patch.object(aio, "get_or_make_loop") as get_or_make_loop:
            mock_rest_bot.run(asyncio_debug=True, close_loop=False)

        get_or_make_loop.return_value.set_debug.assert_called_once_with(True)

    def test_run_with_coroutine_tracking_depth(self, mock_rest_bot):
        mock_rest_bot.start = mock.Mock()
        mock_rest_bot.join = mock.Mock()

        with mock.patch.object(aio, "get_or_make_loop"):
            with mock.patch.object(
                sys, "set_coroutine_origin_tracking_depth", side_effect=AttributeError, create=True
            ) as set_tracking_depth:
                mock_rest_bot.run(coroutine_tracking_depth=42, close_loop=False)

        set_tracking_depth.assert_called_once_with(42)

    def test_run_when_already_running(self, mock_rest_bot):
        mock_rest_bot._close_event = object()

        with pytest.raises(errors.ComponentStateConflictError):
            mock_rest_bot.run()

    def test_run_closes_executor_when_present(self, mock_rest_bot, mock_executor):
        mock_rest_bot.start = mock.Mock()
        mock_rest_bot.join = mock.Mock()

        with mock.patch.object(aio, "get_or_make_loop"):
            mock_rest_bot.run(
                asyncio_debug=False,
                backlog=321,
                check_for_updates=False,
                close_loop=False,
                close_passed_executor=True,
                coroutine_tracking_depth=32123,
                enable_signal_handlers=True,
                host="192.168.1.102",
                path="pathathath",
                port=4554,
                reuse_address=True,
                reuse_port=False,
                shutdown_timeout=534.534,
                socket=object(),
                ssl_context=object(),
            )

        mock_executor.shutdown.assert_called_once_with(wait=True)
        assert mock_rest_bot.executor is None

    def test_run_ignores_close_executor_when_not_present(self, mock_rest_bot):
        mock_rest_bot.start = mock.Mock()
        mock_rest_bot.join = mock.Mock()
        mock_rest_bot._executor = None

        with mock.patch.object(aio, "get_or_make_loop"):
            mock_rest_bot.run(
                asyncio_debug=False,
                backlog=321,
                check_for_updates=False,
                close_loop=False,
                close_passed_executor=True,
                coroutine_tracking_depth=32123,
                enable_signal_handlers=True,
                host="192.168.1.102",
                path="pathathath",
                port=4554,
                reuse_address=True,
                reuse_port=False,
                shutdown_timeout=534.534,
                socket=object(),
                ssl_context=object(),
            )

        assert mock_rest_bot.executor is None

    @pytest.mark.asyncio
    async def test_start(
        self, mock_rest_bot: rest_bot_impl.RESTBot, mock_interaction_server: mock.Mock, mock_rest_client: mock.Mock
    ):
        mock_socket = object()
        mock_ssl_context = object()
        mock_callback_1 = mock.AsyncMock()
        mock_callback_2 = mock.AsyncMock()
        mock_rest_bot.add_startup_callback(mock_callback_1)
        mock_rest_bot.add_startup_callback(mock_callback_2)
        mock_rest_bot._is_closing = True

        with mock.patch.object(ux, "check_for_updates"):
            await mock_rest_bot.start(
                backlog=34123,
                check_for_updates=False,
                host="hostostosot",
                port=123123123,
                path="patpatpapt",
                reuse_address=True,
                reuse_port=False,
                socket=mock_socket,
                shutdown_timeout=4312312.3132132,
                ssl_context=mock_ssl_context,
            )

            ux.check_for_updates.assert_not_called()

        mock_interaction_server.start.assert_awaited_once_with(
            backlog=34123,
            host="hostostosot",
            port=123123123,
            path="patpatpapt",
            reuse_address=True,
            reuse_port=False,
            socket=mock_socket,
            shutdown_timeout=4312312.3132132,
            ssl_context=mock_ssl_context,
        )
        mock_rest_client.start.assert_called_once_with()
        mock_rest_client.close.assert_not_called()
        assert mock_rest_bot._is_closing is False
        mock_callback_1.assert_awaited_once_with(mock_rest_bot)
        mock_callback_2.assert_awaited_once_with(mock_rest_bot)

    @pytest.mark.asyncio
    async def test_start_when_startup_callback_raises(
        self, mock_rest_bot: rest_bot_impl.RESTBot, mock_interaction_server: mock.Mock, mock_rest_client: mock.Mock
    ):
        mock_socket = object()
        mock_ssl_context = object()
        mock_rest_bot._is_closing = True
        mock_error = TypeError("Not a real catgirl")
        mock_callback_1 = mock.AsyncMock(side_effect=mock_error)
        mock_callback_2 = mock.AsyncMock()
        mock_rest_bot.add_startup_callback(mock_callback_1)
        mock_rest_bot.add_startup_callback(mock_callback_2)

        with mock.patch.object(ux, "check_for_updates"):
            with pytest.raises(TypeError) as exc_info:
                await mock_rest_bot.start(
                    backlog=34123,
                    check_for_updates=False,
                    host="hostostosot",
                    port=123123123,
                    path="patpatpapt",
                    reuse_address=True,
                    reuse_port=False,
                    socket=mock_socket,
                    shutdown_timeout=4312312.3132132,
                    ssl_context=mock_ssl_context,
                )

            assert exc_info.value is mock_error
            ux.check_for_updates.assert_not_called()

        mock_interaction_server.start.assert_not_called()
        mock_rest_client.start.assert_called_once_with()
        mock_rest_client.close.assert_awaited_once_with()
        assert mock_rest_bot._is_closing is False
        mock_callback_1.assert_awaited_once_with(mock_rest_bot)
        mock_callback_2.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_checks_for_update(self, mock_rest_bot, mock_http_settings, mock_proxy_settings):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(asyncio, "create_task"))
        stack.enter_context(mock.patch.object(ux, "check_for_updates", new=mock.Mock()))

        with stack:
            await mock_rest_bot.start(
                backlog=34123,
                check_for_updates=True,
                host="hostostosot",
                port=123123123,
                path="patpatpapt",
                reuse_address=True,
                reuse_port=False,
                socket=object(),
                shutdown_timeout=4312312.3132132,
                ssl_context=object(),
            )

            asyncio.create_task.assert_called_once_with(
                ux.check_for_updates.return_value, name="check for package updates"
            )
            ux.check_for_updates.assert_called_once_with(mock_http_settings, mock_proxy_settings)

    @pytest.mark.asyncio
    async def test_start_when_is_alive(self, mock_rest_bot):
        mock_rest_bot._close_event = object()

        with mock.patch.object(ux, "check_for_updates", new=mock.Mock()) as check_for_updates:
            with pytest.raises(errors.ComponentStateConflictError):
                await mock_rest_bot.start()

            check_for_updates.assert_not_called()

    def test_get_listener(self, mock_rest_bot, mock_interaction_server):
        mock_type = object()

        result = mock_rest_bot.get_listener(mock_type)

        assert result is mock_interaction_server.get_listener.return_value
        mock_interaction_server.get_listener.assert_called_once_with(mock_type)

    def test_set_listener(self, mock_rest_bot, mock_interaction_server):
        mock_type = object()
        mock_listener = object()

        mock_rest_bot.set_listener(mock_type, mock_listener, replace=True)

        mock_interaction_server.set_listener.assert_called_once_with(mock_type, mock_listener, replace=True)
