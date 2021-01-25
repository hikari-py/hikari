# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = [
    "BasicAuthHeader",
    "ProxySettings",
    "HTTPTimeoutSettings",
    "HTTPSettings",
    "CacheSettings",
]

import base64
import ssl as ssl_
import typing

import attr
import yarl

from hikari.internal import attr_extensions
from hikari.internal import data_binding

_BASICAUTH_TOKEN_PREFIX: typing.Final[str] = "Basic"  # nosec
_PROXY_AUTHENTICATION_HEADER: typing.Final[str] = "Proxy-Authentication"


def _ssl_factory(value: typing.Union[bool, ssl_.SSLContext]) -> ssl_.SSLContext:
    if isinstance(value, bool):
        ssl = ssl_.create_default_context()
        # We can't turn SSL verification off without disabling hostname verification first.
        # If we are using verification, this will just leave it enabled, so it is fine.
        ssl.check_hostname = value
        ssl.verify_mode = ssl_.CERT_REQUIRED if value else ssl_.CERT_NONE
    else:
        ssl = value
    return ssl


@attr_extensions.with_copy
@attr.s(slots=True, kw_only=True, repr=True, weakref_slot=False)
class BasicAuthHeader:
    """An object that can be set as a producer for a basic auth header."""

    username: str = attr.ib(validator=attr.validators.instance_of(str))
    """Username for the header.

    Returns
    -------
    builtins.str
        The username to use. This must not contain `":"`.
    """

    password: str = attr.ib(repr=False, validator=attr.validators.instance_of(str))
    """Password to use.

    Returns
    -------
    builtins.str
        The password to use.
    """

    charset: str = attr.ib(default="utf-8", validator=attr.validators.instance_of(str))
    """Encoding to use for the username and password.

    Default is `"utf-8"`, but you may choose to use something else,
    including third-party encodings (e.g. IBM's EBCDIC codepages).

    Returns
    -------
    builtins.str
        The encoding to use.
    """

    @property
    def header(self) -> str:
        """Create the full `Authentication` header value.

        Returns
        -------
        builtins.str
            A base64-encoded string containing
            `"{username}:{password}"`.
        """
        raw_token = f"{self.username}:{self.password}".encode(self.charset)
        token_part = base64.b64encode(raw_token).decode(self.charset)
        return f"{_BASICAUTH_TOKEN_PREFIX} {token_part}"

    def __str__(self) -> str:
        return self.header


@attr_extensions.with_copy
@attr.s(slots=True, kw_only=True, weakref_slot=False)
class ProxySettings:
    """Settings for configuring an HTTP-based proxy."""

    auth: typing.Any = attr.ib(default=None)
    """Authentication header value to use.

    When cast to a `builtins.str`, this should provide the full value
    for the authentication header.

    If you are using basic auth, you should consider using the
    `BasicAuthHeader` helper object here, as this will provide any
    transformations you may require into a base64 string.

    The default is to have this set to `builtins.None`, which will
    result in no authentication being provided.

    Returns
    -------
    typing.Any
        The value for the `Authentication` header, or `builtins.None`
        to disable.
    """

    headers: typing.Optional[data_binding.Headers] = attr.ib(default=None)
    """Additional headers to use for requests via a proxy, if required."""

    url: typing.Union[None, str, yarl.URL] = attr.ib(default=None)
    """Proxy URL to use.

    Defaults to `builtins.None` which disables the use of an explicit proxy.

    Returns
    -------
    typing.Union[builtins.None, builtins.str, yarl.URL]
        The proxy URL to use, or `builtins.None` to disable it.
    """

    @url.validator
    def _(self, _: attr.Attribute[typing.Optional[str]], value: typing.Optional[str]) -> None:
        if value is not None and not isinstance(value, (str, yarl.URL)):
            raise TypeError("ProxySettings.url must be None, a str, or a yarl.URL instance")

    trust_env: bool = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    """Toggle whether to look for a `netrc` file or environment variables.

    If `builtins.True`, and no `url` is given on this object, then
    `HTTP_PROXY` and `HTTPS_PROXY` will be used from the environment
    variables, or a `netrc` file may be read to determine credentials.

    If `builtins.False`, then this information is instead ignored.

    Defaults to `builtins.False` to prevent potentially unwanted behavior.

    !!! note
        For more details of using `netrc`, visit:
        https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html

    Returns
    -------
    builtins.bool
        `builtins.True` if allowing the use of environment variables
        and/or `netrc` to determine proxy settings; `builtins.False`
        if this should be disabled explicitly.
    """

    @property
    def all_headers(self) -> typing.Optional[data_binding.Headers]:
        """Return all proxy headers.

        Returns
        -------
        typing.Optional[hikari.internal.data_binding.Headers]
            Any headers that are set, or `builtins.None` if no headers are to
            be sent with any request.
        """
        if self.headers is None:
            if self.auth is None:
                return None
            return {_PROXY_AUTHENTICATION_HEADER: self.auth}

        if self.auth is None:
            return self.headers
        return {**self.headers, _PROXY_AUTHENTICATION_HEADER: self.auth}


