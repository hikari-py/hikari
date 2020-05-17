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

__all__ = ["CompiledRoute", "Route"]

import re
import typing

DEFAULT_MAJOR_PARAMS: typing.Final[typing.Set[str]] = {"channel_id", "guild_id", "webhook_id"}
HASH_SEPARATOR: typing.Final[str] = ";"


class CompiledRoute:
    """A compiled representation of a route ready to be made into a full e and to be used for a request.

    Parameters
    ----------
    route : Route
        The route used to make this compiled route.
    path : str
        The path with any major parameters interpolated in.
    major_params_hash : str
        The part of the hash identifier to use for the compiled set of major parameters.
    """

    __slots__ = ("route", "major_param_hash", "compiled_path", "hash_code")

    route: typing.Final[Route]
    """The route this compiled route was created from."""

    major_param_hash: typing.Final[str]
    """The major parameters in a bucket hash-compatible representation."""

    compiled_path: typing.Final[str]
    """The compiled route path to use."""

    hash_code: typing.Final[int]
    """The hash code."""

    def __init__(self, route: Route, path: str, major_params_hash: str) -> None:
        self.route = route
        self.major_param_hash = major_params_hash
        self.compiled_path = path
        self.hash_code = hash((self.method, self.route.path_template, major_params_hash))

    @property
    def method(self) -> str:
        """Return the HTTP method of this compiled route."""
        return self.route.method

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
            and self.route == other.route
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


