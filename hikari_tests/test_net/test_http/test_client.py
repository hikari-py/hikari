#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

from hikari.net import http


@pytest.mark.asyncio
async def test_initialize_http(event_loop):
    client = http.HTTPClient(loop=event_loop, token="1a2b3c4d.1a2b3c4d")

    assert client is not None
