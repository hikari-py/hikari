# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
import asyncio

import mock
import pytest

from hikari.net import gateway


@pytest.fixture()
def client():
    return gateway.Gateway(url="wss://gateway.discord.gg", token="lol", app=mock.MagicMock(), config=mock.MagicMock(),)


class TestInit:
    @pytest.mark.parametrize(
        ["v", "use_compression", "expect"],
        [
            (6, False, "v=6&encoding=json"),
            (6, True, "v=6&encoding=json&compress=zlib-stream"),
            (7, False, "v=7&encoding=json"),
            (7, True, "v=7&encoding=json&compress=zlib-stream"),
        ],
    )
    def test_url_is_correct_json(self, v, use_compression, expect):
        g = gateway.Gateway(
            app=mock.MagicMock(),
            config=mock.MagicMock(),
            token=mock.MagicMock(),
            url="wss://gaytewhuy.discord.meh",
            version=v,
            use_etf=False,
            use_compression=use_compression,
        )

        assert g.url == f"wss://gaytewhuy.discord.meh?{expect}"

    @pytest.mark.parametrize(["v", "use_compression"], [(6, False), (6, True), (7, False), (7, True),])
    def test_using_etf_is_unsupported(self, v, use_compression):
        with pytest.raises(NotImplementedError):
            gateway.Gateway(
                app=mock.MagicMock(),
                config=mock.MagicMock(),
                token=mock.MagicMock(),
                url="wss://erlpack-is-broken-lol.discord.meh",
                version=v,
                use_etf=True,
                use_compression=use_compression,
            )


class TestAppProperty:
    def test_returns_app(self):
        app = mock.MagicMock()
        g = gateway.Gateway(url="wss://gateway.discord.gg", token="lol", app=app, config=mock.MagicMock())
        assert g.app is app


class TestIsAliveProperty:
    def test_is_alive(self, client):
        client.connected_at = 1234
        assert client.is_alive

    def test_not_is_alive(self, client):
        client.connected_at = float("nan")
        assert not client.is_alive


@pytest.mark.asyncio
class TestStart:
    @pytest.mark.parametrize("shard_id", [0, 1, 2])
    async def test_starts_task(self, event_loop, shard_id):
        g = gateway.Gateway(
            url="wss://gateway.discord.gg",
            token="lol",
            app=mock.MagicMock(),
            config=mock.MagicMock(),
            shard_id=shard_id,
            shard_count=100,
        )

        g._handshake_event = mock.MagicMock()
        g._handshake_event.wait = mock.AsyncMock()
        g._run = mock.MagicMock()

        future = event_loop.create_future()
        future.set_result(None)

        with mock.patch.object(asyncio, "create_task", return_value=future) as create_task:
            result = await g.start()
            assert result is future
            create_task.assert_called_once_with(g._run(), name=f"shard {shard_id} keep-alive")

    async def test_waits_for_ready(self, client):
        client._handshake_event = mock.MagicMock()
        client._handshake_event.wait = mock.AsyncMock()
        client._run = mock.AsyncMock()

        await client.start()
        client._handshake_event.wait.assert_awaited_once_with()
