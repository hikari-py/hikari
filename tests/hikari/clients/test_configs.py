#!/usr/bin/env python3
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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import datetime
import ssl

import aiohttp
import pytest

from hikari import gateway_entities
from hikari import guilds
from hikari import intents
from hikari.clients import configs
from tests.hikari import _helpers


@pytest.fixture
def test_debug_config():
    return {"debug": True}


@pytest.fixture
def test_aiohttp_config():
    return {
        "allow_redirects": True,
        "tcp_connector": "aiohttp#TCPConnector",
        "proxy_headers": {"Some-Header": "headercontent"},
        "proxy_auth": "basic Tm90aGluZyB0byBzZWUgaGVyZSA6IGpvaW4gZGlzY29yZC5nZy9IS0dQRTlRIDopIH5kYXZmc2E=",
        "proxy_url": "proxy_url",
        "request_timeout": 100,
        "ssl_context": "ssl#SSLContext",
        "verify_ssl": False,
    }


@pytest.fixture
def test_token_config():
    return {"token": "token"}


@pytest.fixture
def test_websocket_config(test_debug_config, test_aiohttp_config, test_token_config):
    return {
        "gateway_use_compression": False,
        "gateway_version": 7,
        "initial_activity": {"name": "test", "url": "some_url", "type": 0},
        "initial_status": "dnd",
        "initial_is_afk": True,
        "initial_idle_since": None,  # Set in test
        "intents": 513,
        "large_threshold": 1000,
        "shard_ids": "5...10",
        "shard_count": "17",
        **test_debug_config,
        **test_aiohttp_config,
        **test_token_config,
    }


@pytest.fixture
def test_rest_config(test_aiohttp_config, test_token_config):
    return {"rest_version": 6, **test_aiohttp_config, **test_token_config}


@pytest.fixture
def test_bot_config(test_rest_config, test_websocket_config):
    return {**test_rest_config, **test_websocket_config}


class TestDebugConfig:
    def test_deserialize(self, test_debug_config):
        debug_config_obj = configs.DebugConfig.deserialize(test_debug_config)

        assert debug_config_obj.debug is True

    def test_empty_deserialize(self):
        debug_config_obj = configs.DebugConfig.deserialize({})

        assert debug_config_obj.debug is False


class TestAIOHTTPConfig:
    def test_deserialize(self, test_aiohttp_config):
        aiohttp_config_obj = configs.AIOHTTPConfig.deserialize(test_aiohttp_config)

        assert aiohttp_config_obj.allow_redirects is True
        assert aiohttp_config_obj.tcp_connector == aiohttp.TCPConnector
        assert aiohttp_config_obj.proxy_headers == {"Some-Header": "headercontent"}
        assert aiohttp_config_obj.proxy_auth == aiohttp.BasicAuth.decode(
            "basic Tm90aGluZyB0byBzZWUgaGVyZSA6IGpvaW4gZGlzY29yZC5nZy9IS0dQRTlRIDopIH5kYXZmc2E="
        )
        assert aiohttp_config_obj.proxy_url == "proxy_url"
        assert aiohttp_config_obj.request_timeout == 100
        assert aiohttp_config_obj.ssl_context == ssl.SSLContext
        assert aiohttp_config_obj.verify_ssl is False

    def test_empty_deserialize(self):
        aiohttp_config_obj = configs.AIOHTTPConfig.deserialize({})

        assert aiohttp_config_obj.allow_redirects is False
        assert aiohttp_config_obj.tcp_connector is None
        assert aiohttp_config_obj.proxy_headers is None
        assert aiohttp_config_obj.proxy_auth is None
        assert aiohttp_config_obj.proxy_url is None
        assert aiohttp_config_obj.request_timeout is None
        assert aiohttp_config_obj.ssl_context is None
        assert aiohttp_config_obj.verify_ssl is True


class TestTokenConfig:
    def test_deserialize(self, test_token_config):
        token_config_obj = configs.TokenConfig.deserialize(test_token_config)

        assert token_config_obj._token == "token"

    def test_empty_deserialize(self):
        token_config_obj = configs.TokenConfig.deserialize({})

        assert token_config_obj._token is None


