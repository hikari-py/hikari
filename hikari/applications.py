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
"""Application and entities related to discord's OAuth2 flow."""

from __future__ import annotations

__all__: typing.List[str] = [
    "InviteApplication",
    "Application",
    "ApplicationFlags",
    "AuthorizationApplication",
    "AuthorizationInformation",
    "ConnectionVisibility",
    "OAuth2AuthorizationToken",
    "OAuth2ImplicitToken",
    "OAuth2Scope",
    "OwnConnection",
    "OwnGuild",
    "PartialOAuth2Token",
    "Team",
    "TeamMember",
    "TeamMembershipState",
    "TokenType",
    "get_token_id",
]

import base64
import typing

import attr

from hikari import guilds
from hikari import snowflakes
from hikari import urls
from hikari import users
from hikari.internal import attr_extensions
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    import datetime

    from hikari import colors
    from hikari import files
    from hikari import permissions as permissions_
    from hikari import traits
    from hikari import webhooks


@typing.final
class ApplicationFlags(enums.Flag):
    """The known application flag bits."""

    VERIFIED_FOR_GUILD_PRESENCES = 1 << 12
    """Denotes that a verified application can use the GUILD_PRESENCES intent."""

    GUILD_PRESENCES_INTENT = 1 << 13
    """Denotes that the application has the GUILD_PRESENCES intent enabled in it's dashboard."""

    VERIFIED_FOR_GUILD_MEMBERS_INTENT = 1 << 14
    """Denotes that a verified application can use the GUILD_MEMBERS intent."""

    GUILD_MEMBERS_INTENT = 1 << 15
    """Denotes that the application has the GUILD_MEMBERS intent enabled in it's dashboard."""

    VERIFICATION_PENDING_GUILD_LIMIT = 1 << 16
    """Denotes that the application's verification is pending."""

    EMBEDDED = 1 << 17
    """Denotes that the application has functionality that's specially embedded in Discord's client."""


