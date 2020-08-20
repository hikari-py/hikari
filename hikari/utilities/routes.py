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
"""Provides the valid routes that can be used on the API and the CDN."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["CompiledRoute", "Route", "CDNRoute"]

import math
import re
import typing
import urllib.parse

import attr

from hikari import files
from hikari.utilities import attr_extensions
from hikari.utilities import data_binding

HASH_SEPARATOR: typing.Final[str] = ";"


# This could be frozen, except attrs' docs advise against this for performance
# reasons when using slotted classes.
@attr_extensions.with_copy
@attr.s(init=True, slots=True, hash=True, weakref_slot=False)
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
        base_url : builtins.str
            The base of the URL to prepend to the compiled path.

        Returns
        -------
        builtins.str
            The full URL for the route.
        """
        return base_url + self.compiled_path

    def create_real_bucket_hash(self, initial_bucket_hash: str) -> str:
        """Create a full bucket hash from a given initial hash.

        The result of this hash will be decided by the value of the major
        parameters passed to the route during the compilation phase.

        Parameters
        ----------
        initial_bucket_hash : builtins.str
            The initial bucket hash provided by Discord in the HTTP headers
            for a given response.

        Returns
        -------
        builtins.str
            The input hash amalgamated with a hash code produced by the
            major parameters in this compiled route instance.
        """
        return initial_bucket_hash + HASH_SEPARATOR + self.major_param_hash

    def __str__(self) -> str:
        return f"{self.method} {self.compiled_path}"


