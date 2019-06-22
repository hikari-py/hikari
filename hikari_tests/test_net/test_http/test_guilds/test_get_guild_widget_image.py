#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


def test_get_guild_widget_image(http_client):
    http_client.base_uri = "https://potato.com/api/v12"
    assert (
        http_client.get_guild_widget_image("1234", style="banner3")
        == "https://potato.com/api/v12/guilds/1234/widget.png?style=banner3"
    )
