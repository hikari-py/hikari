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
__all__ = ["CompiledRoute", "RouteTemplate"]

import typing

DEFAULT_MAJOR_PARAMS = {"channel_id", "guild_id", "webhook_id"}


class CompiledRoute:
    """A compiled representation of a route ready to be made into a full e and to be used for a request.

    Parameters
    ----------
    method : :obj:`str`
        The HTTP method to use.
    path : :obj:`str`
        The path with any major parameters interpolated in.
    major_params_hash : :obj:`str`
        The part of the hash identifier to use for the compiled set of major parameters.
    """

    __slots__ = ("method", "major_params_hash", "compiled_path", "hash_code", "__weakref__")

    #: The method to use on the route.
    #:
    #: :type: :obj:`str`
    method: str
    #: The major parameters in a bucket hash-compatible representation.
    #:
    #: :type: :obj:`str`
    major_params_hash: str
    #: The compiled route path to use
    #:
    #: :type: :obj:`str`
    compiled_path: str
    #: The hash code
    #:
    #: :type: :obj:`int`
    hash_code: int

    def __init__(self, method: str, path_template: str, path: str, major_params_hash: str) -> None:
        self.method = method
        self.major_params_hash = major_params_hash
        self.compiled_path = path
        self.hash_code = hash((path_template, major_params_hash))

    def create_url(self, base_url: str) -> str:
        """Create the full URL with which you can make a request.

        Parameters
        ----------
        base_url : :obj:`str`
            The base of the URL to prepend to the compiled path.

        Returns
        -------
        :obj:`str`
            The full URL for the route.
        """
        return base_url + self.compiled_path

    def create_real_bucket_hash(self, initial_bucket_hash: str) -> str:
        """Create a full bucket hash from a given initial hash.

        The result of this hash will be decided by the value of the major
        parameters passed to the route during the compilation phase.

        Parameters
        ----------
        initial_bucket_hash: :obj:`str`
            The initial bucket hash provided by Discord in the HTTP headers
            for a given response.

        Returns
        -------
        :obj:`str`
            The input hash amalgamated with a hash code produced by the
            major parameters in this compiled route instance.
        """
        return initial_bucket_hash + ";" + self.major_params_hash

    def __hash__(self) -> int:
        return self.hash_code

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __repr__(self) -> str:
        this_type = type(self).__name__
        major_params = ", ".join(
            (
                f"method={self.method!r}",
                f"compiled_path={self.compiled_path!r}",
                f"major_params_hash={self.major_params_hash!r}",
            )
        )
        return f"{this_type}({major_params})"

    def __str__(self) -> str:
        return f"{self.method} {self.compiled_path}"


class RouteTemplate:
    """A template used to create compiled routes for specific parameters.

    These compiled routes are used to identify rate limit buckets.

    Parameters
    ----------
    path_template : :obj:`str`
        The template string for the path to use.
    major_params : :obj:`str`
        A collection of major parameter names that appear in the template path.
        If not specified, the default major parameter names are extracted and
        used in-place.
    """

    __slots__ = ("path_template", "major_params")

    #: The template string used for the path.
    #:
    #: :type: :obj:`str`
    path_template: str
    #: Major parameter names that appear in the template path.
    #:
    #: :type: :obj:`typing.FrozenSet` [ :obj:`str` ]
    major_params: typing.FrozenSet[str]

    def __init__(self, path_template: str, major_params: typing.Collection[str] = None) -> None:
        self.path_template = path_template
        if major_params is None:
            self.major_params = frozenset(p for p in DEFAULT_MAJOR_PARAMS if f"{{{p}}}" in path_template)
        else:
            self.major_params = frozenset(major_params)

    def compile(self, method: str, /, **kwargs: typing.Any) -> CompiledRoute:
        """Generate a formatted :obj:`CompiledRoute` for this route template.

        This takes into account any URL parameters that have been passed, and extracting
        the :attr:major_params" for bucket hash operations accordingly.

        Parameters
        ----------
        method : :obj:`str`
            The method to use.
        **kwargs : :obj:`typing.Any`
            Any parameters to interpolate into the route path.

        Returns
        -------
        :obj:`CompiledRoute`
            The compiled route.
        """
        major_hash_part = "-".join((str(kwargs[p]) for p in self.major_params))

        return CompiledRoute(method, self.path_template, self.path_template.format_map(kwargs), major_hash_part)

    def __repr__(self) -> str:
        this_type = type(self).__name__
        major_params = ", ".join((f"path_template={self.path_template!r}", f"major_params={self.major_params!r}",))
        return f"{this_type}({major_params})"

    def __str__(self) -> str:
        return self.path_template


