# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Data class containing network-related configuration settings."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "BasicAuthHeader",
    "ProxySettings",
    "HTTPTimeoutSettings",
    "HTTPSettings",
    "CacheSettings",
)

import base64
import ssl as ssl_
import typing

import attr

from hikari.api import config
from hikari.internal import attr_extensions
from hikari.internal import data_binding

_BASICAUTH_TOKEN_PREFIX: typing.Final[str] = "Basic"  # nosec
_PROXY_AUTHENTICATION_HEADER: typing.Final[str] = "Proxy-Authentication"


def _ssl_factory(value: typing.Union[bool, ssl_.SSLContext]) -> ssl_.SSLContext:
    if not isinstance(value, bool):
        return value

    ssl = ssl_.create_default_context()
    # We can't turn SSL verification off without disabling hostname verification first.
    # If we are using verification, this will just leave it enabled, so it is fine.
    ssl.check_hostname = value
    ssl.verify_mode = ssl_.CERT_REQUIRED if value else ssl_.CERT_NONE
    return ssl


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=True, weakref_slot=False)
class BasicAuthHeader:
    """An object that can be set as a producer for a basic auth header."""

    username: str = attr.field(validator=attr.validators.instance_of(str))
    """Username for the header.

    .. warning::
        This must not contain `":"`.
    """

    password: str = attr.field(repr=False, validator=attr.validators.instance_of(str))
    """Password to use."""

    charset: str = attr.field(default="utf-8", validator=attr.validators.instance_of(str))
    """Encoding to use for the username and password.

    Default is `"utf-8"`, but you may choose to use something else,
    including third-party encodings (e.g. IBM's EBCDIC codepages).
    """

    @property
    def header(self) -> str:
        """Create the full `Authentication` header value."""
        raw_token = f"{self.username}:{self.password}".encode(self.charset)
        token_part = base64.b64encode(raw_token).decode(self.charset)
        return f"{_BASICAUTH_TOKEN_PREFIX} {token_part}"

    def __str__(self) -> str:
        return self.header


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class ProxySettings(config.ProxySettings):
    """Settings for configuring an HTTP-based proxy."""

    auth: typing.Any = attr.field(default=None)
    """Authentication header value to use.

    When cast to a `str`, this should provide the full value
    for the authentication header.

    If you are using basic auth, you should consider using the
    `BasicAuthHeader` helper object here, as this will provide any
    transformations you may require into a base64 string.

    The default is to have this set to `None`, which will
    result in no authentication being provided.
    """

    headers: typing.Optional[data_binding.Headers] = attr.field(default=None)
    """Additional headers to use for requests via a proxy, if required."""

    url: typing.Union[None, str] = attr.field(default=None)
    """Proxy URL to use.

    Defaults to `None` which disables the use of an explicit proxy.
    """

    trust_env: bool = attr.field(default=False, validator=attr.validators.instance_of(bool))
    """Toggle whether to look for a `netrc` file or environment variables.

    If `True`, and no `url` is given on this object, then
    `HTTP_PROXY` and `HTTPS_PROXY` will be used from the environment
    variables, or a `netrc` file may be read to determine credentials.

    If `False`, then this information is instead ignored.

    Defaults to `False` to prevent potentially unwanted behavior.

    .. note::
        For more details of using `netrc`, visit:
        <https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html>
    """

    @property
    def all_headers(self) -> typing.Optional[data_binding.Headers]:
        """Return all proxy headers.

        Will be `None` if no headers are to be send with any request.
        """
        if self.headers is None:
            if self.auth is None:
                return None
            return {_PROXY_AUTHENTICATION_HEADER: self.auth}

        if self.auth is None:
            return self.headers
        return {**self.headers, _PROXY_AUTHENTICATION_HEADER: self.auth}


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class HTTPTimeoutSettings:
    """Settings to control HTTP request timeouts."""

    acquire_and_connect: typing.Optional[float] = attr.field(default=None)
    """Timeout for `request_socket_connect` PLUS connection acquisition.

    By default, this has no timeout allocated. Setting it to `None`
    will disable it.
    """

    request_socket_connect: typing.Optional[float] = attr.field(default=None)
    """Timeout for connecting a socket.

    By default, this has no timeout allocated. Setting it to `None`
    will disable it.
    """

    request_socket_read: typing.Optional[float] = attr.field(default=None)
    """Timeout for reading a socket.

    By default, this has no timeout allocated. Setting it to `None`
    will disable it.
    """

    total: typing.Optional[float] = attr.field(default=30.0)
    """Total timeout for entire request.

    By default, this has a 30 second timeout allocated. Setting it to `None`
    will disable it.
    """

    @acquire_and_connect.validator
    @request_socket_connect.validator
    @request_socket_read.validator
    @total.validator
    def _(self, attrib: attr.Attribute[typing.Optional[float]], value: typing.Any) -> None:
        # This error won't occur until some time in the future where it will be annoying to
        # try and determine the root cause, so validate it NOW.
        if value is not None and (not isinstance(value, (float, int)) or value <= 0):
            raise ValueError(f"HTTPTimeoutSettings.{attrib.name} must be None, or a POSITIVE float/int")


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class HTTPSettings(config.HTTPSettings):
    """Settings to control HTTP clients."""

    enable_cleanup_closed: bool = attr.field(default=True, validator=attr.validators.instance_of(bool))
    """Toggle whether to clean up closed transports.

    This defaults to `True` to combat various protocol and asyncio
    issues present when using Microsoft Windows. If you are sure you know
    what you are doing, you may instead set this to `False` to disable this
    behavior internally.
    """

    force_close_transports: bool = attr.field(default=True, validator=attr.validators.instance_of(bool))
    """Toggle whether to force close transports on shut down.

    This defaults to `True` to combat various protocol and asyncio
    issues present when using Microsoft Windows. If you are sure you know
    what you are doing, you may instead set this to `False` to disable this
    behavior internally.
    """

    max_redirects: typing.Optional[int] = attr.field(default=10)
    """Behavior for handling redirect HTTP responses.

    If a `int`, allow following redirects from `3xx` HTTP responses
    for up to this many redirects. Exceeding this value will raise an
    exception.

    If `None`, then disallow any redirects.

    The default is to disallow this behavior for security reasons.

    Generally, it is safer to keep this disabled. You may find a case in the
    future where you need to enable this if Discord change their URL without
    warning.

    .. note::
        This will only apply to the REST API. WebSockets remain unaffected
        by any value set here.
    """

    @max_redirects.validator
    def _(self, _: attr.Attribute[typing.Optional[int]], value: typing.Any) -> None:
        # This error won't occur until some time in the future where it will be annoying to
        # try and determine the root cause, so validate it NOW.
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise ValueError("http_settings.max_redirects must be None or a POSITIVE integer")

    ssl: ssl_.SSLContext = attr.field(
        factory=lambda: _ssl_factory(True),
        converter=_ssl_factory,
        validator=attr.validators.instance_of(ssl_.SSLContext),
    )
    """SSL context to use.

    This may be assigned a `bool` or an `ssl.SSLContext` object.

    If assigned to `True`, a default SSL context is generated by
    this class that will enforce SSL verification. This is then stored in
    this field.

    If `False`, then a default SSL context is generated by this
    class that will **NOT** enforce SSL verification. This is then stored
    in this field.

    If an instance of `ssl.SSLContext`, then this context will be used.

    .. warning::
        Setting a custom value here may have security implications, or
        may result in the application being unable to connect to Discord
        at all.

    .. warning::
        Disabling SSL verification is almost always unadvised. This
        is because your application will no longer check whether you are
        connecting to Discord, or to some third party spoof designed
        to steal personal credentials such as your application token.

        There may be cases where SSL certificates do not get updated,
        and in this case, you may find that disabling this explicitly
        allows you to work around any issues that are occurring, but
        you should immediately seek a better solution where possible
        if any form of personal security is in your interest.
    """

    timeouts: HTTPTimeoutSettings = attr.field(
        factory=HTTPTimeoutSettings, validator=attr.validators.instance_of(HTTPTimeoutSettings)
    )
    """Settings to control HTTP request timeouts.

    The behaviour if this is not explicitly defined is to use sane
    defaults that are most efficient for optimal use of this library.
    """


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class CacheSettings(config.CacheSettings):
    """Settings to control the cache."""

    components: config.CacheComponents = attr.field(
        converter=config.CacheComponents, default=config.CacheComponents.ALL
    )
    """The cache components to use.

    Defaults to `hikari.api.cache.CacheComponents.ALL`.
    """

    max_messages: int = attr.field(default=300)
    """The maximum number of messages to store in the cache at once.

    This will have no effect if the messages cache is not enabled.

    Defaults to `300`.
    """

    max_dm_channel_ids: int = attr.field(default=50)
    """The maximum number of channel IDs to store in the cache at once.

    This will have no effect if the channel IDs cache is not enabled.

    Defaults to `50`.
    """
