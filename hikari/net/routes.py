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
    method: typing.Final[str]

    #: The major parameters in a bucket hash-compatible representation.
    #:
    #: :type: :obj:`str`
    major_params_hash: typing.Final[str]

    #: The compiled route path to use
    #:
    #: :type: :obj:`str`
    compiled_path: typing.Final[str]

    #: The hash code
    #:
    #: :type: :obj:`int`
    hash_code: typing.Final[int]

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
    path_template: typing.Final[str]

    #: Major parameter names that appear in the template path.
    #:
    #: :type: :obj:`typing.FrozenSet` [ :obj:`str` ]
    major_params: typing.Final[typing.FrozenSet[str]]

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


_RT = typing.Final[RouteTemplate]

# Channels
CHANNEL: _RT = RouteTemplate("/channels/{channel_id}")
CHANNEL_DM_RECIPIENTS: _RT = RouteTemplate("/channels/{channel_id}/recipients/{user_id}")
CHANNEL_INVITES: _RT = RouteTemplate("/channels/{channel_id}/invites")
CHANNEL_MESSAGE: _RT = RouteTemplate("/channels/{channel_id}/messages/{message_id}")
CHANNEL_MESSAGES: _RT = RouteTemplate("/channels/{channel_id}/messages")
CHANNEL_MESSAGES_BULK_DELETE: _RT = RouteTemplate("/channels/{channel_id}/messages")
CHANNEL_PERMISSIONS: _RT = RouteTemplate("/channels/{channel_id}/permissions/{overwrite_id}")
CHANNEL_PIN: _RT = RouteTemplate("/channels/{channel_id}/pins/{message_id}")
CHANNEL_PINS: _RT = RouteTemplate("/channels/{channel_id}/pins")
CHANNEL_TYPING: _RT = RouteTemplate("/channels/{channel_id}/typing")
CHANNEL_WEBHOOKS: _RT = RouteTemplate("/channels/{channel_id}/webhooks")

# Reactions
ALL_REACTIONS: _RT = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions")
REACTION_EMOJI: _RT = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")
REACTION_EMOJI_USER: _RT = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{used_id}")
REACTIONS: _RT = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}")

# Guilds
GUILD: _RT = RouteTemplate("/guilds/{guild_id}")
GUILDS: _RT = RouteTemplate("/guilds")
GUILD_AUDIT_LOGS: _RT = RouteTemplate("/guilds/{guild_id}/audit-logs")
GUILD_BAN: _RT = RouteTemplate("/guilds/{guild_id}/bans/{user_id}")
GUILD_BANS: _RT = RouteTemplate("/guilds/{guild_id}/bans")
GUILD_CHANNELS: _RT = RouteTemplate("/guilds/{guild_id}/channels")
GUILD_EMBED: _RT = RouteTemplate("/guilds/{guild_id}/embed")
GUILD_EMOJI: _RT = RouteTemplate("/guilds/{guild_id}/emojis/{emoji_id}")
GUILD_EMOJIS: _RT = RouteTemplate("/guilds/{guild_id}/emojis")
GUILD_INTEGRATION: _RT = RouteTemplate("/guilds/{guild_id}/integrations/{integration_id}")
GUILD_INTEGRATIONS: _RT = RouteTemplate("/guilds/{guild_id}/integrations")
GUILD_INTEGRATION_SYNC: _RT = RouteTemplate("/guilds/{guild_id}/integrations/{integration_id}")
GUILD_INVITES: _RT = RouteTemplate("/guilds/{guild_id}/invites")
GUILD_MEMBERS: _RT = RouteTemplate("/guilds/{guild_id}/members")
GUILD_MEMBER: _RT = RouteTemplate("/guilds/{guild_id}/members/{user_id}")
GUILD_MEMBER_ROLE: _RT = RouteTemplate("/guilds/{guild_id}/members/{user_id}/roles/{role_id}")
GUILD_PREVIEW: _RT = RouteTemplate("/guilds/{guild_id}/preview")
GUILD_PRUNE: _RT = RouteTemplate("/guilds/{guild_id}/prune")
GUILD_ROLE: _RT = RouteTemplate("/guilds/{guild_id}/roles/{role_id}")
GUILD_ROLES: _RT = RouteTemplate("/guilds/{guild_id}/roles")
GUILD_VANITY_URL: _RT = RouteTemplate("/guilds/{guild_id}/vanity-url")
GUILD_VOICE_REGIONS: _RT = RouteTemplate("/guilds/{guild_id}/regions")
GUILD_WIDGET_IMAGE: _RT = RouteTemplate("/guilds/{guild_id}/widget.png")
GUILD_WEBHOOKS: _RT = RouteTemplate("/guilds/{guild_id}/webhooks")

# Invites
INVITE: _RT = RouteTemplate("/invites/{invite_code}")

# Users
USER: _RT = RouteTemplate("/users/{user_id}")

# @me
LEAVE_GUILD: _RT = RouteTemplate("/users/@me/guilds/{guild_id}")
OWN_CONNECTIONS: _RT = RouteTemplate("/users/@me/connections")  # OAuth2 only
OWN_DMS: _RT = RouteTemplate("/users/@me/channels")
OWN_GUILDS: _RT = RouteTemplate("/users/@me/guilds")
OWN_GUILD_NICKNAME: _RT = RouteTemplate("/guilds/{guild_id}/members/@me/nick")
OWN_USER: _RT = RouteTemplate("/users/@me")
OWN_REACTION: _RT = RouteTemplate("/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")

# Voice
VOICE_REGIONS: _RT = RouteTemplate("/voice/regions")

# Webhooks
WEBHOOK: _RT = RouteTemplate("/webhooks/{webhook_id}")
WEBHOOK_WITH_TOKEN: _RT = RouteTemplate("/webhooks/{webhook_id}/{webhook_token}")
WEBHOOK_WITH_TOKEN_GITHUB: _RT = RouteTemplate("/webhooks/{webhook_id}/{webhook_token}/github")
WEBHOOK_WITH_TOKEN_SLACK: _RT = RouteTemplate("/webhooks/{webhook_id}/{webhook_token}/slack")

# OAuth2 API
OAUTH2_APPLICATIONS: _RT = RouteTemplate("/oauth2/applications")
OAUTH2_APPLICATIONS_ME: _RT = RouteTemplate("/oauth2/applications/@me")
OAUTH2_AUTHORIZE: _RT = RouteTemplate("/oauth2/authorize")
OAUTH2_TOKEN: _RT = RouteTemplate("/oauth2/token")
OAUTH2_TOKEN_REVOKE: _RT = RouteTemplate("/oauth2/token/revoke")

# Gateway
GATEWAY: _RT = RouteTemplate("/gateway")
GATEWAY_BOT: _RT = RouteTemplate("/gateway/bot")
