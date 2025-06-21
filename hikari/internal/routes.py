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
"""Provides the valid routes that can be used on the API and the CDN."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("CDNRoute", "CompiledRoute", "Route")

import math
import re
import typing
import urllib.parse

import attrs

from hikari import files
from hikari import undefined
from hikari.internal import attrs_extensions
from hikari.internal import data_binding
from hikari.internal import typing_extensions

HASH_SEPARATOR: typing.Final[str] = ";"
PARAM_REGEX: typing.Final[typing.Pattern[str]] = re.compile(r"{(\w+)}")
MAJOR_PARAM_COMBOS: typing.Mapping[frozenset[str], typing.Callable[[typing.Mapping[str, str]], str]] = {
    frozenset(("channel",)): lambda d: d["channel"],
    frozenset(("guild",)): lambda d: d["guild"],
    frozenset(("webhook", "token")): lambda d: d["webhook"] + ":" + d["token"],
    frozenset(("webhook",)): lambda d: d["webhook"],
}


# This could be frozen, except attrs' docs advise against this for performance
# reasons when using slotted classes.
@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, weakref_slot=False)
@typing.final
class CompiledRoute:
    """A compiled representation of a route to a specific resource.

    This is a similar representation to what [`Route`][] provides, except
    [`Route`][] is treated as a template, this is treated as an instance.
    """

    major_param_hash: str = attrs.field()
    """The major parameters in a bucket hash-compatible representation."""

    route: Route = attrs.field()
    """The route this compiled route was created from."""

    compiled_path: str = attrs.field()
    """The compiled route path to use."""

    @property
    def method(self) -> str:
        """Return the HTTP method of this compiled route."""
        return self.route.method

    def create_url(self, base_url: str) -> str:
        """Create the full URL with which you can make a request.

        Parameters
        ----------
        base_url
            The base of the URL to prepend to the compiled path.

        Returns
        -------
        str
            The full URL for the route.
        """
        return base_url + self.compiled_path

    def create_real_bucket_hash(self, initial_bucket_hash: str, authentication_hash: str) -> str:
        """Create a full bucket hash from a given initial hash.

        The result of this hash will be decided by the value of the major
        parameters passed to the route during the compilation phase.

        Parameters
        ----------
        initial_bucket_hash
            The initial bucket hash provided by Discord in the HTTP headers
            for a given response.
        authentication_hash
            The token hash.

        Returns
        -------
        str
            The input hash amalgamated with a hash code produced by the
            major parameters in this compiled route instance.
        """
        return f"{initial_bucket_hash}{HASH_SEPARATOR}{authentication_hash}{HASH_SEPARATOR}{self.major_param_hash}"

    @typing_extensions.override
    def __str__(self) -> str:
        return f"{self.method} {self.compiled_path}"


@attrs_extensions.with_copy
@attrs.define(hash=False, eq=False, weakref_slot=False)
@typing.final
class Route:
    """A template used to create compiled routes for specific parameters.

    These compiled routes are used to identify rate limit buckets. Compiled
    routes may have a single major parameter.

    Parameters
    ----------
    method
        The HTTP method.
    path_template
        The template string for the path to use.
    """

    method: str = attrs.field()
    """The HTTP method."""

    path_template: str = attrs.field()
    """The template string used for the path."""

    major_params: frozenset[str] | None = attrs.field(repr=False, init=False, default=None)
    """The optional major parameter name combination for this endpoint."""

    ratelimit_hash: int | None = attrs.field(repr=False, default=None)
    """The rate limit hash for this endpoint."""

    has_ratelimits: bool = attrs.field(repr=False, default=True)
    """Whether this route is affected by ratelimits.

    This should be left as [`True`][] (the default) for most routes. This
    only covers specific routes where no ratelimits exist, so we can
    be a bit more efficient with them.
    """

    def __attrs_post_init__(self) -> None:
        match = PARAM_REGEX.findall(self.path_template)
        for major_param_combo in MAJOR_PARAM_COMBOS:
            if major_param_combo.issubset(match):
                self.major_params = major_param_combo
                break

    def compile(self, **kwargs: data_binding.Stringish) -> CompiledRoute:
        """Generate a formatted [`CompiledRoute`][] for this route.

        This takes into account any URL parameters that have been passed.

        Parameters
        ----------
        **kwargs
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
            major_param_hash=MAJOR_PARAM_COMBOS[self.major_params](data) if self.major_params else "-",
        )

    @typing_extensions.override
    def __hash__(self) -> int:
        return self.ratelimit_hash or hash((self.method, self.path_template))

    @typing_extensions.override
    def __str__(self) -> str:
        return self.method + " " + self.path_template


