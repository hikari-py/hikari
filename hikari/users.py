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
"""Application and entities that are used to describe Users on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("OwnUser", "PartialUser", "PremiumType", "User", "UserFlag")

import abc
import typing

import attrs

from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import enums
from hikari.internal import routes

if not typing.TYPE_CHECKING:
    # This is insanely hacky, but it is needed for ruff to not complain until it gets type inference
    from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import datetime

    import typing_extensions  # noqa: TC004

    from hikari import channels
    from hikari import colors
    from hikari import embeds as embeds_
    from hikari import files
    from hikari import guilds
    from hikari import locales
    from hikari import messages
    from hikari.api import special_endpoints


@typing.final
class UserFlag(enums.Flag):
    """The known user flags that represent account badges."""

    NONE = 0
    """None."""

    DISCORD_EMPLOYEE = 1 << 0
    """User is a Discord Employee."""

    PARTNERED_SERVER_OWNER = 1 << 1
    """User owns a partnered Discord server."""

    HYPESQUAD_EVENTS = 1 << 2
    """User participated in HypeSquad Events."""

    BUG_HUNTER_LEVEL_1 = 1 << 3
    """User participated in the Discord Testers community."""

    MFA_SMS = 1 << 4
    """User has SMS enabled as a two-factor authentication method for their account.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    PREMIUM_PROMO_DISMISSED = 1 << 5
    """User has dismissed the current Nitro promotion.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    HYPESQUAD_BRAVERY = 1 << 6
    """User was sorted into the HypeSquad House of Bravery."""

    HYPESQUAD_BRILLIANCE = 1 << 7
    """User was sorted into the HypeSquad House of Brilliance."""

    HYPESQUAD_BALANCE = 1 << 8
    """User was sorted into the HypeSquad House of Balance."""

    EARLY_SUPPORTER = 1 << 9
    """User purchased Discord Nitro before Wednesday, October 10th, 2018."""

    TEAM_USER = 1 << 10
    """Account is a pseudo-user for an app's development team."""

    PARTNER_APPLICANT = 1 << 11
    """User previously applied for the Discord Partner program.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    SYSTEM = 1 << 12
    """Account is a system user used to send official Discord messages.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    HAS_UNREAD_URGENT_MESSAGES = 1 << 13
    """User has unread urgent system messages from Trust & Safety.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    BUG_HUNTER_LEVEL_2 = 1 << 14
    """User went above and beyond in the Discord Testers community."""

    UNDERAGE_DELETED = 1 << 15
    """User's account is pending deletion due to being underage.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    VERIFIED_BOT = 1 << 16
    """App is owned by a team which has a user that has verified their identity with
    Discord's identity verification provider Stripe. App must also meet a list of
    metric requirements.
    """

    EARLY_VERIFIED_DEVELOPER = 1 << 17
    """User owned a verified bot before Tuesday, August 20th, 2019."""

    DISCORD_CERTIFIED_MODERATOR = 1 << 18
    """User passed the Discord Moderator Academy courses and was an active participant in the
    moderator program ecosystem before Thursday, December 1st, 2022."""

    BOT_HTTP_INTERACTIONS = 1 << 19
    """Bot uses only HTTP interactions and is shown in the active member list."""

    SPAMMER = 1 << 20
    """User is suspected of being a spammer and has their messages automatically collapsed from view.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    DISABLE_PREMIUM = 1 << 21
    """User's Nitro features have been disabled.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    ACTIVE_DEVELOPER = 1 << 22
    """User is a developer or team member that owns an app which has had an application command
    executed in the last 30 days.
    """

    PROVISIONAL_ACCOUNT = 1 << 23
    """User is a provisional account used with the social layer integration.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    HIGH_GLOBAL_RATE_LIMIT = 1 << 33
    """User has their global ratelimit raised to 1,200 requests per second.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    DELETED = 1 << 34
    """User's account is deleted.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    DISABLED_SUSPICIOUS_ACTIVITY = 1 << 35
    """User's account is disabled due to suspicious activity and must reset their password.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    SELF_DELETED = 1 << 36
    """User's account is deleted by the user.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    PREMIUM_DISCRIMINATOR = 1 << 37
    """User's account has a custom Nitro discriminator.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    USED_DESKTOP_CLIENT = 1 << 38
    """User has used the desktop client.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    USED_WEB_CLIENT = 1 << 39
    """User has used the web client.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    USED_MOBILE_CLIENT = 1 << 40
    """User has used the mobile client.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    DISABLED = 1 << 41
    """User's account is disabled.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    VERIFIED_EMAIL = 1 << 43
    """User has verified their email address.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    QUARANTINED = 1 << 44
    """User's account is quarantined and can't create DMs or join servers.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    ELIGIBLE_FOR_POMELO_USERNAME_MIGRATION = 1 << 47
    """User is eligible to migrate their account from using discriminators to using the unique username system.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    COLLABORATOR = 1 << 50
    """User is a Discord Collaborator and has permissions roughly equivalent to Employee accounts.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """

    RESTRICTED_COLLABORATOR = 1 << 51
    """User is a restricted Discord Collaborator and has permissions lesser than Employee accounts.

    !!! note
        This flag is not documented, but appears stable and consistent.
    """


@typing.final
class PremiumType(int, enums.Enum):
    """The types of Nitro."""

    NONE = 0
    """No premium."""

    NITRO_CLASSIC = 1
    """Legacy premium tier, including basic perks like animated emojis and avatars."""

    NITRO = 2
    """Premium tier including *all* available perks (e.g. 2 server boosts)."""

    NITRO_BASIC = 3
    """Premium tier including basic perks (e.g. animated emojis and avatars)."""


@attrs.define(kw_only=True, weakref_slot=False)
class AvatarDecoration:
    """Data for an avatar decoration."""

    asset_hash: str = attrs.field(repr=True)
    """The hash of the asset."""

    sku_id: snowflakes.Snowflake = attrs.field(repr=True)
    """The ID of the asset's SKU."""

    expires_at: datetime.datetime | None = attrs.field(repr=True)
    """The datetime at which the user will no longer have access to the avatar decoration."""

    @property
    def url(self) -> files.URL:
        """Return the URL for this avatar decoration."""
        return self.make_url()

    def make_url(self, size: int = 4096) -> files.URL:
        """Generate the url for this avatar decoration.

        Parameters
        ----------
        size
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        hikari.files.URL
            The URL to the avatar decoration.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        return routes.CDN_AVATAR_DECORATION.compile_to_file(
            urls.CDN_URL, hash=self.asset_hash, size=size, file_format="png"
        )


class PartialUser(snowflakes.Unique, abc.ABC):
    """A partial interface for a user.

    Fields may or may not be present, and should be explicitly checked
    before using them to ensure they are not [`hikari.undefined.UNDEFINED`][].

    This is used for endpoints and events that only expose partial user
    information.

    For full user info, consider calling the [`hikari.users.PartialUser.fetch_self`][] method to perform an
    API call.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def app(self) -> traits.RESTAware:
        """Client application that models may use for procedures."""

    @property
    @abc.abstractmethod
    def avatar_decoration(self) -> undefined.UndefinedNoneOr[AvatarDecoration]:
        """Avatar decoration for the user, if they have one, otherwise [`None`][]."""

    @property
    @abc.abstractmethod
    def avatar_hash(self) -> undefined.UndefinedNoneOr[str]:
        """Avatar hash for the user, if they have one, otherwise [`None`][]."""

    @property
    @abc.abstractmethod
    def banner_hash(self) -> undefined.UndefinedNoneOr[str]:
        """Banner hash for the user, if they have one, otherwise [`None`][]."""

    @property
    @abc.abstractmethod
    def accent_color(self) -> undefined.UndefinedNoneOr[colors.Color]:
        """Custom banner color for the user if set, else [`None`][].

        The official client will decide the default color if not set.
        """

    @property
    def accent_colour(self) -> undefined.UndefinedNoneOr[colors.Color]:
        """Alias for the [`hikari.users.PartialUser.accent_color`][] field."""
        return self.accent_color

    @property
    @abc.abstractmethod
    def discriminator(self) -> undefined.UndefinedOr[str]:
        """Discriminator for the user.

        !!! deprecated 2.0.0.dev120
            Discriminators are deprecated and being replaced with "0" by Discord
            during username migration. This field will be removed after migration is complete.
            Learn more here: https://dis.gd/usernames
        """

    @property
    @abc.abstractmethod
    def username(self) -> undefined.UndefinedOr[str]:
        """Username for the user."""

    @property
    @abc.abstractmethod
    def global_name(self) -> undefined.UndefinedNoneOr[str]:
        """Global name for the user, if they have one, otherwise [`None`][]."""

    @property
    def display_name(self) -> undefined.UndefinedNoneOr[str]:
        """Return the user's display name.

        Either users global name (if set) or its username.
        """
        return self.global_name or self.username

    @property
    @abc.abstractmethod
    def is_bot(self) -> undefined.UndefinedOr[bool]:
        """Whether this user is a bot account."""

    @property
    @abc.abstractmethod
    def is_system(self) -> undefined.UndefinedOr[bool]:
        """Whether  this user is a system account."""

    @property
    @abc.abstractmethod
    def flags(self) -> undefined.UndefinedOr[UserFlag]:
        """Flag bits that are set for the user."""

    @property
    @abc.abstractmethod
    def mention(self) -> str:
        """Return a raw mention string for the given user.

        Examples
        --------
        ```py
        >>> some_user.mention
        '<@123456789123456789>'
        ```
        """

    async def fetch_dm_channel(self) -> channels.DMChannel:
        """Fetch the DM channel for this user.

        Returns
        -------
        hikari.channels.DMChannel
            The requested channel.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.create_dm_channel(self.id)

    async def fetch_self(self) -> User:
        """Get this user's up-to-date object by performing an API call.

        Returns
        -------
        hikari.users.User
            The requested user object.

        Raises
        ------
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_user(user=self.id)

    async def send(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages.PartialMessage]] = undefined.UNDEFINED,
        reply_must_exist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[PartialUser] | bool] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[guilds.PartialRole] | bool
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedType | int | messages.MessageFlag = undefined.UNDEFINED,
    ) -> messages.Message:
        """Send a message to this user in DM's.

        Parameters
        ----------
        content
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.

            Likewise, if this is a [`hikari.files.Resource`][], then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.
        attachment
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.

            Attachments can be passed as many different things, to aid in
            convenience.

            - If a [`pathlib.PurePath`][] or [`str`][] to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                [`hikari.files.WebResource`][] such as
                [`hikari.files.URL`][],
                [`hikari.messages.Attachment`][],
                [`hikari.emojis.Emoji`][],
                [`hikari.embeds.EmbedResource`][], etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a [`hikari.files.Bytes`][] is passed, or a [`str`][]
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a [`hikari.files.File`][], [`pathlib.PurePath`][] or
                [`str`][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of [`concurrent.futures.Executor`][] that is being used for
                the application (default is a thread pool which supports this
                behaviour).
        attachments
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        component
            If provided, builder object of the component to include in this message.
        components
            If provided, a sequence of the component builder objects to include
            in this message.
        embed
            If provided, the message embed.
        embeds
            If provided, the message embeds.
        tts
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        reply
            If provided, the message to reply to.
        reply_must_exist
            If provided, whether to error if the message being replied to does
            not exist instead of sending as a normal (non-reply) message.

            This will not do anything if not being used with `reply`.
        mentions_everyone
            If provided, whether the message should parse @everyone/@here
            mentions.
        mentions_reply
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if not being used with `reply`.
        user_mentions
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.
        flags
            If provided, optional flags to set on the message. If
            [`hikari.undefined.UNDEFINED`][], then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are [`hikari.messages.MessageFlag.NONE`][]
            and [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].

        Returns
        -------
        hikari.messages.Message
            The created message.

        Raises
        ------
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        TypeError
            If both `attachment` and `attachments` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; `reply` not found or not in the same
            channel; too many components.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.SEND_MESSAGES`][] in
            the channel or the person you are trying to message has the DM's disabled.
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel_id = None
        if isinstance(self.app, traits.CacheAware):
            channel_id = self.app.cache.get_dm_channel_id(self.id)

        if channel_id is None:
            channel_id = (await self.fetch_dm_channel()).id

        return await self.app.rest.create_message(
            channel=channel_id,
            content=content,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            embed=embed,
            embeds=embeds,
            tts=tts,
            reply=reply,
            reply_must_exist=reply_must_exist,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            mentions_reply=mentions_reply,
            flags=flags,
        )


class User(PartialUser, abc.ABC):
    """Interface for any user-like object.

    This does not include partial users, as they may not be fully formed.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def app(self) -> traits.RESTAware:
        """Client application that models may use for procedures."""

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def accent_color(self) -> colors.Color | None:
        """The custom banner color for the user, if set else [`None`][].

        The official client will decide the default color if not set.
        """

    @property
    @typing_extensions.override
    def accent_colour(self) -> colors.Color | None:
        """Alias for the [`hikari.users.User.accent_color`][] field."""
        return self.accent_color

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def avatar_decoration(self) -> AvatarDecoration | None:
        """Avatar decoration for the user, if they have one, otherwise [`None`][]."""

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def avatar_hash(self) -> str | None:
        """Avatar hash for the user, if they have one, otherwise [`None`][]."""

    @property
    def avatar_url(self) -> files.URL | None:
        """Avatar URL for the user, if they have one set.

        Will be [`None`][] if no custom avatar is set. In this case, you
        should use [`hikari.User.default_avatar_url`][] instead.
        """
        return self.make_avatar_url()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def banner_hash(self) -> str | None:
        """Banner hash for the user, if they have one, otherwise [`None`][]."""

    @property
    def banner_url(self) -> files.URL | None:
        """Banner URL for the user, if they have one set.

        Will be [`None`][] if no custom banner is set.
        """
        return self.make_banner_url()

    @property
    def default_avatar_url(self) -> files.URL:
        """Default avatar URL for this user."""
        if self.discriminator == "0":  # migrated account
            return routes.CDN_DEFAULT_USER_AVATAR.compile_to_file(
                urls.CDN_URL, style=(self.id >> 22) % 6, file_format="png"
            )

        return routes.CDN_DEFAULT_USER_AVATAR.compile_to_file(
            urls.CDN_URL, style=int(self.discriminator) % 5, file_format="png"
        )

    @property
    def display_avatar_decoration(self) -> AvatarDecoration | None:
        """Display avatar decoration for the user, if they have one set.

        Will be [`None`][] if no avatar decoration is set.
        """
        return self.avatar_decoration

    @property
    def display_avatar_url(self) -> files.URL:
        """Display avatar URL for this user."""
        return self.make_avatar_url() or self.default_avatar_url

    @property
    def display_banner_url(self) -> files.URL | None:
        """Display banner URL for this user, if they have one set.

        Will be [`None`][] if no custom banner is set.
        """
        return self.make_banner_url()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def discriminator(self) -> str:
        """Discriminator for the user.

        !!! deprecated 2.0.0.dev120
            Discriminators are deprecated and being replaced with "0" by Discord
            during username migration. This field will be removed after migration is complete.
            Learn more here: https://dis.gd/usernames
        """

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def flags(self) -> UserFlag:
        """Flag bits that are set for the user."""

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def is_bot(self) -> bool:
        """Whether this user is a bot account."""

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def is_system(self) -> bool:
        """Whether this user is a system account."""

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def mention(self) -> str:
        """Return a raw mention string for the given user.

        Examples
        --------
        ```py
        >>> some_user.mention
        '<@123456789123456789>'
        ```
        """

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def username(self) -> str:
        """Username for the user."""

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def global_name(self) -> str | None:
        """Global name for the user, if they have one, otherwise [`None`][]."""

    def make_avatar_url(self, *, ext: str | None = None, size: int = 4096) -> files.URL | None:
        """Generate the avatar URL for this user, if set.

        If no custom avatar is set, this returns [`None`][]. You can then
        use the [`hikari.User.default_avatar_url`][] attribute instead to fetch
        the displayed URL.

        Parameters
        ----------
        ext
            The ext to use for this URL.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated). Will be ignored for default avatars which can only be
            `png`.

            If [`None`][], then the correct default extension is
            determined based on whether the icon is animated or not.
        size
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.
            Will be ignored for default avatars.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the avatar, or [`None`][] if not present.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.avatar_hash is None:
            return None

        if ext is None:
            ext = "gif" if self.avatar_hash.startswith("a_") else "png"

        return routes.CDN_USER_AVATAR.compile_to_file(
            urls.CDN_URL, user_id=self.id, hash=self.avatar_hash, size=size, file_format=ext
        )

    def make_banner_url(self, *, ext: str | None = None, size: int = 4096) -> files.URL | None:
        """Generate the banner URL for this user, if set.

        If no custom banner is set, this returns [`None`][].

        Parameters
        ----------
        ext
            The ext to use for this URL.
            Supports `png`, `jpeg`, `jpg`, `webp` and `gif` (when
            animated).

            If [`None`][], then the correct default extension is
            determined based on whether the banner is animated or not.
        size
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL to the banner, or [`None`][] if not present.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.banner_hash is None:
            return None

        if ext is None:
            ext = "gif" if self.banner_hash.startswith("a_") else "png"

        return routes.CDN_USER_BANNER.compile_to_file(
            urls.CDN_URL, user_id=self.id, hash=self.banner_hash, size=size, file_format=ext
        )


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class PartialUserImpl(PartialUser):
    """Implementation for partial information about a user.

    This is pretty much the same as a normal user, but information may not be
    present, which will be denoted by [`hikari.undefined.UNDEFINED`][].
    """

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this user."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    discriminator: undefined.UndefinedOr[str] = attrs.field(eq=False, hash=False, repr=True)
    """Four-digit discriminator for the user if unmigrated.

    !!! deprecated 2.0.0.dev120
        Discriminators are deprecated and being replaced with "0" by Discord
        during username migration. This field will be removed after migration is complete.
        Learn more here: https://dis.gd/usernames
    """

    username: undefined.UndefinedOr[str] = attrs.field(eq=False, hash=False, repr=True)
    """Username of the user."""

    global_name: undefined.UndefinedNoneOr[str] = attrs.field(eq=False, hash=False, repr=True)
    """Global name of the user."""

    avatar_decoration: undefined.UndefinedNoneOr[AvatarDecoration] = attrs.field(eq=False, hash=False, repr=False)
    """Avatar decoration of the user, if an avatar decoration is set."""

    avatar_hash: undefined.UndefinedNoneOr[str] = attrs.field(eq=False, hash=False, repr=False)
    """Avatar hash of the user, if a custom avatar is set."""

    banner_hash: undefined.UndefinedNoneOr[str] = attrs.field(eq=False, hash=False, repr=False)
    """Banner hash of the user, if a custom banner is set."""

    accent_color: undefined.UndefinedNoneOr[colors.Color] = attrs.field(eq=False, hash=False, repr=False)
    """The custom banner color for the user, if set.

    The official client will decide the default color if not set.
    """

    is_bot: undefined.UndefinedOr[bool] = attrs.field(eq=False, hash=False, repr=True)
    """Whether this user is a bot account."""

    is_system: undefined.UndefinedOr[bool] = attrs.field(eq=False, hash=False, repr=True)
    """Whether this user is a system account."""

    flags: undefined.UndefinedOr[UserFlag] = attrs.field(eq=False, hash=False, repr=True)
    """Public flags for this user."""

    @property
    @typing_extensions.override
    def mention(self) -> str:
        """Return a raw mention string for the given user.

        Examples
        --------
        ```py
        >>> some_user.mention
        '<@123456789123456789>'
        ```
        """
        return f"<@{self.id}>"

    @typing_extensions.override
    def __str__(self) -> str:
        if self.username is undefined.UNDEFINED or self.discriminator is undefined.UNDEFINED:
            return f"Partial user ID {self.id}"
        if self.discriminator == "0":  # migrated account
            return self.username
        return f"{self.username}#{self.discriminator}"


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class UserImpl(PartialUserImpl, User):
    """Concrete implementation of user information."""

    discriminator: str = attrs.field(eq=False, hash=False, repr=True)
    """The user's discriminator.

    !!! deprecated 2.0.0.dev120
        Discriminators are deprecated and being replaced with "0" by Discord
        during username migration. This field will be removed after migration is complete.
        Learn more here: https://dis.gd/usernames
    """

    username: str = attrs.field(eq=False, hash=False, repr=True)
    """The user's username."""

    global_name: str | None = attrs.field(eq=False, hash=False, repr=True)
    """The user's global name."""

    avatar_decoration: AvatarDecoration | None = attrs.field(eq=False, hash=False, repr=False)
    """Avatar decoration of the user, if they have one."""

    avatar_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The user's avatar hash, if they have one, otherwise [`None`][]."""

    banner_hash: str | None = attrs.field(eq=False, hash=False, repr=False)
    """Banner hash of the user, if they have one, otherwise [`None`][]"""

    accent_color: colors.Color | None = attrs.field(eq=False, hash=False, repr=False)
    """The custom banner color for the user, if set.

    The official client will decide the default color if not set.
    """

    is_bot: bool = attrs.field(eq=False, hash=False, repr=True)
    """[`True`][] if this user is a bot account, [`False`][] otherwise."""

    is_system: bool = attrs.field(eq=False, hash=False, repr=True)
    """[`True`][] if this user is a system account, [`False`][] otherwise."""

    flags: UserFlag = attrs.field(eq=False, hash=False, repr=True)
    """The public flags for this user."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class OwnUser(UserImpl):
    """Represents a user with extended OAuth2 information."""

    is_mfa_enabled: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the user's account has multi-factor authentication enabled."""

    locale: str | locales.Locale | None = attrs.field(eq=False, hash=False, repr=False)
    """The user's set locale.

    This is not provided in the `READY` event.
    """

    is_verified: bool | None = attrs.field(eq=False, hash=False, repr=False)
    """Whether the email for this user's account has been verified.

    Will be [`None`][] if retrieved through the OAuth2 flow without the `email`
    scope.
    """

    email: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The user's set email.

    Will be [`None`][] if retrieved through OAuth2 flow without the `email`
    scope. Will always be [`None`][] for bot users.
    """

    premium_type: PremiumType | int | None = attrs.field(eq=False, hash=False, repr=False)
    """The type of Nitro Subscription this user account had.

    This will always be [`None`][] for bots.
    """

    @typing_extensions.override
    async def fetch_self(self) -> OwnUser:
        """Get this user's up-to-date object.

        Returns
        -------
        hikari.users.OwnUser
            The requested user object.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_my_user()

    @typing_extensions.override
    async def fetch_dm_channel(self) -> typing.NoReturn:
        msg = "Unable to fetch your own DM channel"
        raise TypeError(msg)

    @typing_extensions.override
    async def send(
        self,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages.PartialMessage]] = undefined.UNDEFINED,
        reply_must_exist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[PartialUser] | bool] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[guilds.PartialRole] | bool
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedType | int | messages.MessageFlag = undefined.UNDEFINED,
    ) -> typing.NoReturn:
        msg = "Unable to send a DM to yourself"
        raise TypeError(msg)
