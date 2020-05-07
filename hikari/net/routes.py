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
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Provides the valid routes that can be used on the API, as well as mechanisms to aid with rate limit bucketing."""

from __future__ import annotations

__all__ = ["CompiledRoute", "RouteTemplate"]

import re
import typing

DEFAULT_MAJOR_PARAMS: typing.Final[typing.Set[str]] = {"channel_id", "guild_id", "webhook_id"}
HASH_SEPARATOR: typing.Final[str] = ";"


class CompiledRoute:
    """A compiled representation of a route ready to be made into a full e and to be used for a request.

    Parameters
    ----------
    route_template : RouteTemplate
        The route template used to make this route.
    path : str
        The path with any major parameters interpolated in.
    major_params_hash : str
        The part of the hash identifier to use for the compiled set of major parameters.
    """

    __slots__ = ("route_template", "major_param_hash", "compiled_path", "hash_code")

    route_template: typing.Final[RouteTemplate]
    """The route template this compiled route was created from."""

    major_param_hash: typing.Final[str]
    """The major parameters in a bucket hash-compatible representation."""

    compiled_path: typing.Final[str]
    """The compiled route path to use."""

    hash_code: typing.Final[int]
    """The hash code."""

    def __init__(self, route_template: RouteTemplate, path: str, major_params_hash: str) -> None:
        self.route_template = route_template
        self.major_param_hash = major_params_hash
        self.compiled_path = path
        self.hash_code = hash((self.method, self.route_template.path_template, major_params_hash))

    @property
    def method(self) -> str:
        """Return the HTTP method of this compiled route."""
        return self.route_template.method

    def create_url(self, base_url: str) -> str:
        """Create the full URL with which you can make a request.

        Parameters
        ----------
        base_url : str
            The base of the URL to prepend to the compiled path.

        Returns
        -------
        str
            The full URL for the route.
        """
        return base_url + self.compiled_path

    def create_real_bucket_hash(self, initial_bucket_hash: str) -> str:
        """Create a full bucket hash from a given initial hash.

        The result of this hash will be decided by the value of the major
        parameters passed to the route during the compilation phase.

        Parameters
        ----------
        initial_bucket_hash : str
            The initial bucket hash provided by Discord in the HTTP headers
            for a given response.

        Returns
        -------
        str
            The input hash amalgamated with a hash code produced by the
            major parameters in this compiled route instance.
        """
        return initial_bucket_hash + HASH_SEPARATOR + self.major_param_hash

    def __hash__(self) -> int:
        return self.hash_code

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, CompiledRoute)
            and self.route_template == other.route_template
            and self.major_param_hash == other.major_param_hash
            and self.compiled_path == other.compiled_path
            and self.hash_code == other.hash_code
        )

    def __repr__(self) -> str:
        this_type = type(self).__name__
        major_params = ", ".join(
            (
                f"method={self.method!r}",
                f"compiled_path={self.compiled_path!r}",
                f"major_params_hash={self.major_param_hash!r}",
            )
        )
        return f"{this_type}({major_params})"

    def __str__(self) -> str:
        return f"{self.method} {self.compiled_path}"


class RouteTemplate:
    """A template used to create compiled routes for specific parameters.

    These compiled routes are used to identify rate limit buckets. Compiled
    routes may have a single major parameter.

    Parameters
    ----------
    method : str
        The HTTP method
    path_template : str
        The template string for the path to use.
    """

    _MAJOR_PARAM_REGEX = re.compile(r"\{(.*?)\}")

    __slots__ = ("method", "path_template", "major_param", "hash_code")

    method: str
    """The HTTP method."""

    path_template: typing.Final[str]
    """The template string used for the path."""

    major_param: typing.Final[typing.Optional[str]]
    """The optional major parameter name."""

    hash_code: typing.Final[int]
    """The hash code."""

    def __init__(self, method: str, path_template: str) -> None:
        self.method = method
        self.path_template = path_template

        if match := self._MAJOR_PARAM_REGEX.search(path_template):
            self.major_param = match.group(1)
        else:
            self.major_param = None

        self.hash_code = hash((self.method, self.path_template))

    def compile(self, **kwargs: typing.Any) -> CompiledRoute:
        """Generate a formatted `CompiledRoute` for this route template.

        This takes into account any URL parameters that have been passed.

        Parameters
        ----------
        **kwargs : typing.Any
            Any parameters to interpolate into the route path.

        Returns
        -------
        CompiledRoute
            The compiled route.
        """
        return CompiledRoute(
            self,
            self.path_template.format_map(kwargs),
            str(kwargs[self.major_param]) if self.major_param is not None else "-",
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(path_template={self.path_template!r}, major_param={self.major_param!r})"

    def __str__(self) -> str:
        return self.path_template

    def __hash__(self) -> int:
        return self.hash_code

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, RouteTemplate)
            and self.method == other.method
            and self.major_param == other.major_param
            and self.path_template == other.path_template
            and self.hash_code == other.hash_code
        )


GET = "GET"
PATCH = "PATCH"
DELETE = "DELETE"
PUT = "PUT"
POST = "POST"

# Channels
GET_CHANNEL = RouteTemplate(GET, "/channels/{channel_id}")
PATCH_CHANNEL = RouteTemplate(PATCH, "/channels/{channel_id}")
DELETE_CHANNEL = RouteTemplate(DELETE, "/channels/{channel_id}")

GET_CHANNEL_INVITES = RouteTemplate(GET, "/channels/{channel_id}/invites")
POST_CHANNEL_INVITES = RouteTemplate(POST, "/channels/{channel_id}/invites")

GET_CHANNEL_MESSAGE = RouteTemplate(GET, "/channels/{channel_id}/messages/{message_id}")
PATCH_CHANNEL_MESSAGE = RouteTemplate(PATCH, "/channels/{channel_id}/messages/{message_id}")
DELETE_CHANNEL_MESSAGE = RouteTemplate(DELETE, "/channels/{channel_id}/messages/{message_id}")

GET_CHANNEL_MESSAGES = RouteTemplate(GET, "/channels/{channel_id}/messages")
POST_CHANNEL_MESSAGES = RouteTemplate(POST, "/channels/{channel_id}/messages")

POST_DELETE_CHANNEL_MESSAGES_BULK = RouteTemplate(POST, "/channels/{channel_id}/messages")

PATCH_CHANNEL_PERMISSIONS = RouteTemplate(PATCH, "/channels/{channel_id}/permissions/{overwrite_id}")
DELETE_CHANNEL_PERMISSIONS = RouteTemplate(DELETE, "/channels/{channel_id}/permissions/{overwrite_id}")

DELETE_CHANNEL_PIN = RouteTemplate(DELETE, "/channels/{channel_id}/pins/{message_id}")

GET_CHANNEL_PINS = RouteTemplate(GET, "/channels/{channel_id}/pins")
PUT_CHANNEL_PINS = RouteTemplate(PUT, "/channels/{channel_id}/pins")

POST_CHANNEL_TYPING = RouteTemplate(POST, "/channels/{channel_id}/typing")

POST_CHANNEL_WEBHOOKS = RouteTemplate(POST, "/channels/{channel_id}/webhooks")
GET_CHANNEL_WEBHOOKS = RouteTemplate(GET, "/channels/{channel_id}/webhooks")

# Reactions
DELETE_ALL_REACTIONS = RouteTemplate(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions")

DELETE_REACTION_EMOJI = RouteTemplate(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")
DELETE_REACTION_USER = RouteTemplate(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{used_id}")
GET_REACTIONS = RouteTemplate(GET, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")

# Guilds
GET_GUILD = RouteTemplate(GET, "/guilds/{guild_id}")
PATCH_GUILD = RouteTemplate(PATCH, "/guilds/{guild_id}")
DELETE_GUILD = RouteTemplate(DELETE, "/guilds/{guild_id}")

POST_GUILDS = RouteTemplate(POST, "/guilds")

GET_GUILD_AUDIT_LOGS = RouteTemplate(GET, "/guilds/{guild_id}/audit-logs")

GET_GUILD_BAN = RouteTemplate(GET, "/guilds/{guild_id}/bans/{user_id}")
PUT_GUILD_BAN = RouteTemplate(PUT, "/guilds/{guild_id}/bans/{user_id}")
DELETE_GUILD_BAN = RouteTemplate(DELETE, "/guilds/{guild_id}/bans/{user_id}")

GET_GUILD_BANS = RouteTemplate(GET, "/guilds/{guild_id}/bans")

GET_GUILD_CHANNELS = RouteTemplate(GET, "/guilds/{guild_id}/channels")
POST_GUILD_CHANNELS = RouteTemplate(POST, "/guilds/{guild_id}/channels")
PUT_GUILD_CHANNELS = RouteTemplate(PUT, "/guilds/{guild_id}/channels")
PATCH_GUILD_CHANNELS = RouteTemplate(PATCH, "/guilds/{guild_id}/channels")

GET_GUILD_EMBED = RouteTemplate(GET, "/guilds/{guild_id}/embed")
PATCH_GUILD_EMBED = RouteTemplate(PATCH, "/guilds/{guild_id}/embed")

GET_GUILD_EMOJI = RouteTemplate(GET, "/guilds/{guild_id}/emojis/{emoji_id}")
PATCH_GUILD_EMOJI = RouteTemplate(PATCH, "/guilds/{guild_id}/emojis/{emoji_id}")
DELETE_GUILD_EMOJI = RouteTemplate(DELETE, "/guilds/{guild_id}/emojis/{emoji_id}")

GET_GUILD_EMOJIS = RouteTemplate(GET, "/guilds/{guild_id}/emojis")
POST_GUILD_EMOJIS = RouteTemplate(POST, "/guilds/{guild_id}/emojis")

PATCH_GUILD_INTEGRATION = RouteTemplate(PATCH, "/guilds/{guild_id}/integrations/{integration_id}")
DELETE_GUILD_INTEGRATION = RouteTemplate(DELETE, "/guilds/{guild_id}/integrations/{integration_id}")

GET_GUILD_INTEGRATIONS = RouteTemplate(GET, "/guilds/{guild_id}/integrations")

POST_GUILD_INTEGRATION_SYNC = RouteTemplate(POST, "/guilds/{guild_id}/integrations/{integration_id}")

GET_GUILD_INVITES = RouteTemplate(GET, "/guilds/{guild_id}/invites")

GET_GUILD_MEMBERS = RouteTemplate(GET, "/guilds/{guild_id}/members")

GET_GUILD_MEMBER = RouteTemplate(GET, "/guilds/{guild_id}/members/{user_id}")
PATCH_GUILD_MEMBER = RouteTemplate(PATCH, "/guilds/{guild_id}/members/{user_id}")
DELETE_GUILD_MEMBER = RouteTemplate(DELETE, "/guilds/{guild_id}/members/{user_id}")

PUT_GUILD_MEMBER_ROLE = RouteTemplate(PUT, "/guilds/{guild_id}/members/{user_id}/roles/{role_id}")
DELETE_GUILD_MEMBER_ROLE = RouteTemplate(DELETE, "/guilds/{guild_id}/members/{user_id}/roles/{role_id}")

GET_GUILD_PREVIEW = RouteTemplate(GET, "/guilds/{guild_id}/preview")

GET_GUILD_PRUNE = RouteTemplate(GET, "/guilds/{guild_id}/prune")
POST_GUILD_PRUNE = RouteTemplate(POST, "/guilds/{guild_id}/prune")

PATCH_GUILD_ROLE = RouteTemplate(PATCH, "/guilds/{guild_id}/roles/{role_id}")
DELETE_GUILD_ROLE = RouteTemplate(DELETE, "/guilds/{guild_id}/roles/{role_id}")

GET_GUILD_ROLES = RouteTemplate(GET, "/guilds/{guild_id}/roles")
POST_GUILD_ROLES = RouteTemplate(POST, "/guilds/{guild_id}/roles")
PATCH_GUILD_ROLES = RouteTemplate(PATCH, "/guilds/{guild_id}/roles")

GET_GUILD_VANITY_URL = RouteTemplate(GET, "/guilds/{guild_id}/vanity-url")

GET_GUILD_VOICE_REGIONS = RouteTemplate(GET, "/guilds/{guild_id}/regions")

GET_GUILD_WIDGET_IMAGE = RouteTemplate(GET, "/guilds/{guild_id}/widget.png")

GET_GUILD_WEBHOOKS = RouteTemplate(GET, "/guilds/{guild_id}/webhooks")

# Invites
GET_INVITE = RouteTemplate(GET, "/invites/{invite_code}")
DELETE_INVITE = RouteTemplate(DELETE, "/invites/{invite_code}")

# Users
GET_USER = RouteTemplate(GET, "/users/{user_id}")

# @me
DELETE_MY_GUILD = RouteTemplate(DELETE, "/users/@me/guilds/{guild_id}")

GET_MY_CONNECTIONS = RouteTemplate(GET, "/users/@me/connections")  # OAuth2 only

POST_MY_CHANNELS = RouteTemplate(POST, "/users/@me/channels")

GET_MY_GUILDS = RouteTemplate(GET, "/users/@me/guilds")

PATCH_MY_GUILD_NICKNAME = RouteTemplate(PATCH, "/guilds/{guild_id}/members/@me/nick")

GET_MY_USER = RouteTemplate(GET, "/users/@me")
PATCH_MY_USER = RouteTemplate(PATCH, "/users/@me")

PUT_MY_REACTION = RouteTemplate(PUT, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")
DELETE_MY_REACTION = RouteTemplate(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")

# Voice
GET_VOICE_REGIONS = RouteTemplate(GET, "/voice/regions")

# Webhooks
GET_WEBHOOK = RouteTemplate(GET, "/webhooks/{webhook_id}")
PATCH_WEBHOOK = RouteTemplate(PATCH, "/webhooks/{webhook_id}")
POST_WEBHOOK = RouteTemplate(POST, "/webhooks/{webhook_id}")
DELETE_WEBHOOK = RouteTemplate(DELETE, "/webhooks/{webhook_id}")

GET_WEBHOOK_WITH_TOKEN = RouteTemplate(GET, "/webhooks/{webhook_id}/{webhook_token}")
PATCH_WEBHOOK_WITH_TOKEN = RouteTemplate(PATCH, "/webhooks/{webhook_id}/{webhook_token}")
DELETE_WEBHOOK_WITH_TOKEN = RouteTemplate(DELETE, "/webhooks/{webhook_id}/{webhook_token}")
POST_WEBHOOK_WITH_TOKEN = RouteTemplate(POST, "/webhooks/{webhook_id}/{webhook_token}")

POST_WEBHOOK_WITH_TOKEN_GITHUB = RouteTemplate(POST, "/webhooks/{webhook_id}/{webhook_token}/github")
POST_WEBHOOK_WITH_TOKEN_SLACK = RouteTemplate(POST, "/webhooks/{webhook_id}/{webhook_token}/slack")

# OAuth2 API
GET_MY_APPLICATION = RouteTemplate(GET, "/oauth2/applications/@me")

# Gateway
GET_GATEWAY = RouteTemplate(GET, "/gateway")
GET_GATEWAY_BOT = RouteTemplate(GET, "/gateway/bot")