@attr_extensions.with_copy
@attr.s(slots=True, kw_only=True, weakref_slot=False)
class HTTPTimeoutSettings:
    """Settings to control HTTP request timeouts."""

    acquire_and_connect: typing.Optional[float] = attr.ib(default=None)
    """Timeout for `request_socket_connect` PLUS connection acquisition.

    By default, this has no timeout allocated.

    Returns
    -------
    typing.Optional[builtins.float]
        The timeout, or `builtins.None` to disable it.
    """

    request_socket_connect: typing.Optional[float] = attr.ib(default=None)
    """Timeout for connecting a socket.

    By default, this has no timeout allocated.

    Returns
    -------
    typing.Optional[builtins.float]
        The timeout, or `builtins.None` to disable it.
    """

    request_socket_read: typing.Optional[float] = attr.ib(default=None)
    """Timeout for reading a socket.

    By default, this has no timeout allocated.

    Returns
    -------
    typing.Optional[builtins.float]
        The timeout, or `builtins.None` to disable it.
    """

    total: typing.Optional[float] = attr.ib(default=30.0)
    """Total timeout for entire request.

    By default, this has a 30 second timeout allocated.

    Returns
    -------
    typing.Optional[builtins.float]
        The timeout, or `builtins.None` to disable it.
    """

    @acquire_and_connect.validator
    @request_socket_connect.validator
    @request_socket_read.validator
    @total.validator
    def _(self, attrib: attr.Attribute[typing.Optional[float]], value: typing.Optional[float]) -> None:
        # This error won't occur until some time in the future where it will be annoying to
        # try and determine the root cause, so validate it NOW.
        if value is not None and (not isinstance(value, (float, int)) or value <= 0):
            raise ValueError(f"HTTPTimeoutSettings.{attrib.name} must be None, or a POSITIVE float/int")


