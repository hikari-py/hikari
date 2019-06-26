#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest

from hikari.net.http import client


class ClientMock(client.HTTPClient):
    """
    Useful for HTTP client calls that need to mock the HTTP connection quickly in a fixture.

    .. code-block::
        @pytest.fixture()
        def http_client(event_loop):
            from hikari_tests.test_net.test_http import ClientMock
            return ClientMock(token="foobarsecret", loop=event_loop)

        @pytest.mark.asyncio
        async def test_that_something_does_a_thing(http_client):
            http_client.request = asynctest.CoroutineMock(return_value=69)
            assert await http_client.something() == 69

    """

    def __init__(self, *args, **kwargs):
        with asynctest.patch("aiohttp.ClientSession", new=asynctest.MagicMock()):
            super().__init__(*args, **kwargs)

    async def request(self, method, path, params=None, **kwargs):
        pass