@attr_extensions.with_copy
@attr.s(hash=True, init=False, slots=True, weakref_slot=False)
@typing.final
class Route:
    """A template used to create compiled routes for specific parameters.

    These compiled routes are used to identify rate limit buckets. Compiled
    routes may have a single major parameter.

    Parameters
    ----------
    method : builtins.str
        The HTTP method
    path_template : builtins.str
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


def _cdn_valid_formats_converter(values: typing.Set[str]) -> typing.FrozenSet[str]:
    return frozenset(v.lower() for v in values)


@attr_extensions.with_copy
@attr.s(hash=True, init=True, slots=True, weakref_slot=False)
@typing.final
class CDNRoute:
    """Route implementation for a CDN resource."""

    path_template: str = attr.ib()
    """Template string for this endpoint."""

    valid_formats: typing.AbstractSet[str] = attr.ib(
        converter=_cdn_valid_formats_converter, eq=False, hash=False, repr=False,
    )
    """Valid file formats for this endpoint."""

    @valid_formats.validator
    def _(self, _: attr.Attribute[typing.AbstractSet[str]], values: typing.AbstractSet[str]) -> None:
        if not values:
            raise ValueError(f"{self.path_template} must have at least one valid format set")

    sizable: bool = attr.ib(default=True, kw_only=True, repr=False, hash=False, eq=False)
    """`builtins.True` if a `size` param can be specified, or `builtins.False` otherwise."""

    def compile(
        self, base_url: str, *, file_format: str, size: typing.Optional[int] = None, **kwargs: typing.Any,
    ) -> str:
        """Generate a full CDN url from this endpoint.

        Parameters
        ----------
        base_url : builtins.str
            The base URL for the CDN. The generated route is concatenated onto
            this.
        file_format : builtins.str
            The file format to use for the asset.
        size : builtins.int or buitlins.None
            The custom size query parameter to set. If `builtins.None`,
            it is not passed.
        **kwargs : typing.Any
            Parameters to interpolate into the path template.

        Returns
        -------
        builtins.str
            The full asset URL.

        Raises
        ------
        builtins.TypeError
            If a GIF is requested, but the asset is not animated;
            if an invalid file format for the endpoint is passed; or if a `size`
            is passed but the route is not `sizable`.

        builtins.ValueError
            If `size` is specified, but is not an integer power of `2` between
            `16` and `4096` inclusive.
        """
        file_format = file_format.lower()

        if file_format not in self.valid_formats:
            raise TypeError(
                f"{file_format} is not a valid format for this asset. Valid formats are: "
                + ", ".join(self.valid_formats)
            )

        if "hash" in kwargs and not kwargs["hash"].startswith("a_") and file_format == GIF:
            raise TypeError("This asset is not animated, so cannot be retrieved as a GIF")

        # Make URL-safe first.
        kwargs = {k: urllib.parse.quote(str(v)) for k, v in kwargs.items()}
        url = base_url + self.path_template.format(**kwargs) + f".{file_format}"

        if size is not None:
            if not self.sizable:
                raise TypeError("This asset cannot be resized.")

            size_power = math.log2(size)
            if size_power.is_integer() and 4 <= size_power <= 12:
                url += "?"
                url += urllib.parse.urlencode({"size": str(size)})
            else:
                raise ValueError("size, if specified, must be an integer power of 2 between 16 and 4096 inclusive")

        return url

    def compile_to_file(
        self, base_url: str, *, file_format: str, size: typing.Optional[int] = None, **kwargs: typing.Any,
    ) -> files.URL:
        """Perform the same as `compile`, but return the URL as a `files.URL`."""
        return files.URL(self.compile(base_url, file_format=file_format, size=size, **kwargs))


GET: typing.Final[str] = "GET"
POST: typing.Final[str] = "POST"
PATCH: typing.Final[str] = "PATCH"
DELETE: typing.Final[str] = "DELETE"
PUT: typing.Final[str] = "PUT"

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

GET_CHANNEL_PINS: typing.Final[Route] = Route(GET, "/channels/{channel}/pins")
PUT_CHANNEL_PINS: typing.Final[Route] = Route(PUT, "/channels/{channel}/pins/{message}")
DELETE_CHANNEL_PIN: typing.Final[Route] = Route(DELETE, "/channels/{channel}/pins/{message}")

POST_CHANNEL_TYPING: typing.Final[Route] = Route(POST, "/channels/{channel}/typing")

POST_CHANNEL_WEBHOOKS: typing.Final[Route] = Route(POST, "/channels/{channel}/webhooks")
GET_CHANNEL_WEBHOOKS: typing.Final[Route] = Route(GET, "/channels/{channel}/webhooks")

# Reactions
GET_REACTIONS: typing.Final[Route] = Route(GET, "/channels/{channel}/messages/{message}/reactions/{emoji}")
DELETE_ALL_REACTIONS: typing.Final[Route] = Route(DELETE, "/channels/{channel}/messages/{message}/reactions")
DELETE_REACTION_EMOJI: typing.Final[Route] = Route(DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}")
DELETE_REACTION_USER: typing.Final[Route] = Route(
    DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}/{user}"
)

# Guilds
GET_GUILD: typing.Final[Route] = Route(GET, "/guilds/{guild}")
POST_GUILDS: typing.Final[Route] = Route(POST, "/guilds")
PATCH_GUILD: typing.Final[Route] = Route(PATCH, "/guilds/{guild}")
DELETE_GUILD: typing.Final[Route] = Route(DELETE, "/guilds/{guild}")

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

GET_GUILD_MEMBER: typing.Final[Route] = Route(GET, "/guilds/{guild}/members/{user}")
PATCH_GUILD_MEMBER: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/members/{user}")
PUT_GUILD_MEMBER: typing.Final[Route] = Route(PUT, "/guilds/{guild}/members/{user}")

GET_GUILD_MEMBERS: typing.Final[Route] = Route(GET, "/guilds/{guild}/members")
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
POST_MY_CHANNELS: typing.Final[Route] = Route(POST, "/users/@me/channels")
GET_MY_CONNECTIONS: typing.Final[Route] = Route(GET, "/users/@me/connections")  # OAuth2 only
DELETE_MY_GUILD: typing.Final[Route] = Route(DELETE, "/users/@me/guilds/{guild}")

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


PNG: typing.Final[str] = "png".casefold()
JPEG: typing.Final[str] = "jpeg".casefold()
WEBP: typing.Final[str] = "webp".casefold()
GIF: typing.Final[str] = "gif".casefold()

# CDN specific endpoints. These reside on a different server.
CDN_CUSTOM_EMOJI: typing.Final[CDNRoute] = CDNRoute("/emojis/{emoji_id}", {PNG, GIF})

CDN_GUILD_ICON: typing.Final[CDNRoute] = CDNRoute("/icons/{guild_id}/{hash}", {PNG, JPEG, WEBP, GIF})
CDN_GUILD_SPLASH: typing.Final[CDNRoute] = CDNRoute("/splashes/{guild_id}/{hash}", {PNG, JPEG, WEBP})
CDN_GUILD_DISCOVERY_SPLASH: typing.Final[CDNRoute] = CDNRoute(
    "/discovery-splashes/{guild_id}/{hash}", {PNG, JPEG, WEBP}
)
CDN_GUILD_BANNER: typing.Final[CDNRoute] = CDNRoute("/banners/{guild_id}/{hash}", {PNG, JPEG, WEBP})

CDN_DEFAULT_USER_AVATAR: typing.Final[CDNRoute] = CDNRoute("/embed/avatars/{discriminator}", {PNG}, sizable=False)
CDN_USER_AVATAR: typing.Final[CDNRoute] = CDNRoute("/avatars/{user_id}/{hash}", {PNG, JPEG, WEBP, GIF})

CDN_APPLICATION_ICON: typing.Final[CDNRoute] = CDNRoute("/app-icons/{application_id}/{hash}", {PNG, JPEG, WEBP})
CDN_APPLICATION_COVER: typing.Final[CDNRoute] = CDNRoute("/app-assets/{application_id}/{hash}", {PNG, JPEG, WEBP})
CDN_ACHIEVEMENT_ICON: typing.Final[CDNRoute] = CDNRoute(
    "/app-assets/{application_id}/achievements/{achievement_id}/icons/{hash}", {PNG, JPEG, WEBP}
)

CDN_TEAM_ICON: typing.Final[CDNRoute] = CDNRoute("/team-icons/{team_id}/{hash}", {PNG, JPEG, WEBP})
# undocumented on the Discord docs.
CDN_CHANNEL_ICON: typing.Final[CDNRoute] = CDNRoute("/channel-icons/{channel_id}/{hash}", {PNG, JPEG, WEBP})