@attr_extensions.with_copy
@attr.s(slots=True, kw_only=True, weakref_slot=False)
class HTTPSettings:
    """Settings to control HTTP clients."""

    enable_cleanup_closed: bool = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    """Toggle whether to clean up closed transports.

    This defaults to `builtins.True` to combat various protocol and asyncio
    issues present when using Microsoft Windows. If you are sure you know
    what you are doing, you may instead set this to `False` to disable this
    behavior internally.

    Returns
    -------
    builtins.bool
        `builtins.True` to enable this behavior, `builtins.False` to disable
        it.
    """

    force_close_transports: bool = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    """Toggle whether to force close transports on shutdown.

    This defaults to `builtins.True` to combat various protocol and asyncio
    issues present when using Microsoft Windows. If you are sure you know
    what you are doing, you may instead set this to `False` to disable this
    behavior internally.

    Returns
    -------
    builtins.bool
        `builtins.True` to enable this behavior, `builtins.False` to disable
        it.
    """

    max_redirects: typing.Optional[int] = attr.ib(default=10)
    """Behavior for handling redirect HTTP responses.

    If a `builtins.int`, allow following redirects from `3xx` HTTP responses
    for up to this many redirects. Exceeding this value will raise an
    exception.

    If `builtins.None`, then disallow any redirects.

    The default is to disallow this behavior for security reasons.

    Generally, it is safer to keep this disabled. You may find a case in the
    future where you need to enable this if Discord change their URL without
    warning.

    !!! note
        This will only apply to the REST API. WebSockets remain unaffected
        by any value set here.

    Returns
    -------
    typing.Optional[builtins.int]
        The number of redirects to allow at a maximum per request.
        `builtins.None` disables the handling
        of redirects and will result in exceptions being raised instead
        should one occur.
    """

    @max_redirects.validator
    def _(self, _: attr.Attribute[typing.Optional[int]], value: typing.Optional[int]) -> None:
        # This error won't occur until some time in the future where it will be annoying to
        # try and determine the root cause, so validate it NOW.
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise ValueError("http_settings.max_redirects must be None or a POSITIVE integer")

    _ssl: typing.Union[bool, ssl_.SSLContext] = attr.ib(
        default=True,
        converter=_ssl_factory,
        validator=attr.validators.instance_of(ssl_.SSLContext),  # type: ignore[assignment,arg-type]
    )

    @property
    def ssl(self) -> ssl_.SSLContext:
        ssl = self._ssl
        assert isinstance(ssl, ssl_.SSLContext), "conversion logic in hikari for SSL customisation has broken"
        return ssl

    """SSL context to use.

    This may be __assigned__ a `builtins.bool` or an `ssl.SSLContext` object.

    If assigned to `builtins.True`, a default SSL context is generated by
    this class that will enforce SSL verification. This is then stored in
    this field.

    If `builtins.False`, then a default SSL context is generated by this
    class that will **NOT** enforce SSL verification. This is then stored
    in this field.

    If an instance of `ssl.SSLContext`, then this context will be used.

    !!! warning
        Setting a custom value here may have security implications, or
        may result in the application being unable to connect to Discord
        at all.

    !!! warning
        Disabling SSL verification is almost always unadvised. This
        is because your application will no longer check whether you are
        connecting to Discord, or to some third party spoof designed
        to steal personal credentials such as your application token.

        There may be cases where SSL certificates do not get updated,
        and in this case, you may find that disabling this explicitly
        allows you to work around any issues that are occurring, but
        you should immediately seek a better solution where possible
        if any form of personal security is in your interest.

    Returns
    -------
    ssl.SSLContext
        The SSL context to use for this application.
    """

    timeouts: HTTPTimeoutSettings = attr.ib(
        factory=HTTPTimeoutSettings, validator=attr.validators.instance_of(HTTPTimeoutSettings)
    )
    """Settings to control HTTP request timeouts.

    The behaviour if this is not explicitly defined is to use sane
    defaults that are most efficient for optimal use of this library.

    Returns
    -------
    HTTPTimeoutSettings
        The HTTP timeout settings to use for connection timeouts.
    """


@attr_extensions.with_copy
@attr.s(slots=True, kw_only=True, weakref_slot=False)
class CacheSettings:
    """Settings to control the cache."""

    enable: bool = attr.ib(default=True)
    """Whether to enable the cache.

    If set to `False`, all the cache functionality will be disabled.

    Defaults to `builtins.True`.
    """

    guilds: bool = attr.ib(default=True)
    """Whether to enable the guilds cache.

    Defaults to `builtins.True`.
    """

    members: bool = attr.ib(default=True)
    """Whether to enable the members cache.

    Defaults to `builtins.True`.
    """

    guild_channels: bool = attr.ib(default=True)
    """Whether to enable the guild channels cache.

    Defaults to `builtins.True`.
    """

    roles: bool = attr.ib(default=True)
    """Whether to enable the roles cache.

    Defaults to `builtins.True`.
    """

    invites: bool = attr.ib(default=True)
    """Whether to enable the invites cache.

    Defaults to `builtins.True`.
    """

    emojis: bool = attr.ib(default=True)
    """Whether to enable the emojis cache.

    Defaults to `builtins.True`.
    """

    presences: bool = attr.ib(default=True)
    """Whether to enable the presences cache.

    Defaults to `builtins.True`.
    """

    voice_states: bool = attr.ib(default=True)
    """Whether to enable the voice states cache.

    Defaults to `builtins.True`.
    """

    messages: bool = attr.ib(default=True)
    """Whether to enable the message cache.

    Defaults to `builtins.True`.
    """

    max_messages: int = attr.ib(default=300)
    """The max number of messages to store in the cache at once.

    This will have no effect if `messages` is `builtins.False`.

    Defaults to `300`.
    """