@typing.final
class OAuth2Scope(str, enums.Enum):
    """OAuth2 Scopes that Discord allows.

    These are categories of permissions for applications using the OAuth2 API
    directly. Most users will only ever need the `BOT` scope when developing
    bots.
    """

    ACTIVITIES_READ = "activities.read"
    """Enables fetching the "Now Playing/Recently Played" list.

    !!! note
        You must be whitelisted to use this scope.
    """

    ACTIVITIES_WRITE = "activities.write"
    """Enables updating a user's activity.

    !!! note
        You must be whitelisted to use this scope.

    !!! note
        This is not required to use the GameSDK activity manager.
    """

    APPLICATIONS_BUILDS_READ = "applications.builds.read"
    """Enables reading build data for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_BUILDS_UPLOAD = "applications.builds.upload"
    """Enables uploading/updating builds for a user's applications.

    !!! note
        You must be whitelisted to use this scope.
    """

    APPLICATIONS_COMMANDS = "applications.commands"
    """Allows your application's (slash) commands to be used in a guild.

    This is used in Discord's special Bot Authorization Flow like
    `OAuth2Scope.BOT` in-order to join an application into a guild as an
    application command providing integration.
    """

    APPLICATIONS_COMMANDS_UPDATE = "applications.commands.update"
    """Allows your application to update it's (slash) commands via a bearer token."""

    APPLICATIONS_ENTITLEMENTS = "applications.entitlements"
    """Enables reading entitlements for a user's applications."""

    APPLICATIONS_STORE_UPDATE = "applications.store.update"
    """Enables reading/updating store data for the user's applications.

    This includes store listings, achievements, SKU's, etc.

    !!! note
        The store API is deprecated and may be removed in the future.
    """

    BOT = "bot"
    """Enables adding a bot application to a guild.

    !!! note
        This requires you to have set up a bot account for your application.
    """

    CONNECTIONS = "connections"
    """Enables viewing third-party linked accounts such as Twitch."""

    EMAIL = "email"
    """Enable the application to view the user's email and application info."""

    GROUP_DM_JOIN = "gdm.join"
    """Enables joining users into a group DM.

    !!! warning
        This cannot add the bot to a group DM.
    """

    GUILDS = "guilds"
    """Enables viewing the guilds the user is in."""

    GUILDS_JOIN = "guilds.join"
    """Enables adding the user to a specific guild.

    !!! note
        This requires you to have set up a bot account for your application.
    """

    IDENTIFY = "identify"
    """Enables viewing info about itself.

    !!! note
        This does not include email address info. Use the `EMAIL` scope instead
        to retrieve this information.
    """

    RELATIONSHIPS_READ = "relationships.read"
    """Enables viewing a user's friend list.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC = "rpc"
    """Enables the RPC application to control the local user's Discord client.

    !!! note
        You must be whitelisted to use this scope.
    """

    RPC_MESSAGES_READ = "messages.read"
    """Enables the RPC application to read messages from all channels the user is in."""

    RPC_NOTIFICATIONS_READ = "rpc.notifications.read"
    """Enables the RPC application to read  from all channels the user is in.

    !!! note
        You must be whitelisted to use this scope.
    """

    WEBHOOK_INCOMING = "webhook.incoming"
    """Used to generate a webhook that is returned in the OAuth2 token response.

    This is used during authorization code grants.
    """


@typing.final
class ConnectionVisibility(int, enums.Enum):
    """Describes who can see a connection with a third party account."""

    NONE = 0
    """Implies that only you can see the corresponding connection."""

    EVERYONE = 1
    """Everyone can see the connection."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class OwnConnection:
    """Represents a user's connection with a third party account.

    Returned by the `GET Current User Connections` endpoint.
    """

    id: str = attr.field(hash=True, repr=True)
    """The string ID of the third party connected account.

    !!! warning
        Seeing as this is a third party ID, it will not be a snowflakes.
    """

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The username of the connected account."""

    type: str = attr.field(eq=False, hash=False, repr=True)
    """The type of service this connection is for."""

    is_revoked: bool = attr.field(eq=False, hash=False, repr=False)
    """`builtins.True` if the connection has been revoked."""

    integrations: typing.Sequence[guilds.PartialIntegration] = attr.field(eq=False, hash=False, repr=False)
    """A sequence of the partial guild integration objects this connection has."""

    is_verified: bool = attr.field(eq=False, hash=False, repr=False)
    """`builtins.True` if the connection has been verified."""

    is_friend_sync_enabled: bool = attr.field(eq=False, hash=False, repr=False)
    """`builtins.True` if friends should be added based on this connection."""

    is_activity_visible: bool = attr.field(eq=False, hash=False, repr=False)
    """`builtins.True` if this connection's activities are shown in the user's presence."""

    visibility: typing.Union[ConnectionVisibility, int] = attr.field(eq=False, hash=False, repr=True)
    """The visibility of the connection."""


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class OwnGuild(guilds.PartialGuild):
    """Represents a user bound partial guild object."""

    features: typing.Sequence[typing.Union[str, guilds.GuildFeature]] = attr.field(eq=False, hash=False, repr=False)
    """A list of the features in this guild."""

    is_owner: bool = attr.field(eq=False, hash=False, repr=True)
    """`builtins.True` when the current user owns this guild."""

    my_permissions: permissions_.Permissions = attr.field(eq=False, hash=False, repr=False)
    """The guild-level permissions that apply to the current user or bot."""


@typing.final
class TeamMembershipState(int, enums.Enum):
    """Represents the state of a user's team membership."""

    INVITED = 1
    """Denotes the user has been invited to the team but has yet to accept."""

    ACCEPTED = 2
    """Denotes the user has accepted the invite and is now a member."""


