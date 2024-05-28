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

import ssl

import pytest

from hikari.impl import config as config_


class TestSSLFactory:
    def test_when_value_is_True(self):
        returned = config_._ssl_factory(True)

        assert returned.check_hostname is True
        assert returned.verify_mode is ssl.CERT_REQUIRED

    def test_when_value_is_False(self):
        returned = config_._ssl_factory(False)

        assert returned.check_hostname is False
        assert returned.verify_mode is ssl.CERT_NONE

    def test_when_value_is_non_bool(self):
        value = object()
        assert config_._ssl_factory(value) is value


class TestBasicAuthHeader:
    @pytest.fixture
    def config(self):
        return config_.BasicAuthHeader(username="davfsa", password="securepassword123")

    def test_header_property(self, config):
        assert config.header == f"{config_._BASICAUTH_TOKEN_PREFIX} ZGF2ZnNhOnNlY3VyZXBhc3N3b3JkMTIz"

    def test_str(self, config):
        assert str(config) == f"{config_._BASICAUTH_TOKEN_PREFIX} ZGF2ZnNhOnNlY3VyZXBhc3N3b3JkMTIz"


class TestHTTPTimeoutSettings:
    @pytest.mark.parametrize("arg", ["acquire_and_connect", "request_socket_connect", "request_socket_read", "total"])
    def test_max_redirects_validator_when_not_None_nor_int_nor_float(self, arg):
        with pytest.raises(ValueError, match=rf"HTTPTimeoutSettings.{arg} must be None, or a POSITIVE float/int"):
            config_.HTTPTimeoutSettings(**{arg: object()})

    @pytest.mark.parametrize("arg", ["acquire_and_connect", "request_socket_connect", "request_socket_read", "total"])
    def test_max_redirects_validator_when_negative_int(self, arg):
        with pytest.raises(ValueError, match=rf"HTTPTimeoutSettings.{arg} must be None, or a POSITIVE float/int"):
            config_.HTTPTimeoutSettings(**{arg: -1})

    @pytest.mark.parametrize("arg", ["acquire_and_connect", "request_socket_connect", "request_socket_read", "total"])
    def test_max_redirects_validator_when_negative_float(self, arg):
        with pytest.raises(ValueError, match=rf"HTTPTimeoutSettings.{arg} must be None, or a POSITIVE float/int"):
            config_.HTTPTimeoutSettings(**{arg: -1.1})

    @pytest.mark.parametrize("arg", ["acquire_and_connect", "request_socket_connect", "request_socket_read", "total"])
    @pytest.mark.parametrize("value", [1, 1.1, None])
    def test_max_redirects_validator(self, arg, value):
        config_.HTTPTimeoutSettings(**{arg: value})


class TestHTTPSettings:
    def test_max_redirects_validator_when_not_None_nor_int(self):
        with pytest.raises(ValueError, match=r"http_settings.max_redirects must be None or a POSITIVE integer"):
            config_.HTTPSettings(max_redirects=object())

    def test_max_redirects_validator_when_negative(self):
        with pytest.raises(ValueError, match=r"http_settings.max_redirects must be None or a POSITIVE integer"):
            config_.HTTPSettings(max_redirects=-1)

    @pytest.mark.parametrize("value", [1, None])
    def test_max_redirects_validator(self, value):
        config_.HTTPSettings(max_redirects=value)

    def test_ssl(self):
        mock_ssl = ssl.create_default_context()
        config = config_.HTTPSettings(ssl=mock_ssl)

        assert config.ssl is mock_ssl


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
