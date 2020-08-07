# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Various strings used in multiple places."""

from __future__ import annotations

import platform
import typing

import aiohttp

from hikari import _about

# Headers.
ACCEPT_HEADER: typing.Final[str] = "Accept"
AUTHORIZATION_HEADER: typing.Final[str] = "Authorization"
CF_RAY_HEADER: typing.Final[str] = "CF-Ray"
CF_REQUEST_ID_HEADER: typing.Final[str] = "CF-Request-ID"
CONTENT_LENGTH_HEADER: typing.Final[str] = "Content-Length"
CONTENT_TYPE_HEADER: typing.Final[str] = "Content-Type"
DATE_HEADER: typing.Final[str] = "Date"
PROXY_AUTHENTICATION_HEADER: typing.Final[str] = "Proxy-Authentication"
USER_AGENT_HEADER: typing.Final[str] = "User-Agent"
X_AUDIT_LOG_REASON_HEADER: typing.Final[str] = "X-Audit-Log-Reason"
X_RATELIMIT_BUCKET_HEADER: typing.Final[str] = "X-RateLimit-Bucket"
X_RATELIMIT_LIMIT_HEADER: typing.Final[str] = "X-RateLimit-Limit"
X_RATELIMIT_PRECISION_HEADER: typing.Final[str] = "X-RateLimit-Precision"
X_RATELIMIT_REMAINING_HEADER: typing.Final[str] = "X-RateLimit-Remaining"
X_RATELIMIT_RESET_HEADER: typing.Final[str] = "X-RateLimit-Reset"
X_RATELIMIT_RESET_AFTER_HEADER: typing.Final[str] = "X-RateLimit-Reset-After"

# Mimetypes.
APPLICATION_JSON: typing.Final[str] = "application/json"
APPLICATION_XML: typing.Final[str] = "application/xml"
APPLICATION_OCTET_STREAM: typing.Final[str] = "application/octet-stream"

# Bits of text.
BASICAUTH_TOKEN: typing.Final[str] = "Basic"  # nosec
BEARER_TOKEN: typing.Final[str] = "Bearer"  # nosec
BOT_TOKEN: typing.Final[str] = "Bot"  # nosec
MILLISECOND_PRECISION: typing.Final[str] = "millisecond"

# User-agent info.
AIOHTTP_VERSION: typing.Final[str] = f"aiohttp {aiohttp.__version__}"
LIBRARY_VERSION: typing.Final[str] = f"hikari {_about.__version__}"
SYSTEM_TYPE: typing.Final[str] = f"{platform.system()} {platform.architecture()[0]}"
HTTP_USER_AGENT: typing.Final[str] = (
    f"DiscordBot ({_about.__url__}, {_about.__version__}) {_about.__author__} "
    f"Aiohttp/{aiohttp.__version__} "
    f"{platform.python_implementation()}/{platform.python_version()} {SYSTEM_TYPE}"
)
PYTHON_PLATFORM_VERSION: typing.Final[str] = (
    f"{platform.python_implementation()} {platform.python_version()} "
    f"{platform.python_branch()} {platform.python_compiler()}"
).replace(" " * 2, " ")

# URLs
BASE_URL: typing.Final[str] = "https://discord.com"
REST_API_URL: typing.Final[str] = BASE_URL + "/api/v{0.version}"  # noqa: FS003  fstring missing prefix
OAUTH2_API_URL: typing.Final[str] = f"{REST_API_URL}/oauth2"
CDN_URL: typing.Final[str] = "https://cdn.discordapp.com"
TWEMOJI_PNG_BASE_URL: typing.Final[str] = "https://github.com/twitter/twemoji/raw/master/assets/72x72/"
TWEMOJI_SVG_BASE_URL: typing.Final[str] = "https://github.com/twitter/twemoji/raw/master/assets/svg/"

__all__: typing.Final[typing.List[str]] = [attr for attr in globals() if not any(c.islower() for c in attr)]
