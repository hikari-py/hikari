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

__all__: typing.Final[typing.Sequence[str]] = ["CompiledRoute", "Route"]

import re
import typing

import attr

from hikari.utilities import data_binding

DEFAULT_MAJOR_PARAMS: typing.Final[typing.Set[str]] = {"channel", "guild", "webhook"}
HASH_SEPARATOR: typing.Final[str] = ";"


# This could be frozen, except attrs' docs advise against this for performance
# reasons when using slotted classes.
@attr.s(init=True, slots=True, hash=True)
@typing.final
class CompiledRoute:
    """A compiled representation of a route to a specific resource.

    This is a similar representation to what `Route` provides, except
    `Route` is treated as a template, this is treated as an instance.
    """

    major_param_hash: str = attr.ib()
    """The major parameters in a bucket hash-compatible representation."""

    route: Route = attr.ib()
    """The route this compiled route was created from."""

    compiled_path: str = attr.ib()
    """The compiled route path to use."""

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

    def __str__(self) -> str:
        return f"{self.method} {self.compiled_path}"


@attr.s(hash=True, init=False, slots=True)
@typing.final
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

    method: str = attr.ib(hash=True, eq=True)
    """The HTTP method."""

    path_template: str = attr.ib(hash=True, eq=True)
    """The template string used for the path."""

    major_param: typing.Optional[str] = attr.ib(hash=False, eq=False)
    """The optional major parameter name."""

    # noinspection RegExpRedundantEscape
    _MAJOR_PARAM_REGEX: typing.Final[typing.ClassVar[typing.Pattern[str]]] = re.compile(r"\{(.*?)\}")

    def __init__(self, method: str, path_template: str) -> None:
        self.method = method
        self.path_template = path_template

        self.major_param: typing.Optional[str]
        match = self._MAJOR_PARAM_REGEX.search(path_template)
        self.major_param = match.group(1) if match else None

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
        data = data_binding.StringMapBuilder()
        for k, v in kwargs.items():
            data.put(k, v)

        return CompiledRoute(
            route=self,
            compiled_path=self.path_template.format_map(data),
            major_param_hash=data[self.major_param] if self.major_param is not None else "-",
        )

    def __str__(self) -> str:
        return self.path_template


GET: typing.Final[str] = "GET"
PATCH: typing.Final[str] = "PATCH"
DELETE: typing.Final[str] = "DELETE"
PUT: typing.Final[str] = "PUT"
POST: typing.Final[str] = "POST"

# Channels
GET_CHANNEL: typing.Final[Route] = Route(GET, "/channels/{channel}")
PATCH_CHANNEL: typing.Final[Route] = Route(PATCH, "/channels/{channel}")
DELETE_CHANNEL: typing.Final[Route] = Route(DELETE, "/channels/{channel}")

GET_CHANNEL_INVITES: typing.Final[Route] = Route(GET, "/channels/{channel}/invites")
POST_CHANNEL_INVITES: typing.Final[Route] = Route(POST, "/channels/{channel}/invites")

GET_CHANNEL_MESSAGE: typing.Final[Route] = Route(GET, "/channels/{channel}/messages/{message}")
PATCH_CHANNEL_MESSAGE: typing.Final[Route] = Route(PATCH, "/channels/{channel}/messages/{message}")
DELETE_CHANNEL_MESSAGE: typing.Final[Route] = Route(DELETE, "/channels/{channel}/messages/{message}")

GET_CHANNEL_MESSAGES: typing.Final[Route] = Route(GET, "/channels/{channel}/messages")
POST_CHANNEL_MESSAGES: typing.Final[Route] = Route(POST, "/channels/{channel}/messages")

POST_DELETE_CHANNEL_MESSAGES_BULK: typing.Final[Route] = Route(POST, "/channels/{channel}/messages/bulk-delete")

PATCH_CHANNEL_PERMISSIONS: typing.Final[Route] = Route(PATCH, "/channels/{channel}/permissions/{overwrite}")
DELETE_CHANNEL_PERMISSIONS: typing.Final[Route] = Route(DELETE, "/channels/{channel}/permissions/{overwrite}")

DELETE_CHANNEL_PIN: typing.Final[Route] = Route(DELETE, "/channels/{channel}/pins/{message}")