def _cdn_valid_formats_converter(values: typing.AbstractSet[str]) -> frozenset[str]:
    return frozenset(v.upper() for v in values)


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, weakref_slot=False)
@typing.final
class CDNRoute:
    """Route implementation for a CDN resource."""

    path_template: str = attrs.field()
    """Template string for this endpoint."""

    valid_formats: typing.AbstractSet[str] = attrs.field(
        converter=_cdn_valid_formats_converter, eq=False, hash=False, repr=False
    )
    """Valid file formats for this endpoint."""

    @valid_formats.validator
    def _(self, _: attrs.Attribute[typing.AbstractSet[str]], values: typing.AbstractSet[str]) -> None:
        if not values:
            msg = f"{self.path_template} must have at least one valid format set"
            raise ValueError(msg)

    def compile(
        self,
        base_url: str,
        *,
        file_format: str,
        lossless: bool = True,
        size: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        **kwargs: object,
    ) -> str:
        """Generate a full CDN url from this endpoint.

        Parameters
        ----------
        base_url
            The base URL for the CDN. The generated route is concatenated onto
            this.
        file_format
            The file format to use for the asset.
        lossless
            Whether to request a lossless image. Defaults to [`True`][].
        size
            The custom size query parameter to set. If unspecified,
            it is not passed.
        **kwargs
            Parameters to interpolate into the path template.

        Returns
        -------
        str
            The full asset URL.

        Raises
        ------
        TypeError
            If an invalid file format for the endpoint is passed;
            If an animated format is requested for a static asset.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        file_format = file_format.upper()

        if file_format not in self.valid_formats:
            raise TypeError(
                f"{file_format} is not a valid format for this asset. Valid formats are: "
                + ", ".join(self.valid_formats)
            )

        if "hash" in kwargs and not str(kwargs["hash"]).startswith("a_") and file_format in {AWEBP, GIF, APNG}:
            msg = f"This asset is not animated, so it cannot be retrieved as {file_format}."
            raise TypeError(msg)

        query = data_binding.StringMapBuilder()

        if file_format in {WEBP, AWEBP}:
            query.put("lossless", lossless)

        if size is not undefined.UNDEFINED:
            if size < 0:
                msg = "size must be positive"
                raise ValueError(msg)

            size_power = math.log2(size)
            if not (size_power.is_integer() and 4 <= size_power <= 12):
                msg = "size must be an integer power of 2 between 16 and 4096 inclusive"
                raise ValueError(msg)

            query.put("size", size)

        if file_format == AWEBP:
            query.put("animated", True)
        elif file_format == PNG and APNG in self.valid_formats:
            # We want to ensure that if a PNG is requested, then it will never be an APNG
            query.put("passthrough", False)

        # Make URL-safe first.
        kwargs = {k: urllib.parse.quote(str(v)) for k, v in kwargs.items()}
        ext = CDN_FORMAT_TRANSFORM.get(file_format, file_format).lower()
        url = base_url + self.path_template.format(**kwargs) + f".{ext}"

        if query:
            url += "?" + urllib.parse.urlencode(query)

        return url

    def compile_to_file(
        self,
        base_url: str,
        *,
        file_format: str,
        lossless: bool = True,
        size: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        **kwargs: object,
    ) -> files.URL:
        """Perform the same as `compile`, but return the URL as a [`hikari.files.URL`][]."""
        return files.URL(self.compile(base_url, file_format=file_format, size=size, lossless=lossless, **kwargs))


GET: typing.Final[str] = "GET"
POST: typing.Final[str] = "POST"
PATCH: typing.Final[str] = "PATCH"
DELETE: typing.Final[str] = "DELETE"
PUT: typing.Final[str] = "PUT"

# PUT/DELETE /reactions/ are a special case because you pass arguments as part of the route,
# so we need to join them
_JOINED_REACTIONS_HASH = hash("PUT/DELETE REACTIONS")

# Channels
GET_CHANNEL: typing.Final[Route] = Route(GET, "/channels/{channel}")
PATCH_CHANNEL: typing.Final[Route] = Route(PATCH, "/channels/{channel}")
DELETE_CHANNEL: typing.Final[Route] = Route(DELETE, "/channels/{channel}")

POST_MESSAGE_THREADS: typing.Final[Route] = Route(POST, "/channels/{channel}/messages/{message}/threads")
POST_CHANNEL_THREADS: typing.Final[Route] = Route(POST, "/channels/{channel}/threads")
PUT_MY_THREAD_MEMBER: typing.Final[Route] = Route(PUT, "/channels/{channel}/thread-members/@me")
PUT_THREAD_MEMBER: typing.Final[Route] = Route(PUT, "/channels/{channel}/thread-members/{user}")
DELETE_MY_THREAD_MEMBER: typing.Final[Route] = Route(DELETE, "/channels/{channel}/thread-members/@me")
DELETE_THREAD_MEMBER: typing.Final[Route] = Route(DELETE, "/channels/{channel}/thread-members/{user}")
GET_THREAD_MEMBER: typing.Final[Route] = Route(GET, "/channels/{channel}/thread-members/{user}")
GET_THREAD_MEMBERS: typing.Final[Route] = Route(GET, "/channels/{channel}/thread-members")
GET_ACTIVE_THREADS: typing.Final[Route] = Route(GET, "/guilds/{guild}/threads/active")
GET_PUBLIC_ARCHIVED_THREADS: typing.Final[Route] = Route(GET, "/channels/{channel}/threads/archived/public")
GET_PRIVATE_ARCHIVED_THREADS: typing.Final[Route] = Route(GET, "/channels/{channel}/threads/archived/private")
GET_JOINED_PRIVATE_ARCHIVED_THREADS: typing.Final[Route] = Route(
    GET, "/channels/{channel}/users/@me/threads/archived/private"
)

POST_CHANNEL_FOLLOWERS: typing.Final[Route] = Route(POST, "/channels/{channel}/followers")

GET_CHANNEL_INVITES: typing.Final[Route] = Route(GET, "/channels/{channel}/invites")
POST_CHANNEL_INVITES: typing.Final[Route] = Route(POST, "/channels/{channel}/invites")

GET_CHANNEL_MESSAGE: typing.Final[Route] = Route(GET, "/channels/{channel}/messages/{message}")
PATCH_CHANNEL_MESSAGE: typing.Final[Route] = Route(PATCH, "/channels/{channel}/messages/{message}")
DELETE_CHANNEL_MESSAGE: typing.Final[Route] = Route(DELETE, "/channels/{channel}/messages/{message}")

POST_CHANNEL_CROSSPOST: typing.Final[Route] = Route(POST, "/channels/{channel}/messages/{message}/crosspost")

GET_CHANNEL_MESSAGES: typing.Final[Route] = Route(GET, "/channels/{channel}/messages")
POST_CHANNEL_MESSAGES: typing.Final[Route] = Route(POST, "/channels/{channel}/messages")

POST_DELETE_CHANNEL_MESSAGES_BULK: typing.Final[Route] = Route(POST, "/channels/{channel}/messages/bulk-delete")

PUT_CHANNEL_PERMISSIONS: typing.Final[Route] = Route(PUT, "/channels/{channel}/permissions/{overwrite}")
DELETE_CHANNEL_PERMISSIONS: typing.Final[Route] = Route(DELETE, "/channels/{channel}/permissions/{overwrite}")

GET_CHANNEL_PINS: typing.Final[Route] = Route(GET, "/channels/{channel}/pins")
PUT_CHANNEL_PINS: typing.Final[Route] = Route(PUT, "/channels/{channel}/pins/{message}")
DELETE_CHANNEL_PIN: typing.Final[Route] = Route(DELETE, "/channels/{channel}/pins/{message}")

POST_CHANNEL_TYPING: typing.Final[Route] = Route(POST, "/channels/{channel}/typing")

POST_CHANNEL_WEBHOOKS: typing.Final[Route] = Route(POST, "/channels/{channel}/webhooks")
GET_CHANNEL_WEBHOOKS: typing.Final[Route] = Route(GET, "/channels/{channel}/webhooks")

# Stage instances
POST_STAGE_INSTANCE: typing.Final[Route] = Route(POST, "/stage-instances")
GET_STAGE_INSTANCE: typing.Final[Route] = Route(GET, "/stage-instances/{channel}")
PATCH_STAGE_INSTANCE: typing.Final[Route] = Route(PATCH, "/stage-instances/{channel}")
DELETE_STAGE_INSTANCE: typing.Final[Route] = Route(DELETE, "/stage-instances/{channel}")

# Polls
GET_POLL_ANSWER: typing.Final[Route] = Route(GET, "/channels/{channel}/polls/{message}/answer/{answer}")
POST_EXPIRE_POLL: typing.Final[Route] = Route(POST, "/channels/{channel}/polls/{message}/expire")

# Reactions
GET_REACTIONS: typing.Final[Route] = Route(GET, "/channels/{channel}/messages/{message}/reactions/{emoji}")
DELETE_ALL_REACTIONS: typing.Final[Route] = Route(
    DELETE, "/channels/{channel}/messages/{message}/reactions", ratelimit_hash=_JOINED_REACTIONS_HASH
)
DELETE_REACTION_EMOJI: typing.Final[Route] = Route(
    DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}", ratelimit_hash=_JOINED_REACTIONS_HASH
)
DELETE_REACTION_USER: typing.Final[Route] = Route(
    DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}/{user}", ratelimit_hash=_JOINED_REACTIONS_HASH
)

# Guilds
GET_GUILD: typing.Final[Route] = Route(GET, "/guilds/{guild}")
POST_GUILDS: typing.Final[Route] = Route(POST, "/guilds")
PATCH_GUILD: typing.Final[Route] = Route(PATCH, "/guilds/{guild}")
DELETE_GUILD: typing.Final[Route] = Route(DELETE, "/guilds/{guild}")

GET_GUILD_AUDIT_LOGS: typing.Final[Route] = Route(GET, "/guilds/{guild}/audit-logs")

PUT_GUILD_INCIDENT_ACTIONS: typing.Final[Route] = Route(PUT, "/guilds/{guild}/incident-actions")

GET_GUILD_BAN: typing.Final[Route] = Route(GET, "/guilds/{guild}/bans/{user}")
PUT_GUILD_BAN: typing.Final[Route] = Route(PUT, "/guilds/{guild}/bans/{user}")
DELETE_GUILD_BAN: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/bans/{user}")

GET_GUILD_BANS: typing.Final[Route] = Route(GET, "/guilds/{guild}/bans")

GET_GUILD_CHANNELS: typing.Final[Route] = Route(GET, "/guilds/{guild}/channels")
POST_GUILD_CHANNELS: typing.Final[Route] = Route(POST, "/guilds/{guild}/channels")
PATCH_GUILD_CHANNELS: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/channels")

GET_GUILD_WIDGET: typing.Final[Route] = Route(GET, "/guilds/{guild}/widget")
PATCH_GUILD_WIDGET: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/widget")

GET_GUILD_WELCOME_SCREEN: typing.Final[Route] = Route(GET, "/guilds/{guild}/welcome-screen")
PATCH_GUILD_WELCOME_SCREEN: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/welcome-screen")

GET_GUILD_MEMBER_VERIFICATION: typing.Final[Route] = Route(GET, "/guilds/{guild}/member-verification")
PATCH_GUILD_MEMBER_VERIFICATION: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/member-verification")

GET_GUILD_EMOJI: typing.Final[Route] = Route(GET, "/guilds/{guild}/emojis/{emoji}")
PATCH_GUILD_EMOJI: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/emojis/{emoji}")
DELETE_GUILD_EMOJI: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/emojis/{emoji}")

GET_GUILD_EMOJIS: typing.Final[Route] = Route(GET, "/guilds/{guild}/emojis")
POST_GUILD_EMOJIS: typing.Final[Route] = Route(POST, "/guilds/{guild}/emojis")

GET_APPLICATION_EMOJI: typing.Final[Route] = Route(GET, "/applications/{application}/emojis/{emoji}")
PATCH_APPLICATION_EMOJI: typing.Final[Route] = Route(PATCH, "/applications/{application}/emojis/{emoji}")
DELETE_APPLICATION_EMOJI: typing.Final[Route] = Route(DELETE, "/applications/{application}/emojis/{emoji}")

GET_APPLICATION_EMOJIS: typing.Final[Route] = Route(GET, "/applications/{application}/emojis")
POST_APPLICATION_EMOJIS: typing.Final[Route] = Route(POST, "/applications/{application}/emojis")


GET_GUILD_SCHEDULED_EVENT: typing.Final[Route] = Route(GET, "/guilds/{guild}/scheduled-events/{scheduled_event}")
GET_GUILD_SCHEDULED_EVENTS: typing.Final[Route] = Route(GET, "/guilds/{guild}/scheduled-events")
GET_GUILD_SCHEDULED_EVENT_USERS: typing.Final[Route] = Route(
    GET, "/guilds/{guild}/scheduled-events/{scheduled_event}/users"
)
POST_GUILD_SCHEDULED_EVENT: typing.Final[Route] = Route(POST, "/guilds/{guild}/scheduled-events")
PATCH_GUILD_SCHEDULED_EVENT: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/scheduled-events/{scheduled_event}")
DELETE_GUILD_SCHEDULED_EVENT: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/scheduled-events/{scheduled_event}")

GET_GUILD_STICKER: typing.Final[Route] = Route(GET, "/guilds/{guild}/stickers/{sticker}")
PATCH_GUILD_STICKER: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/stickers/{sticker}")
DELETE_GUILD_STICKER: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/stickers/{sticker}")

GET_GUILD_STICKERS: typing.Final[Route] = Route(GET, "/guilds/{guild}/stickers")
POST_GUILD_STICKERS: typing.Final[Route] = Route(POST, "/guilds/{guild}/stickers")

GET_GUILD_INTEGRATIONS: typing.Final[Route] = Route(GET, "/guilds/{guild}/integrations")
DELETE_GUILD_INTEGRATION: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/integrations/{integration}")

GET_GUILD_INVITES: typing.Final[Route] = Route(GET, "/guilds/{guild}/invites")

GET_GUILD_MEMBER: typing.Final[Route] = Route(GET, "/guilds/{guild}/members/{user}")
PATCH_GUILD_MEMBER: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/members/{user}")
PATCH_MY_GUILD_MEMBER: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/members/@me")
PUT_GUILD_MEMBER: typing.Final[Route] = Route(PUT, "/guilds/{guild}/members/{user}")

GET_GUILD_MEMBERS: typing.Final[Route] = Route(GET, "/guilds/{guild}/members")
DELETE_GUILD_MEMBER: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/members/{user}")

GET_GUILD_MEMBERS_SEARCH: typing.Final[Route] = Route(GET, "/guilds/{guild}/members/search")

PUT_GUILD_MEMBER_ROLE: typing.Final[Route] = Route(PUT, "/guilds/{guild}/members/{user}/roles/{role}")
DELETE_GUILD_MEMBER_ROLE: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/members/{user}/roles/{role}")

GET_GUILD_PREVIEW: typing.Final[Route] = Route(GET, "/guilds/{guild}/preview")

GET_GUILD_PRUNE: typing.Final[Route] = Route(GET, "/guilds/{guild}/prune")
POST_GUILD_PRUNE: typing.Final[Route] = Route(POST, "/guilds/{guild}/prune")

GET_GUILD_ROLE: typing.Final[Route] = Route(GET, "/guilds/{guild}/roles/{role}")
PATCH_GUILD_ROLE: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/roles/{role}")
DELETE_GUILD_ROLE: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/roles/{role}")

GET_GUILD_ROLES: typing.Final[Route] = Route(GET, "/guilds/{guild}/roles")
POST_GUILD_ROLES: typing.Final[Route] = Route(POST, "/guilds/{guild}/roles")
PATCH_GUILD_ROLES: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/roles")

GET_GUILD_VANITY_URL: typing.Final[Route] = Route(GET, "/guilds/{guild}/vanity-url")

GET_GUILD_VOICE_STATE: typing.Final[Route] = Route(GET, "/guilds/{guild}/voice-states/{user}")
GET_MY_GUILD_VOICE_STATE: typing.Final[Route] = Route(GET, "/guilds/{guild}/voice-states/@me")

PATCH_GUILD_VOICE_STATE: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/voice-states/{user}")
PATCH_MY_GUILD_VOICE_STATE: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/voice-states/@me")

GET_GUILD_VOICE_REGIONS: typing.Final[Route] = Route(GET, "/guilds/{guild}/regions")

GET_GUILD_WEBHOOKS: typing.Final[Route] = Route(GET, "/guilds/{guild}/webhooks")

GET_GUILD_AUTO_MODERATION_RULES: typing.Final[Route] = Route(GET, "/guilds/{guild}/auto-moderation/rules")
GET_GUILD_AUTO_MODERATION_RULE: typing.Final[Route] = Route(GET, "/guilds/{guild}/auto-moderation/rules/{rule}")
POST_GUILD_AUTO_MODERATION_RULE: typing.Final[Route] = Route(POST, "/guilds/{guild}/auto-moderation/rules")
PATCH_GUILD_AUTO_MODERATION_RULE: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/auto-moderation/rules/{rule}")
DELETE_GUILD_AUTO_MODERATION_RULE: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/auto-moderation/rules/{rule}")

# Stickers
GET_STICKER_PACKS: typing.Final[Route] = Route(GET, "/sticker-packs")
GET_STICKER: typing.Final[Route] = Route(GET, "/stickers/{sticker}")

# Templates
DELETE_GUILD_TEMPLATE: typing.Final[Route] = Route(DELETE, "/guilds/{guild}/templates/{template}")
GET_TEMPLATE: typing.Final[Route] = Route(GET, "/guilds/templates/{template}")
GET_GUILD_TEMPLATES: typing.Final[Route] = Route(GET, "/guilds/{guild}/templates")
PATCH_GUILD_TEMPLATE: typing.Final[Route] = Route(PATCH, "/guilds/{guild}/templates/{template}")
POST_GUILD_TEMPLATES: typing.Final[Route] = Route(POST, "/guilds/{guild}/templates")
POST_TEMPLATE: typing.Final[Route] = Route(POST, "/guilds/templates/{template}")
PUT_GUILD_TEMPLATE: typing.Final[Route] = Route(PUT, "/guilds/{guild}/templates/{template}")

# Invites
GET_INVITE: typing.Final[Route] = Route(GET, "/invites/{invite_code}")
DELETE_INVITE: typing.Final[Route] = Route(DELETE, "/invites/{invite_code}")

# Users
GET_USER: typing.Final[Route] = Route(GET, "/users/{user}")

# @me
POST_MY_CHANNELS: typing.Final[Route] = Route(POST, "/users/@me/channels")
GET_MY_CONNECTIONS: typing.Final[Route] = Route(GET, "/users/@me/connections")  # OAuth2
GET_MY_GUILD_MEMBER: typing.Final[Route] = Route(GET, "/users/@me/guilds/{guild}/member")  # OAuth2
DELETE_MY_GUILD: typing.Final[Route] = Route(DELETE, "/users/@me/guilds/{guild}")
GET_MY_USER_APPLICATION_ROLE_CONNECTIONS: typing.Final[Route] = Route(
    GET, "/users/@me/applications/{application}/role-connection"
)  # OAuth2
PUT_MY_USER_APPLICATION_ROLE_CONNECTIONS: typing.Final[Route] = Route(
    PUT, "/users/@me/applications/{application}/role-connection"
)  # OAuth2

GET_MY_GUILDS: typing.Final[Route] = Route(GET, "/users/@me/guilds")

GET_MY_USER: typing.Final[Route] = Route(GET, "/users/@me")
PATCH_MY_USER: typing.Final[Route] = Route(PATCH, "/users/@me")

PUT_MY_REACTION: typing.Final[Route] = Route(
    PUT, "/channels/{channel}/messages/{message}/reactions/{emoji}/@me", ratelimit_hash=_JOINED_REACTIONS_HASH
)
DELETE_MY_REACTION: typing.Final[Route] = Route(
    DELETE, "/channels/{channel}/messages/{message}/reactions/{emoji}/@me", ratelimit_hash=_JOINED_REACTIONS_HASH
)

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

GET_WEBHOOK_MESSAGE: typing.Final[Route] = Route(GET, "/webhooks/{webhook}/{token}/messages/{message}")
PATCH_WEBHOOK_MESSAGE: typing.Final[Route] = Route(PATCH, "/webhooks/{webhook}/{token}/messages/{message}")
DELETE_WEBHOOK_MESSAGE: typing.Final[Route] = Route(DELETE, "/webhooks/{webhook}/{token}/messages/{message}")

# Applications
GET_APPLICATION_COMMAND: typing.Final[Route] = Route(GET, "/applications/{application}/commands/{command}")
GET_APPLICATION_COMMANDS: typing.Final[Route] = Route(GET, "/applications/{application}/commands")
PATCH_APPLICATION_COMMAND: typing.Final[Route] = Route(PATCH, "/applications/{application}/commands/{command}")
POST_APPLICATION_COMMAND: typing.Final[Route] = Route(POST, "/applications/{application}/commands")
PUT_APPLICATION_COMMANDS: typing.Final[Route] = Route(PUT, "/applications/{application}/commands")
DELETE_APPLICATION_COMMAND: typing.Final[Route] = Route(DELETE, "/applications/{application}/commands/{command}")

GET_APPLICATION_GUILD_COMMAND: typing.Final[Route] = Route(
    GET, "/applications/{application}/guilds/{guild}/commands/{command}"
)
GET_APPLICATION_GUILD_COMMANDS: typing.Final[Route] = Route(GET, "/applications/{application}/guilds/{guild}/commands")
PATCH_APPLICATION_GUILD_COMMAND: typing.Final[Route] = Route(
    PATCH, "/applications/{application}/guilds/{guild}/commands/{command}"
)
POST_APPLICATION_GUILD_COMMAND: typing.Final[Route] = Route(POST, "/applications/{application}/guilds/{guild}/commands")
PUT_APPLICATION_GUILD_COMMANDS: typing.Final[Route] = Route(PUT, "/applications/{application}/guilds/{guild}/commands")
DELETE_APPLICATION_GUILD_COMMAND: typing.Final[Route] = Route(
    DELETE, "/applications/{application}/guilds/{guild}/commands/{command}"
)

GET_APPLICATION_GUILD_COMMANDS_PERMISSIONS: typing.Final[Route] = Route(
    GET, "/applications/{application}/guilds/{guild}/commands/permissions"
)
GET_APPLICATION_COMMAND_PERMISSIONS: typing.Final[Route] = Route(
    GET, "/applications/{application}/guilds/{guild}/commands/{command}/permissions"
)
PUT_APPLICATION_COMMAND_PERMISSIONS: typing.Final[Route] = Route(
    PUT, "/applications/{application}/guilds/{guild}/commands/{command}/permissions"
)

GET_APPLICATION_ROLE_CONNECTION_METADATA_RECORDS: typing.Final[Route] = Route(
    GET, "/applications/{application}/role-connections/metadata"
)
PUT_APPLICATION_ROLE_CONNECTION_METADATA_RECORDS: typing.Final[Route] = Route(
    PUT, "/applications/{application}/role-connections/metadata"
)

# Entitlements (also known as Monetization)
GET_APPLICATION_SKUS: typing.Final[Route] = Route(GET, "/applications/{application}/skus")
GET_APPLICATION_ENTITLEMENTS: typing.Final[Route] = Route(GET, "/applications/{application}/entitlements")
POST_APPLICATION_TEST_ENTITLEMENT: typing.Final[Route] = Route(POST, "/applications/{application}/entitlements")
DELETE_APPLICATION_TEST_ENTITLEMENT: typing.Final[Route] = Route(
    DELETE, "/applications/{application}/entitlements/{entitlement}"
)

# Interactions
# For these endpoints "webhook" is the application ID.
GET_INTERACTION_RESPONSE: typing.Final[Route] = Route(GET, "/webhooks/{webhook}/{token}/messages/@original")
PATCH_INTERACTION_RESPONSE: typing.Final[Route] = Route(PATCH, "/webhooks/{webhook}/{token}/messages/@original")
POST_INTERACTION_RESPONSE: typing.Final[Route] = Route(
    POST, "/interactions/{interaction}/{token}/callback", has_ratelimits=False
)
DELETE_INTERACTION_RESPONSE: typing.Final[Route] = Route(DELETE, "/webhooks/{webhook}/{token}/messages/@original")

# OAuth2 API
GET_MY_APPLICATION: typing.Final[Route] = Route(GET, "/oauth2/applications/@me")
GET_MY_AUTHORIZATION: typing.Final[Route] = Route(GET, "/oauth2/@me")

POST_TOKEN: typing.Final[Route] = Route(POST, "/oauth2/token", has_ratelimits=False)
POST_TOKEN_REVOKE: typing.Final[Route] = Route(POST, "/oauth2/token/revoke", has_ratelimits=False)

# Gateway
GET_GATEWAY: typing.Final[Route] = Route(GET, "/gateway")
GET_GATEWAY_BOT: typing.Final[Route] = Route(GET, "/gateway/bot")

PNG: typing.Final[str] = "PNG"
JPEG_JPG: typing.Final[tuple[str, str]] = ("JPEG", "JPG")
WEBP: typing.Final[str] = "WEBP"
APNG: typing.Final[str] = "APNG"
AWEBP: typing.Final[str] = "AWEBP"
GIF: typing.Final[str] = "GIF"
LOTTIE: typing.Final[str] = "LOTTIE"  # https://airbnb.io/lottie/

CDN_FORMAT_TRANSFORM: typing.Final[dict[str, str]] = {APNG: "png", AWEBP: "webp", LOTTIE: "json"}

# CDN specific endpoints. These reside on a different server.
CDN_CUSTOM_EMOJI: typing.Final[CDNRoute] = CDNRoute("/emojis/{emoji_id}", {PNG, *JPEG_JPG, WEBP, AWEBP, GIF})

CDN_GUILD_ICON: typing.Final[CDNRoute] = CDNRoute("/icons/{guild_id}/{hash}", {PNG, *JPEG_JPG, WEBP, AWEBP, GIF})
CDN_GUILD_SPLASH: typing.Final[CDNRoute] = CDNRoute("/splashes/{guild_id}/{hash}", {PNG, *JPEG_JPG, WEBP})
CDN_GUILD_DISCOVERY_SPLASH: typing.Final[CDNRoute] = CDNRoute(
    "/discovery-splashes/{guild_id}/{hash}", {PNG, *JPEG_JPG, WEBP}
)
CDN_GUILD_BANNER: typing.Final[CDNRoute] = CDNRoute("/banners/{guild_id}/{hash}", {PNG, *JPEG_JPG, WEBP, AWEBP, GIF})

CDN_AVATAR_DECORATION: typing.Final[CDNRoute] = CDNRoute(
    "/avatar-decoration-presets/{hash}", {PNG, *JPEG_JPG, WEBP, APNG}
)
CDN_DEFAULT_USER_AVATAR: typing.Final[CDNRoute] = CDNRoute("/embed/avatars/{style}", {PNG})
CDN_USER_AVATAR: typing.Final[CDNRoute] = CDNRoute("/avatars/{user_id}/{hash}", {PNG, *JPEG_JPG, WEBP, AWEBP, GIF})
CDN_USER_BANNER: typing.Final[CDNRoute] = CDNRoute("/banners/{user_id}/{hash}", {PNG, *JPEG_JPG, WEBP, AWEBP, GIF})
CDN_MEMBER_AVATAR: typing.Final[CDNRoute] = CDNRoute(
    "/guilds/{guild_id}/users/{user_id}/avatars/{hash}", {PNG, *JPEG_JPG, WEBP, AWEBP, GIF}
)
CDN_MEMBER_BANNER: typing.Final[CDNRoute] = CDNRoute(
    "/guilds/{guild_id}/users/{user_id}/banners/{hash}", {PNG, *JPEG_JPG, WEBP, AWEBP, GIF}
)
CDN_ROLE_ICON: typing.Final[CDNRoute] = CDNRoute("/role-icons/{role_id}/{hash}", {PNG, *JPEG_JPG, WEBP})

CDN_APPLICATION_ICON: typing.Final[CDNRoute] = CDNRoute("/app-icons/{application_id}/{hash}", {PNG, *JPEG_JPG, WEBP})
CDN_APPLICATION_COVER: typing.Final[CDNRoute] = CDNRoute("/app-assets/{application_id}/{hash}", {PNG, *JPEG_JPG, WEBP})
CDN_APPLICATION_ASSET: typing.Final[CDNRoute] = CDNRoute("/app-assets/{application_id}/{hash}", {PNG, *JPEG_JPG, WEBP})
CDN_ACHIEVEMENT_ICON: typing.Final[CDNRoute] = CDNRoute(
    "/app-assets/{application_id}/achievements/{achievement_id}/icons/{hash}", {PNG, *JPEG_JPG, WEBP}
)

CDN_TEAM_ICON: typing.Final[CDNRoute] = CDNRoute("/team-icons/{team_id}/{hash}", {PNG, *JPEG_JPG, WEBP})

# undocumented on the Discord docs.
CDN_CHANNEL_ICON: typing.Final[CDNRoute] = CDNRoute("/channel-icons/{channel_id}/{hash}", {PNG, *JPEG_JPG, WEBP})

CDN_STICKER: typing.Final[CDNRoute] = CDNRoute(
    "/stickers/{sticker_id}", {PNG, *JPEG_JPG, LOTTIE, WEBP, AWEBP, APNG, GIF}
)
CDN_STICKER_PACK_BANNER: typing.Final[CDNRoute] = CDNRoute(
    "/app-assets/710982414301790216/store/{hash}", {PNG, *JPEG_JPG, WEBP}
)

SCHEDULED_EVENT_COVER: typing.Final[CDNRoute] = CDNRoute(
    "/guild-events/{scheduled_event_id}/{hash}", {PNG, *JPEG_JPG, WEBP}
)