class TestWebsocketConfig:
    def test_deserialize(self, test_websocket_config):
        datetime_obj = datetime.datetime.now()
        test_websocket_config["initial_idle_since"] = datetime_obj.timestamp()
        websocket_config_obj = configs.GatewayConfig.deserialize(test_websocket_config)

        assert websocket_config_obj.gateway_use_compression is False
        assert websocket_config_obj.gateway_version == 7
        assert websocket_config_obj.initial_activity == gateway_entities.Activity.deserialize(
            {"name": "test", "url": "some_url", "type": 0}
        )
        assert websocket_config_obj.initial_status == guilds.PresenceStatus.DND
        assert websocket_config_obj.initial_idle_since == datetime_obj
        assert websocket_config_obj.intents == intents.Intent.GUILD_MESSAGES | intents.Intent.GUILDS
        assert websocket_config_obj.large_threshold == 1000
        assert websocket_config_obj.debug is True
        assert websocket_config_obj.allow_redirects is True
        assert websocket_config_obj.tcp_connector == aiohttp.TCPConnector
        assert websocket_config_obj.proxy_headers == {"Some-Header": "headercontent"}
        assert websocket_config_obj.proxy_auth == aiohttp.BasicAuth.decode(
            "basic Tm90aGluZyB0byBzZWUgaGVyZSA6IGpvaW4gZGlzY29yZC5nZy9IS0dQRTlRIDopIH5kYXZmc2E="
        )
        assert websocket_config_obj.proxy_url == "proxy_url"
        assert websocket_config_obj.request_timeout == 100
        assert websocket_config_obj.ssl_context == ssl.SSLContext
        assert websocket_config_obj.verify_ssl is False
        assert websocket_config_obj._token == "token"
        assert websocket_config_obj.shard_ids == [5, 6, 7, 8, 9, 10]
        assert websocket_config_obj.shard_count == 17

    def test_empty_deserialize(self):
        websocket_config_obj = configs.GatewayConfig.deserialize({})

        assert websocket_config_obj.gateway_use_compression is True
        assert websocket_config_obj.gateway_version == 6
        assert websocket_config_obj.initial_activity is None
        assert websocket_config_obj.initial_status == guilds.PresenceStatus.ONLINE
        assert websocket_config_obj.initial_idle_since is None
        assert websocket_config_obj.intents is None
        assert websocket_config_obj.large_threshold == 250
        assert websocket_config_obj.debug is False
        assert websocket_config_obj.allow_redirects is False
        assert websocket_config_obj.tcp_connector is None
        assert websocket_config_obj.proxy_headers is None
        assert websocket_config_obj.proxy_auth is None
        assert websocket_config_obj.proxy_url is None
        assert websocket_config_obj.request_timeout is None
        assert websocket_config_obj.ssl_context is None
        assert websocket_config_obj.verify_ssl is True
        assert websocket_config_obj._token is None
        assert websocket_config_obj.shard_ids is None
        assert websocket_config_obj.shard_count is None


class TestParseShardInfo:
    def test__parse_shard_info_when_exclusive_range(self):
        assert configs._parse_shard_info("0..2") == [0, 1]

    def test__parse_shard_info_when_inclusive_range(self):
        assert configs._parse_shard_info("0...2") == [0, 1, 2]

    def test__parse_shard_info_when_specific_id(self):
        assert configs._parse_shard_info(2) == [2]

    def test__parse_shard_info_when_list(self):
        assert configs._parse_shard_info([2, 5, 6]) == [2, 5, 6]

    @_helpers.assert_raises(type_=ValueError)
    def test__parse_shard_info_when_invalid(self):
        configs._parse_shard_info("something invalid")