@attr_extensions.with_copy
@attr.define(eq=False, hash=False, kw_only=True, weakref_slot=False)
class TeamMember(users.User):
    """Represents a member of a Team."""

    membership_state: typing.Union[TeamMembershipState, int] = attr.field(repr=False)
    """The state of this user's membership."""

    permissions: typing.Sequence[str] = attr.field(repr=False)
    """This member's permissions within a team.

    At the time of writing, this will always be a sequence of one `builtins.str`,
    which will always be `"*"`. This may change in the future, however.
    """

    team_id: snowflakes.Snowflake = attr.field(repr=True)
    """The ID of the team this member belongs to."""

    user: users.User = attr.field(repr=True)
    """The user representation of this team member."""

    @property
    def app(self) -> traits.RESTAware:
        """Return the app that is bound to the user object."""
        return self.user.app

    @property
    def avatar_hash(self) -> typing.Optional[str]:
        return self.user.avatar_hash

    @property
    def avatar_url(self) -> typing.Optional[files.URL]:
        return self.user.avatar_url

    @property
    def default_avatar_url(self) -> files.URL:
        return self.user.default_avatar_url

    @property
    def banner_hash(self) -> typing.Optional[str]:
        return self.user.banner_hash

    @property
    def banner_url(self) -> typing.Optional[files.URL]:
        return self.user.banner_url

    @property
    def accent_color(self) -> typing.Optional[colors.Color]:
        return self.user.accent_color

    @property
    def discriminator(self) -> str:
        return self.user.discriminator

    @property
    def flags(self) -> users.UserFlag:
        return self.user.flags

    @property
    def id(self) -> snowflakes.Snowflake:
        return self.user.id

    @property
    def is_bot(self) -> bool:
        return self.user.is_bot

    @property
    def is_system(self) -> bool:
        return self.user.is_system

    @property
    def mention(self) -> str:
        return self.user.mention

    @property
    def username(self) -> str:
        return self.user.username

    def __str__(self) -> str:
        return str(self.user)

    def __hash__(self) -> int:
        return hash(self.user)

    def __eq__(self, other: object) -> bool:
        return self.user == other


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class Team(snowflakes.Unique):
    """Represents a development team, along with all its members."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attr.field(hash=False, eq=False, repr=True)
    """The name of this team."""

    icon_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The CDN hash of this team's icon.

    If no icon is provided, this will be `builtins.None`.
    """

    members: typing.Mapping[snowflakes.Snowflake, TeamMember] = attr.field(eq=False, hash=False, repr=False)
    """A mapping containing each member in this team.

    The mapping maps keys containing the member's ID to values containing the
    member object.
    """

    owner_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """The ID of this team's owner."""

    def __str__(self) -> str:
        return f"Team {self.name} ({self.id})"

    @property
    def icon_url(self) -> typing.Optional[files.URL]:
        """Team icon URL.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no icon exists.
        """
        return self.make_icon_url()

    def make_icon_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the icon URL for this team if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`. Can be any power
            of two between `16` and `4096` inclusive.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no icon exists.

        Raises
        ------
        builtins.ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.icon_hash is None:
            return None

        return routes.CDN_TEAM_ICON.compile_to_file(
            urls.CDN_URL,
            team_id=self.id,
            hash=self.icon_hash,
            size=size,
            file_format=ext,
        )


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class InviteApplication(guilds.PartialApplication):
    """Represents the information of an Invite Application."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    cover_image_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The CDN's hash of this application's cover image, used in the store or for embedded games."""

    public_key: bytes = attr.field(eq=False, hash=False, repr=False)
    """The key used for verifying interaction and GameSDK payload signatures."""

    @property
    def cover_image_url(self) -> typing.Optional[files.URL]:
        """Cover image URL used in the store or for embedded games.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no cover image exists.
        """
        return self.make_cover_image_url()

    def make_cover_image_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the cover image URL used in the store or for embedded games, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no cover image exists.

        Raises
        ------
        builtins.ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.cover_image_hash is None:
            return None

        return routes.CDN_APPLICATION_COVER.compile_to_file(
            urls.CDN_URL,
            application_id=self.id,
            hash=self.cover_image_hash,
            size=size,
            file_format=ext,
        )


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class Application(guilds.PartialApplication):
    """Represents the information of an Oauth2 Application."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    is_bot_public: bool = attr.field(eq=False, hash=False, repr=True)
    """`builtins.True` if the bot associated with this application is public."""

    is_bot_code_grant_required: bool = attr.field(eq=False, hash=False, repr=False)
    """`builtins.True` if this application's bot is requiring code grant for invites."""

    owner: users.User = attr.field(eq=False, hash=False, repr=True)
    """The application's owner."""

    rpc_origins: typing.Optional[typing.Sequence[str]] = attr.field(eq=False, hash=False, repr=False)
    """A collection of this application's RPC origin URLs, if RPC is enabled."""

    flags: ApplicationFlags = attr.field(eq=False, hash=False, repr=False)
    """The flags for this application."""

    public_key: bytes = attr.field(eq=False, hash=False, repr=False)
    """The key used for verifying interaction and GameSDK payload signatures."""

    team: typing.Optional[Team] = attr.field(eq=False, hash=False, repr=False)
    """The team this application belongs to.

    If the application is not part of a team, this will be `builtins.None`.
    """

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the guild this application is linked to if sold on Discord."""

    primary_sku_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of the primary "Game SKU" of a game that's sold on Discord."""

    slug: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The URL "slug" that is used to point to this application's store page.

    Only applicable to applications sold on Discord.
    """

    cover_image_hash: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The CDN's hash of this application's cover image, used in the store or for embedded games."""

    terms_of_service_url: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The URL of this application's terms of service."""

    privacy_policy_url: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The URL of this application's privacy policy."""

    @property
    def cover_image_url(self) -> typing.Optional[files.URL]:
        """Cover image URL used in the store or for embedded games.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no cover image exists.
        """
        return self.make_cover_image_url()

    def make_cover_image_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the cover image URL used in the store or for embedded games, if set.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or `builtins.None` if no cover image exists.

        Raises
        ------
        builtins.ValueError
            If the size is not an integer power of 2 between 16 and 4096
            (inclusive).
        """
        if self.cover_image_hash is None:
            return None

        return routes.CDN_APPLICATION_COVER.compile_to_file(
            urls.CDN_URL,
            application_id=self.id,
            hash=self.cover_image_hash,
            size=size,
            file_format=ext,
        )

    async def fetch_guild(self) -> typing.Optional[guilds.RESTGuild]:
        """Fetch the guild this application is linked to if sold on Discord.

        Returns
        -------
        typing.Optional[hikari.guilds.RESTGuild]
            The requested guild if the application is linked to a guild, else `builtins.None`.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        if self.guild_id is not None:
            return await self.app.rest.fetch_guild(self.guild_id)
        return None

    async def fetch_guild_preview(self) -> typing.Optional[guilds.GuildPreview]:
        """Fetch the preview of the guild this application is linked to if sold on Discord.

        Returns
        -------
        typing.Optional[hikari.guilds.GuildPreview]
            The requested guild preview if the application is linked to a guild, else `builtins.None`.

        !!! note
            This will only work if you are a part of that guild or it is public.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild is not found or you are not part of the guild.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        if self.guild_id is not None:
            return await self.app.rest.fetch_guild_preview(self.guild_id)

        return None


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class AuthorizationApplication(guilds.PartialApplication):
    """The application model found attached to `AuthorizationInformation`."""

    public_key: bytes = attr.field(eq=False, hash=False, repr=False)
    """The key used for verifying interaction and GameSDK payload signatures."""

    is_bot_public: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=True)
    """`builtins.True` if the bot associated with this application is public.

    Will be `builtins.None` if this application doesn't have an associated bot.
    """

    is_bot_code_grant_required: typing.Optional[bool] = attr.field(eq=False, hash=False, repr=False)
    """`builtins.True` if this application's bot is requiring code grant for invites.

    Will be `builtins.None` if this application doesn't have a bot.
    """

    terms_of_service_url: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The URL of this application's terms of service."""

    privacy_policy_url: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The URL of this application's privacy policy."""


@attr_extensions.with_copy
@attr.define(hash=False, kw_only=True, weakref_slot=False)
class AuthorizationInformation:
    """Model for the data returned by Get Current Authorization Information."""

    application: AuthorizationApplication = attr.field(hash=False, repr=True)
    """The current application."""

    expires_at: datetime.datetime = attr.field(hash=False, repr=True)
    """When the access token this data was retrieved with expires."""

    scopes: typing.Sequence[typing.Union[OAuth2Scope, str]] = attr.field(hash=False, repr=True)
    """A sequence of the scopes the current user has authorized the application for."""

    user: typing.Optional[users.User] = attr.field(hash=False, repr=True)
    """The user who has authorized this token if they included the `identify` scope."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialOAuth2Token:
    """Model for partial OAuth2 token data returned by the API.

    This will generally only be returned when by the client credentials OAuth2
    flow.
    """

    access_token: str = attr.field(hash=True, repr=False)
    """Access token issued by the authorization server."""

    token_type: typing.Union[TokenType, str] = attr.field(eq=False, hash=False, repr=True)
    """Type of token issued by the authorization server."""

    expires_in: datetime.timedelta = attr.field(eq=False, hash=False, repr=True)
    """Lifetime of this access token."""

    scopes: typing.Sequence[typing.Union[OAuth2Scope, str]] = attr.field(eq=False, hash=False, repr=True)
    """Scopes the access token has access to."""

    def __str__(self) -> str:
        return self.access_token


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class OAuth2AuthorizationToken(PartialOAuth2Token):
    """Model for the OAuth2 token data returned by the authorization grant flow."""

    refresh_token: int = attr.field(eq=False, hash=False, repr=False)
    """Refresh token used to obtain new access tokens with the same grant."""

    webhook: typing.Optional[webhooks.IncomingWebhook] = attr.field(eq=False, hash=False, repr=True)
    """Object of the webhook that was created.

    This will only be present if this token was authorized with the
    `webhooks.incoming` scope, otherwise this will be `builtins.None`.
    """

    guild: typing.Optional[guilds.RESTGuild] = attr.field(eq=False, hash=False, repr=True)
    """Object of the guild the user was added to.

    This will only be present if this token was authorized with the
    `bot` scope, otherwise this will be `builtins.None`.
    """


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class OAuth2ImplicitToken(PartialOAuth2Token):
    """Model for the OAuth2 token data returned by the implicit grant flow."""

    state: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """State parameter that was present in the authorization request if provided."""


@typing.final
class TokenType(str, enums.Enum):
    """Token types used within Hikari clients."""

    BOT = "Bot"
    """Bot token type."""

    BASIC = "Basic"
    """OAuth2 basic token type."""

    BEARER = "Bearer"
    """OAuth2 bearer token type."""


def get_token_id(token: str) -> snowflakes.Snowflake:
    """Try to get the bot ID stored in a token.

    Returns
    -------
    hikari.snowflakes.Snowflake
        The ID that was extracted from the token.

    Raises
    ------
    builtins.ValueError
        If the passed token has an unexpected format.
    """
    try:
        segment = token.split(".", 1)[0]
        # I don't trust Discord to always provide the right amount of padding here as they don't
        # with the middle field so just to be safe we will add padding here if necessary to avoid
        # base64.b64decode raising a length or padding error.
        segment += "=" * (len(segment) % 4)
        return snowflakes.Snowflake(base64.b64decode(segment))

    except (TypeError, ValueError, IndexError) as exc:
        raise ValueError("Unexpected token format") from exc
