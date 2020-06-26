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
"""Various strings used in multiple places."""

from __future__ import annotations

import platform
import typing

import aiohttp

import hikari

# Headers.
ACCEPT_HEADER: typing.Final[str] = "Accept"
AUTHORIZATION_HEADER: typing.Final[str] = "Authorization"
CF_RAY_HEADER: typing.Final[str] = "CF-Ray"
CF_REQUEST_ID_HEADER: typing.Final[str] = "CF-Request-ID"
CONTENT_LENGTH_HEADER: typing.Final[str] = "Content-Length"
CONTENT_TYPE_HEADER: typing.Final[str] = "Content-Type"
DATE_HEADER: typing.Final[str] = "Date"
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
BEARER_TOKEN: typing.Final[str] = "Bearer"  # nosec
BOT_TOKEN: typing.Final[str] = "Bot"  # nosec
MILLISECOND_PRECISION: typing.Final[str] = "millisecond"

# User-agent info.
AIOHTTP_VERSION: typing.Final[str] = f"aiohttp {aiohttp.__version__}"
LIBRARY_VERSION: typing.Final[str] = f"hikari {hikari.__version__}"
SYSTEM_TYPE: typing.Final[str] = f"{platform.system()} {platform.architecture()[0]}"
HTTP_USER_AGENT: typing.Final[str] = (
    f"DiscordBot ({hikari.__url__}, {hikari.__version__}) {hikari.__author__} "
    f"Aiohttp/{aiohttp.__version__} "
    f"{platform.python_implementation()}/{platform.python_version()} {SYSTEM_TYPE}"
)
PYTHON_PLATFORM_VERSION: typing.Final[str] = (
    f"{platform.python_implementation()} {platform.python_version()} "
    f"{platform.python_branch()} {platform.python_compiler()}"
).replace(" " * 2, " ")

# URLs
REST_API_URL: typing.Final[str] = "https://discord.com/api/v{0.version}"  # noqa: FS003  fstring missing prefix
OAUTH2_API_URL: typing.Final[str] = f"{REST_API_URL}/oauth2"
CDN_URL: typing.Final[str] = "https://cdn.discordapp.com"

__all__: typing.Final[typing.Sequence[str]] = [attr for attr in globals() if not any(c.islower() for c in attr)]