class TestRESTConfig:
    def test_deserialize(self, test_rest_config):
        rest_config_obj = configs.RESTConfig.deserialize(test_rest_config)

        assert rest_config_obj.rest_version == 6
        assert rest_config_obj.allow_redirects is True
        assert rest_config_obj.tcp_connector == aiohttp.TCPConnector
        assert rest_config_obj.proxy_headers == {"Some-Header": "headercontent"}
        assert rest_config_obj.proxy_auth == aiohttp.BasicAuth.decode(
            "basic Tm90aGluZyB0byBzZWUgaGVyZSA6IGpvaW4gZGlzY29yZC5nZy9IS0dQRTlRIDopIH5kYXZmc2E="
        )
        assert rest_config_obj.proxy_url == "proxy_url"
        assert rest_config_obj.request_timeout == 100
        assert rest_config_obj.ssl_context == ssl.SSLContext
        assert rest_config_obj.verify_ssl is False
        assert rest_config_obj._token == "token"

    def test_empty_deserialize(self):
        rest_config_obj = configs.RESTConfig.deserialize({})

        assert rest_config_obj.rest_version == 7
        assert rest_config_obj.allow_redirects is False
        assert rest_config_obj.tcp_connector is None
        assert rest_config_obj.proxy_headers is None
        assert rest_config_obj.proxy_auth is None
        assert rest_config_obj.proxy_url is None
        assert rest_config_obj.request_timeout is None
        assert rest_config_obj.ssl_context is None
        assert rest_config_obj.verify_ssl is True
        assert rest_config_obj._token is None


class TestBotConfig:
    def test_deserialize(self, test_bot_config):
        datetime_obj = datetime.datetime.now()
        test_bot_config["initial_idle_since"] = datetime_obj.timestamp()
        bot_config_obj = configs.BotConfig.deserialize(test_bot_config)

        assert bot_config_obj.rest_version == 6
        assert bot_config_obj.allow_redirects is True
        assert bot_config_obj.tcp_connector == aiohttp.TCPConnector
        assert bot_config_obj.proxy_headers == {"Some-Header": "headercontent"}
        assert bot_config_obj.proxy_auth == aiohttp.BasicAuth.decode(
            "basic Tm90aGluZyB0byBzZWUgaGVyZSA6IGpvaW4gZGlzY29yZC5nZy9IS0dQRTlRIDopIH5kYXZmc2E="
        )
        assert bot_config_obj.proxy_url == "proxy_url"
        assert bot_config_obj.request_timeout == 100
        assert bot_config_obj.ssl_context == ssl.SSLContext
        assert bot_config_obj.verify_ssl is False
        assert bot_config_obj._token == "token"
        assert bot_config_obj.shard_ids == [5, 6, 7, 8, 9, 10]
        assert bot_config_obj.shard_count == 17
        assert bot_config_obj.gateway_use_compression is False
        assert bot_config_obj.gateway_version == 7
        assert bot_config_obj.initial_activity == gateway_entities.Activity.deserialize(
            {"name": "test", "url": "some_url", "type": 0}
        )
        assert bot_config_obj.initial_status == guilds.PresenceStatus.DND
        assert bot_config_obj.initial_idle_since == datetime_obj
        assert bot_config_obj.intents == intents.Intent.GUILD_MESSAGES | intents.Intent.GUILDS
        assert bot_config_obj.large_threshold == 1000
        assert bot_config_obj.debug is True

    def test_empty_deserialize(self):
        bot_config_obj = configs.BotConfig.deserialize({})

        assert bot_config_obj.rest_version == 7
        assert bot_config_obj.allow_redirects is False
        assert bot_config_obj.tcp_connector is None
        assert bot_config_obj.proxy_headers is None
        assert bot_config_obj.proxy_auth is None
        assert bot_config_obj.proxy_url is None
        assert bot_config_obj.request_timeout is None
        assert bot_config_obj.ssl_context is None
        assert bot_config_obj.verify_ssl is True
        assert bot_config_obj._token is None
        assert bot_config_obj.shard_ids is None
        assert bot_config_obj.shard_count is None
        assert bot_config_obj.gateway_use_compression is True
        assert bot_config_obj.gateway_version == 6
        assert bot_config_obj.initial_activity is None
        assert bot_config_obj.initial_status == guilds.PresenceStatus.ONLINE
        assert bot_config_obj.initial_idle_since is None
        assert bot_config_obj.intents is None
        assert bot_config_obj.large_threshold == 250
        assert bot_config_obj.debug is False
