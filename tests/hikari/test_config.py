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

import pytest

from hikari import config as config_


class TestBasicAuthHeader:
    @pytest.fixture()
    def config(self):
        return config_.BasicAuthHeader(username="davfsa", password="securepassword123")

    def test_header_property(self, config):
        assert config.header == f"{config_._BASICAUTH_TOKEN_PREFIX} ZGF2ZnNhOnNlY3VyZXBhc3N3b3JkMTIz"

    def test_str(self, config):
        assert str(config) == f"{config_._BASICAUTH_TOKEN_PREFIX} ZGF2ZnNhOnNlY3VyZXBhc3N3b3JkMTIz"


class TestProxySettings:
    def test_all_headers_when_headers_and_auth_are_None(self):
        config = config_.ProxySettings(headers=None, auth=None)
        assert config.all_headers is None

    def test_all_headers_when_headers_is_None_and_auth_is_not_None(self):
        config = config_.ProxySettings(headers=None, auth="some auth")
        assert config.all_headers == {config_._PROXY_AUTHENTICATION_HEADER: "some auth"}

    def test_all_headers_when_headers_is_not_None_and_auth_is_None(self):
        config = config_.ProxySettings(headers={"header1": "header1 info"}, auth=None)
        assert config.all_headers == {"header1": "header1 info"}

    def test_all_headers_when_headers_and_auth_are_not_None(self):
        config = config_.ProxySettings(headers={"header1": "header1 info"}, auth="some auth")
        assert config.all_headers == {"header1": "header1 info", config_._PROXY_AUTHENTICATION_HEADER: "some auth"}