GET_CHANNEL_PINS: typing.Final[Route] = Route(GET, "/channels/{channel}/pins")
PUT_CHANNEL_PINS: typing.Final[Route] = Route(PUT, "/channels/{channel}/pins/{message}")

POST_CHANNEL_TYPING: typing.Final[Route] = Route(POST, "/channels/{channel}/typing")

POST_CHANNEL_WEBHOOKS: typing.Final[Route] = Route(POST, "/channels/{channel}/webhooks")
GET_CHANNEL_WEBHOOKS: typing.Final[Route] = Route(GET, "/channels/{channel}/webhooks")

# Reactions
DELETE_ALL_REACTIONS: typing.Final[Route] = Route(DELETE, "/channels/{channel}/messages/{message}/reactions")

DELETE_REACTION_EMOJI: typing.Final[Route] = Route(DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}")
DELETE_REACTION_USER: typing.Final[Route] = Route(
    DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}/{user}"
)
GET_REACTIONS: typing.Final[Route] = Route(GET, "/channels/{channel}/messages/{message}/reactions/{emoji}")

# Guilds
GET_GUILD: typing.Final[Route] = Route(GET, "/guilds/{guild}")
PATCH_GUILD: typing.Final[Route] = Route(PATCH, "/guilds/{guild}")
DELETE_GUILD: typing.Final[Route] = Route(DELETE, "/guilds/{guild}")

POST_GUILDS: typing.Final[Route] = Route(POST, "/guilds")

GET_GUILD_AUDIT_LOGS: typing.Final[Route] = Route(GET, "/guilds/{guild}/audit-logs")

GET_GUILD_BAN: typing.Final[Route] = Route(GET, "/guilds/{guild}/bans/{user}")
PUT_GUILD_BAN: typing.Final[Route] = Route(PUT, "/guilds/{guild}/bans/{user}")
DELETE_GUILD_BAN: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/bans/{user}")

GET_GUILD_BANS: typing.Final[Route] = Route(GET, "/guilds/{guild}/bans")

GET_GUILD_CHANNELS: typing.Final[Route] = Route(GET, "/guilds/{guild}/channels")
POST_GUILD_CHANNELS: typing.Final[Route] = Route(POST, "/guilds/{guild}/channels")
PATCH_GUILD_CHANNELS: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/channels")

GET_GUILD_WIDGET: typing.Final[Route] = Route(GET, "/guilds/{guild}/widget")
PATCH_GUILD_WIDGET: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/widget")

GET_GUILD_EMOJI: typing.Final[Route] = Route(GET, "/guilds/{guild}/emojis/{emoji}")
PATCH_GUILD_EMOJI: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/emojis/{emoji}")
DELETE_GUILD_EMOJI: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/emojis/{emoji}")

GET_GUILD_EMOJIS: typing.Final[Route] = Route(GET, "/guilds/{guild}/emojis")
POST_GUILD_EMOJIS: typing.Final[Route] = Route(POST, "/guilds/{guild}/emojis")

PATCH_GUILD_INTEGRATION: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/integrations/{integration}")
DELETE_GUILD_INTEGRATION: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/integrations/{integration}")

GET_GUILD_INTEGRATIONS: typing.Final[Route] = Route(GET, "/guilds/{guild}/integrations")

POST_GUILD_INTEGRATION_SYNC: typing.Final[Route] = Route(POST, "/guilds/{guild}/integrations/{integration}")

GET_GUILD_INVITES: typing.Final[Route] = Route(GET, "/guilds/{guild}/invites")

GET_GUILD_MEMBERS: typing.Final[Route] = Route(GET, "/guilds/{guild}/members")

GET_GUILD_MEMBER: typing.Final[Route] = Route(GET, "/guilds/{guild}/members/{user}")
PATCH_GUILD_MEMBER: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/members/{user}")
PUT_GUILD_MEMBER: typing.Final[Route] = Route(PUT, "/guilds/{guild}/members/{user}")
DELETE_GUILD_MEMBER: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/members/{user}")

PUT_GUILD_MEMBER_ROLE: typing.Final[Route] = Route(PUT, "/guilds/{guild}/members/{user}/roles/{role}")
DELETE_GUILD_MEMBER_ROLE: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/members/{user}/roles/{role}")