# Channels
CHANNEL = RouteTemplate("/channels/{channel_id}")
CHANNEL_DM_RECIPIENTS = RouteTemplate("/channels/{channel_id}/recipients/{user_id}")
CHANNEL_INVITES = RouteTemplate("/channels/{channel_id}/invites")
CHANNEL_MESSAGE = RouteTemplate("/channels/{channel_id}/messages/{message_id}")
CHANNEL_MESSAGES = RouteTemplate("/channels/{channel_id}/messages")
CHANNEL_MESSAGES_BULK_DELETE = RouteTemplate("/channels/{channel_id}/messages")
CHANNEL_PERMISSIONS = RouteTemplate("/channels/{channel_id}/permissions/{overwrite_id}")
CHANNEL_PIN = RouteTemplate("/channels/{channel_id}/pins/{message_id}")
CHANNEL_PINS = RouteTemplate("/channels/{channel_id}/pins")
CHANNEL_TYPING = RouteTemplate("/channels/{channel_id}/typing")
CHANNEL_WEBHOOKS = RouteTemplate("/channels/{channel_id}/webhooks")

# Reactions
ALL_REACTIONS = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions")
REACTION_EMOJI = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")
REACTION_EMOJI_USER = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{used_id}")
REACTIONS = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")

# Guilds
GUILD = RouteTemplate("/guilds/{guild_id}")
GUILDS = RouteTemplate("/guilds")
GUILD_AUDIT_LOGS = RouteTemplate("/guilds/{guild_id}/audit-logs")
GUILD_BAN = RouteTemplate("/guilds/{guild_id}/bans/{user_id}")
GUILD_BANS = RouteTemplate("/guilds/{guild_id}/bans")
GUILD_CHANNELS = RouteTemplate("/guilds/{guild_id}/channels")
GUILD_EMBED = RouteTemplate("/guilds/{guild_id}/embed")
GUILD_EMOJI = RouteTemplate("/guilds/{guild_id}/emojis/{emoji_id}")
GUILD_EMOJIS = RouteTemplate("/guilds/{guild_id}/emojis")
GUILD_INTEGRATION = RouteTemplate("/guilds/{guild_id}/integrations/{integration_id}")
GUILD_INTEGRATIONS = RouteTemplate("/guilds/{guild_id}/integrations")
GUILD_INTEGRATION_SYNC = RouteTemplate("/guilds/{guild_id}/integrations/{integration_id}")
GUILD_INVITES = RouteTemplate("/guilds/{guild_id}/invites")
GUILD_MEMBERS = RouteTemplate("/guilds/{guild_id}/members")
GUILD_MEMBER = RouteTemplate("/guilds/{guild_id}/members/{user_id}")
GUILD_MEMBER_ROLE = RouteTemplate("/guilds/{guild_id}/members/{user_id}/roles/{role_id}")
GUILD_PRUNE = RouteTemplate("/guilds/{guild_id}/prune")
GUILD_ROLE = RouteTemplate("/guilds/{guild_id}/roles/{role_id}")
GUILD_ROLES = RouteTemplate("/guilds/{guild_id}/roles")
GUILD_VANITY_URL = RouteTemplate("/guilds/{guild_id}/vanity-url")
GUILD_VOICE_REGIONS = RouteTemplate("/guilds/{guild_id}/regions")
GUILD_WIDGET_IMAGE = RouteTemplate("/guilds/{guild_id}/widget.png")
GUILD_WEBHOOKS = RouteTemplate("/guilds/{guild_id}/webhooks")

# Invites
INVITE = RouteTemplate("/invites/{invite_code}")

# Users
USER = RouteTemplate("/users/{user_id}")

# @me
LEAVE_GUILD = RouteTemplate("/users/@me/guilds/{guild_id}")
OWN_CONNECTIONS = RouteTemplate("/users/@me/connections")  # OAuth2 only
OWN_DMS = RouteTemplate("/users/@me/channels")
OWN_GUILDS = RouteTemplate("/users/@me/guilds")
OWN_GUILD_NICKNAME = RouteTemplate("/guilds/{guild_id}/members/@me/nick")
OWN_USER = RouteTemplate("/users/@me")
OWN_REACTION = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")

# Voice
VOICE_REGIONS = RouteTemplate("/voice/regions")

# Webhooks
WEBHOOK = RouteTemplate("/webhooks/{webhook_id}")
WEBHOOK_WITH_TOKEN = RouteTemplate("/webhooks/{webhook_id}/{webhook_token}")
WEBHOOK_WITH_TOKEN_GITHUB = RouteTemplate("/webhooks/{webhook_id}/{webhook_token}/github")
WEBHOOK_WITH_TOKEN_SLACK = RouteTemplate("/webhooks/{webhook_id}/{webhook_token}/slack")

# OAuth2 API
OAUTH2_APPLICATIONS = RouteTemplate("/oauth2/applications")
OAUTH2_APPLICATIONS_ME = RouteTemplate("/oauth2/applications/@me")
OAUTH2_AUTHORIZE = RouteTemplate("/oauth2/authorize")
OAUTH2_TOKEN = RouteTemplate("/oauth2/token")
OAUTH2_TOKEN_REVOKE = RouteTemplate("/oauth2/token/revoke")

# Gateway
GATEWAY = RouteTemplate("/gateway")
GATEWAY_BOT = RouteTemplate("/gateway/bot")