class Route:
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

    # noinspection RegExpRedundantEscape
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
        """Generate a formatted `CompiledRoute` for this route.

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
            isinstance(other, Route)
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
GET_CHANNEL = Route(GET, "/channels/{channel_id}")
PATCH_CHANNEL = Route(PATCH, "/channels/{channel_id}")
DELETE_CHANNEL = Route(DELETE, "/channels/{channel_id}")

GET_CHANNEL_INVITES = Route(GET, "/channels/{channel_id}/invites")
POST_CHANNEL_INVITES = Route(POST, "/channels/{channel_id}/invites")

GET_CHANNEL_MESSAGE = Route(GET, "/channels/{channel_id}/messages/{message_id}")
PATCH_CHANNEL_MESSAGE = Route(PATCH, "/channels/{channel_id}/messages/{message_id}")
DELETE_CHANNEL_MESSAGE = Route(DELETE, "/channels/{channel_id}/messages/{message_id}")

GET_CHANNEL_MESSAGES = Route(GET, "/channels/{channel_id}/messages")
POST_CHANNEL_MESSAGES = Route(POST, "/channels/{channel_id}/messages")

POST_DELETE_CHANNEL_MESSAGES_BULK = Route(POST, "/channels/{channel_id}/messages/bulk-delete")

PATCH_CHANNEL_PERMISSIONS = Route(PATCH, "/channels/{channel_id}/permissions/{overwrite_id}")
DELETE_CHANNEL_PERMISSIONS = Route(DELETE, "/channels/{channel_id}/permissions/{overwrite_id}")

DELETE_CHANNEL_PIN = Route(DELETE, "/channels/{channel_id}/pins/{message_id}")

GET_CHANNEL_PINS = Route(GET, "/channels/{channel_id}/pins")
PUT_CHANNEL_PINS = Route(PUT, "/channels/{channel_id}/pins/{message_id}")

POST_CHANNEL_TYPING = Route(POST, "/channels/{channel_id}/typing")

POST_CHANNEL_WEBHOOKS = Route(POST, "/channels/{channel_id}/webhooks")
GET_CHANNEL_WEBHOOKS = Route(GET, "/channels/{channel_id}/webhooks")

# Reactions
DELETE_ALL_REACTIONS = Route(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions")

DELETE_REACTION_EMOJI = Route(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")
DELETE_REACTION_USER = Route(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{used_id}")
GET_REACTIONS = Route(GET, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")

# Guilds
GET_GUILD = Route(GET, "/guilds/{guild_id}")
PATCH_GUILD = Route(PATCH, "/guilds/{guild_id}")
DELETE_GUILD = Route(DELETE, "/guilds/{guild_id}")

POST_GUILDS = Route(POST, "/guilds")

GET_GUILD_AUDIT_LOGS = Route(GET, "/guilds/{guild_id}/audit-logs")

GET_GUILD_BAN = Route(GET, "/guilds/{guild_id}/bans/{user_id}")
PUT_GUILD_BAN = Route(PUT, "/guilds/{guild_id}/bans/{user_id}")
DELETE_GUILD_BAN = Route(DELETE, "/guilds/{guild_id}/bans/{user_id}")

GET_GUILD_BANS = Route(GET, "/guilds/{guild_id}/bans")

GET_GUILD_CHANNELS = Route(GET, "/guilds/{guild_id}/channels")
POST_GUILD_CHANNELS = Route(POST, "/guilds/{guild_id}/channels")
PATCH_GUILD_CHANNELS = Route(PATCH, "/guilds/{guild_id}/channels")

GET_GUILD_EMBED = Route(GET, "/guilds/{guild_id}/embed")
PATCH_GUILD_EMBED = Route(PATCH, "/guilds/{guild_id}/embed")

GET_GUILD_EMOJI = Route(GET, "/guilds/{guild_id}/emojis/{emoji_id}")
PATCH_GUILD_EMOJI = Route(PATCH, "/guilds/{guild_id}/emojis/{emoji_id}")
DELETE_GUILD_EMOJI = Route(DELETE, "/guilds/{guild_id}/emojis/{emoji_id}")

GET_GUILD_EMOJIS = Route(GET, "/guilds/{guild_id}/emojis")
POST_GUILD_EMOJIS = Route(POST, "/guilds/{guild_id}/emojis")

PATCH_GUILD_INTEGRATION = Route(PATCH, "/guilds/{guild_id}/integrations/{integration_id}")
DELETE_GUILD_INTEGRATION = Route(DELETE, "/guilds/{guild_id}/integrations/{integration_id}")

GET_GUILD_INTEGRATIONS = Route(GET, "/guilds/{guild_id}/integrations")

POST_GUILD_INTEGRATION_SYNC = Route(POST, "/guilds/{guild_id}/integrations/{integration_id}")

GET_GUILD_INVITES = Route(GET, "/guilds/{guild_id}/invites")

GET_GUILD_MEMBERS = Route(GET, "/guilds/{guild_id}/members")

GET_GUILD_MEMBER = Route(GET, "/guilds/{guild_id}/members/{user_id}")
PATCH_GUILD_MEMBER = Route(PATCH, "/guilds/{guild_id}/members/{user_id}")
DELETE_GUILD_MEMBER = Route(DELETE, "/guilds/{guild_id}/members/{user_id}")

PUT_GUILD_MEMBER_ROLE = Route(PUT, "/guilds/{guild_id}/members/{user_id}/roles/{role_id}")
DELETE_GUILD_MEMBER_ROLE = Route(DELETE, "/guilds/{guild_id}/members/{user_id}/roles/{role_id}")

GET_GUILD_PREVIEW = Route(GET, "/guilds/{guild_id}/preview")

GET_GUILD_PRUNE = Route(GET, "/guilds/{guild_id}/prune")
POST_GUILD_PRUNE = Route(POST, "/guilds/{guild_id}/prune")

PATCH_GUILD_ROLE = Route(PATCH, "/guilds/{guild_id}/roles/{role_id}")
DELETE_GUILD_ROLE = Route(DELETE, "/guilds/{guild_id}/roles/{role_id}")

GET_GUILD_ROLES = Route(GET, "/guilds/{guild_id}/roles")
POST_GUILD_ROLES = Route(POST, "/guilds/{guild_id}/roles")
PATCH_GUILD_ROLES = Route(PATCH, "/guilds/{guild_id}/roles")

GET_GUILD_VANITY_URL = Route(GET, "/guilds/{guild_id}/vanity-url")

GET_GUILD_VOICE_REGIONS = Route(GET, "/guilds/{guild_id}/regions")

GET_GUILD_WEBHOOKS = Route(GET, "/guilds/{guild_id}/webhooks")

GET_GUILD_WIDGET_IMAGE = Route(GET, "/guilds/{guild_id}/widget.png")

# Invites
GET_INVITE = Route(GET, "/invites/{invite_code}")
DELETE_INVITE = Route(DELETE, "/invites/{invite_code}")

# Users
GET_USER = Route(GET, "/users/{user_id}")

# @me
DELETE_MY_GUILD = Route(DELETE, "/users/@me/guilds/{guild_id}")

GET_MY_CONNECTIONS = Route(GET, "/users/@me/connections")  # OAuth2 only

POST_MY_CHANNELS = Route(POST, "/users/@me/channels")

GET_MY_GUILDS = Route(GET, "/users/@me/guilds")

PATCH_MY_GUILD_NICKNAME = Route(PATCH, "/guilds/{guild_id}/members/@me/nick")

GET_MY_USER = Route(GET, "/users/@me")
PATCH_MY_USER = Route(PATCH, "/users/@me")

PUT_MY_REACTION = Route(PUT, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")
DELETE_MY_REACTION = Route(DELETE, "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")

# Voice
GET_VOICE_REGIONS = Route(GET, "/voice/regions")

# Webhooks
GET_WEBHOOK = Route(GET, "/webhooks/{webhook_id}")
PATCH_WEBHOOK = Route(PATCH, "/webhooks/{webhook_id}")
POST_WEBHOOK = Route(POST, "/webhooks/{webhook_id}")
DELETE_WEBHOOK = Route(DELETE, "/webhooks/{webhook_id}")

GET_WEBHOOK_WITH_TOKEN = Route(GET, "/webhooks/{webhook_id}/{webhook_token}")
PATCH_WEBHOOK_WITH_TOKEN = Route(PATCH, "/webhooks/{webhook_id}/{webhook_token}")
DELETE_WEBHOOK_WITH_TOKEN = Route(DELETE, "/webhooks/{webhook_id}/{webhook_token}")
POST_WEBHOOK_WITH_TOKEN = Route(POST, "/webhooks/{webhook_id}/{webhook_token}")

POST_WEBHOOK_WITH_TOKEN_GITHUB = Route(POST, "/webhooks/{webhook_id}/{webhook_token}/github")
POST_WEBHOOK_WITH_TOKEN_SLACK = Route(POST, "/webhooks/{webhook_id}/{webhook_token}/slack")

# OAuth2 API
GET_MY_APPLICATION = Route(GET, "/oauth2/applications/@me")

# Gateway
GET_GATEWAY = Route(GET, "/gateway")
GET_GATEWAY_BOT = Route(GET, "/gateway/bot")