GET_GUILD_PREVIEW: typing.Final[Route] = Route(GET, "/guilds/{guild}/preview")

GET_GUILD_PRUNE: typing.Final[Route] = Route(GET, "/guilds/{guild}/prune")
POST_GUILD_PRUNE: typing.Final[Route] = Route(POST, "/guilds/{guild}/prune")

PATCH_GUILD_ROLE: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/roles/{role}")
DELETE_GUILD_ROLE: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/roles/{role}")

GET_GUILD_ROLES: typing.Final[Route] = Route(GET, "/guilds/{guild}/roles")
POST_GUILD_ROLES: typing.Final[Route] = Route(POST, "/guilds/{guild}/roles")
PATCH_GUILD_ROLES: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/roles")

GET_GUILD_VANITY_URL: typing.Final[Route] = Route(GET, "/guilds/{guild}/vanity-url")

GET_GUILD_VOICE_REGIONS: typing.Final[Route] = Route(GET, "/guilds/{guild}/regions")

GET_GUILD_WEBHOOKS: typing.Final[Route] = Route(GET, "/guilds/{guild}/webhooks")

GET_GUILD_BANNER_IMAGE: typing.Final[Route] = Route(GET, "/guilds/{guild}/widget.png")

# Invites
GET_INVITE: typing.Final[Route] = Route(GET, "/invites/{invite_code}")
DELETE_INVITE: typing.Final[Route] = Route(DELETE, "/invites/{invite_code}")

# Users
GET_USER: typing.Final[Route] = Route(GET, "/users/{user}")

# @me
DELETE_MY_GUILD: typing.Final[Route] = Route(DELETE, "/users/@me/guilds/{guild}")

GET_MY_CONNECTIONS: typing.Final[Route] = Route(GET, "/users/@me/connections")  # OAuth2 only

POST_MY_CHANNELS: typing.Final[Route] = Route(POST, "/users/@me/channels")

GET_MY_GUILDS: typing.Final[Route] = Route(GET, "/users/@me/guilds")

PATCH_MY_GUILD_NICKNAME: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/members/@me/nick")

GET_MY_USER: typing.Final[Route] = Route(GET, "/users/@me")
PATCH_MY_USER: typing.Final[Route] = Route(PATCH, "/users/@me")

PUT_MY_REACTION: typing.Final[Route] = Route(PUT, "/channels/{channel}/messages/{message}/reactions/{emoji}/@me")
DELETE_MY_REACTION: typing.Final[Route] = Route(DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}/@me")

# Voice
GET_VOICE_REGIONS: typing.Final[Route] = Route(GET, "/voice/regions")

# Webhooks
GET_WEBHOOK: typing.Final[Route] = Route(GET, "/webhooks/{webhook}")
PATCH_WEBHOOK: typing.Final[Route] = Route(PATCH, "/webhooks/{webhook}")
DELETE_WEBHOOK: typing.Final[Route] = Route(DELETE, "/webhooks/{webhook}")

GET_WEBHOOK_WITH_TOKEN: typing.Final[Route] = Route(GET, "/webhooks/{webhook}/{token}")
PATCH_WEBHOOK_WITH_TOKEN: typing.Final[Route] = Route(PATCH, "/webhooks/{webhook}/{token}")
DELETE_WEBHOOK_WITH_TOKEN: typing.Final[Route] = Route(DELETE, "/webhooks/{webhook}/{token}")
POST_WEBHOOK_WITH_TOKEN: typing.Final[Route] = Route(POST, "/webhooks/{webhook}/{token}")

POST_WEBHOOK_WITH_TOKEN_GITHUB: typing.Final[Route] = Route(POST, "/webhooks/{webhook}/{token}/github")
POST_WEBHOOK_WITH_TOKEN_SLACK: typing.Final[Route] = Route(POST, "/webhooks/{webhook}/{token}/slack")

# OAuth2 API
GET_MY_APPLICATION: typing.Final[Route] = Route(GET, "/oauth2/applications/@me")

# Gateway
GET_GATEWAY: typing.Final[Route] = Route(GET, "/gateway")
GET_GATEWAY_BOT: typing.Final[Route] = Route(GET, "/gateway/bot")
