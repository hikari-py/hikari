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
"""Special additional endpoints used by the REST API."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "AutoModActionBuilder",
    "AutoModBlockMemberInteractionActionBuilder",
    "AutoModBlockMessageActionBuilder",
    "AutoModKeywordPresetTriggerBuilder",
    "AutoModKeywordTriggerBuilder",
    "AutoModMemberProfileTriggerBuilder",
    "AutoModMentionSpamTriggerBuilder",
    "AutoModSendAlertMessageActionBuilder",
    "AutoModSpamTriggerBuilder",
    "AutoModTimeoutActionBuilder",
    "AutoModTriggerBuilder",
    "AutocompleteChoiceBuilder",
    "ButtonBuilder",
    "ChannelSelectMenuBuilder",
    "CommandBuilder",
    "ComponentBuilder",
    "ContainerComponentBuilder",
    "ContextMenuCommandBuilder",
    "FileComponentBuilder",
    "InteractionAutocompleteBuilder",
    "InteractionDeferredBuilder",
    "InteractionMessageBuilder",
    "InteractionModalBuilder",
    "InteractionResponseBuilder",
    "InteractiveButtonBuilder",
    "LinkButtonBuilder",
    "MediaGalleryComponentBuilder",
    "MediaGalleryItemBuilder",
    "MessageActionRowBuilder",
    "ModalActionRowBuilder",
    "PollAnswerBuilder",
    "PollBuilder",
    "SectionComponentBuilder",
    "SelectMenuBuilder",
    "SelectOptionBuilder",
    "SeparatorComponentBuilder",
    "SlashCommandBuilder",
    "TextDisplayComponentBuilder",
    "TextInputBuilder",
    "TextSelectMenuBuilder",
    "ThumbnailComponentBuilder",
    "TypingIndicator",
)

import abc
import typing

from hikari import components as components_
from hikari import polls
from hikari import undefined
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import types

    from typing_extensions import Self

    from hikari import applications
    from hikari import auto_mod
    from hikari import channels
    from hikari import colors
    from hikari import commands
    from hikari import embeds as embeds_
    from hikari import emojis
    from hikari import files
    from hikari import guilds
    from hikari import locales
    from hikari import messages
    from hikari import permissions as permissions_
    from hikari import snowflakes
    from hikari import users
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import rest as rest_api
    from hikari.interactions import base_interactions

_ParentT = typing.TypeVar("_ParentT")


class TypingIndicator(abc.ABC):
    """Result type of [`hikari.api.rest.RESTClient.trigger_typing`][].

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.

    !!! note
        This is a helper class that is used by [`hikari.api.rest.RESTClient`][].
        You should only ever need to use instances of this class that are
        produced by that API.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def __await__(self) -> typing.Generator[None, typing.Any, None]: ...

    @abc.abstractmethod
    async def __aenter__(self) -> None: ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        exception_traceback: types.TracebackType | None,
    ) -> None: ...


class InteractionResponseBuilder(abc.ABC):
    """Base class for all interaction response builders used in the interaction server."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def type(self) -> int | base_interactions.ResponseType:
        """Type of this response."""

    @abc.abstractmethod
    def build(
        self, entity_factory: entity_factory_.EntityFactory, /
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        """Build a JSON object from this builder.

        Parameters
        ----------
        entity_factory
            The entity factory to use to serialize entities within this builder.

        Returns
        -------
        typing.Tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[Files.AsyncReader]]
            A tuple of the built json object representation of this builder and
            a sequence of up to 10 files to send with the response.
        """


class InteractionDeferredBuilder(InteractionResponseBuilder, abc.ABC):
    """Interface of a deferred message interaction response builder."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> base_interactions.DeferredResponseTypesT:
        """Type of this response."""

    @property
    @abc.abstractmethod
    def flags(self) -> undefined.UndefinedType | int | messages.MessageFlag:
        """Message flags this response should have.

        !!! note
            As of writing the only message flags which can be set here are
            [`hikari.messages.MessageFlag.EPHEMERAL`][], [`hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS`][]
            and [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].
        """

    @abc.abstractmethod
    def set_flags(self, flags: undefined.UndefinedType | int | messages.MessageFlag, /) -> Self:
        """Set message flags for this response.

        !!! note
            As of writing, the only message flags which can be set are [`hikari.messages.MessageFlag.EPHEMERAL`][]
            [`hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS`][] and
            [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].

        Parameters
        ----------
        flags
            The message flags to set for this response.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder.
        """


class AutocompleteChoiceBuilder(abc.ABC):
    """Interface of an autocomplete choice used to respond to interactions."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The choice's name."""

    @property
    @abc.abstractmethod
    def value(self) -> int | str | float:
        """The choice's value."""

    @abc.abstractmethod
    def set_name(self, name: str, /) -> Self:
        """Set this choice's name.

        Returns
        -------
        AutocompleteChoiceBuilder
            The autocomplete choice builder.
        """

    @abc.abstractmethod
    def set_value(self, value: float | str, /) -> Self:
        """Set this choice's value.

        Returns
        -------
        AutocompleteChoiceBuilder
            The autocomplete choice builder.
        """

    @abc.abstractmethod
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        """Build a JSON object from this builder.

        Returns
        -------
        typing.MutableMapping[str, typing.Any]
            The built json object representation of this builder.
        """


class InteractionAutocompleteBuilder(InteractionResponseBuilder, abc.ABC):
    """Interface of an autocomplete interaction response builder."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def choices(self) -> typing.Sequence[AutocompleteChoiceBuilder]:
        """Autocomplete choices."""

    @abc.abstractmethod
    def set_choices(self, choices: typing.Sequence[AutocompleteChoiceBuilder], /) -> Self:
        """Set autocomplete choices.

        Parameters
        ----------
        choices
            The choices to set.

        Returns
        -------
        InteractionAutocompleteBuilder
            Object of this builder.
        """


class InteractionMessageBuilder(InteractionResponseBuilder, abc.ABC):
    """Interface of an interaction message response builder used within REST servers.

    This can be returned by the listener registered to
    [`hikari.api.interaction_server.InteractionServer`][] as a response to the interaction
    create.
    """

    __slots__: typing.Sequence[str] = ()

    # Required fields

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> base_interactions.MessageResponseTypesT:
        """Type of this response."""

    # Extendable fields

    @property
    @abc.abstractmethod
    def attachments(self) -> undefined.UndefinedNoneOr[typing.Sequence[files.Resourceish]]:
        """Sequence of up to 10 attachments to send with the message."""

    @property
    @abc.abstractmethod
    def components(self) -> undefined.UndefinedNoneOr[typing.Sequence[ComponentBuilder]]:
        """Sequence of up to 5 component builders to send in this response."""

    @property
    @abc.abstractmethod
    def embeds(self) -> undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]]:
        """Sequence of up to 10 of the embeds included in this response."""

    # Settable fields

    @property
    @abc.abstractmethod
    def content(self) -> undefined.UndefinedNoneOr[str]:
        """Response's message content."""

    @property
    @abc.abstractmethod
    def flags(self) -> undefined.UndefinedType | int | messages.MessageFlag:
        """Message flags this response should have.

        !!! note
            As of writing the only message flags which can be set here are
            [`hikari.messages.MessageFlag.EPHEMERAL`][],
            [`hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS`][]
            and [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].
        """

    @property
    @abc.abstractmethod
    def is_tts(self) -> undefined.UndefinedOr[bool]:
        """Whether this response's content should be treated as text-to-speech."""

    @property
    @abc.abstractmethod
    def mentions_everyone(self) -> undefined.UndefinedOr[bool]:
        """Whether @everyone and @here mentions should be enabled for this response."""

    @property
    @abc.abstractmethod
    def role_mentions(self) -> undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole] | bool]:
        """Whether and what role mentions should be enabled for this response.

        Either a sequence of object/IDs of the roles mentions should be enabled
        for, [`False`][] or [`hikari.undefined.UNDEFINED`][] to disallow any
        role mentions or [`True`][] to allow all role mentions.
        """

    @property
    @abc.abstractmethod
    def user_mentions(self) -> undefined.UndefinedOr[snowflakes.SnowflakeishSequence[users.PartialUser] | bool]:
        """Whether and what user mentions should be enabled for this response.

        Either a sequence of object/IDs of the users mentions should be enabled
        for, [`False`][] or [`hikari.undefined.UNDEFINED`][] to disallow any
        user mentions or [`True`][] to allow all user mentions.
        """

    @property
    @abc.abstractmethod
    def poll(self) -> undefined.UndefinedOr[PollBuilder]:
        """The poll to include with this response."""

    @abc.abstractmethod
    def clear_attachments(self, /) -> Self:
        """Clear attachments for this response.

        This is only useful for message update responses, where you might want to
        remove all existing attachments.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder.
        """

    @abc.abstractmethod
    def add_attachment(self, attachment: files.Resourceish, /) -> Self:
        """Add an attachment to this response.

        Parameters
        ----------
        attachment
            The attachment to add.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder.
        """

    @abc.abstractmethod
    def add_component(self, component: ComponentBuilder, /) -> Self:
        """Add a component to this response.

        Parameters
        ----------
        component
            The component builder to add to this response.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder.
        """

    @abc.abstractmethod
    def clear_components(self, /) -> Self:
        """Clear the components set for this response.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def add_embed(self, embed: embeds_.Embed, /) -> Self:
        """Add an embed to this response.

        Parameters
        ----------
        embed
            Object of the embed to add to this response.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def clear_embeds(self, /) -> Self:
        """Clear the embeds set for this embed.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_content(self, content: undefined.UndefinedOr[str], /) -> Self:
        """Set the response's message content.

        Parameters
        ----------
        content
            The message content to set for this response.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_flags(self, flags: undefined.UndefinedType | int | messages.MessageFlag, /) -> Self:
        """Set message flags for this response.

        !!! note
            As of writing, the only message flags which can be set is
            [`hikari.messages.MessageFlag.EPHEMERAL`][] and [`hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS`][].

        Parameters
        ----------
        flags
            The message flags to set for this response.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_tts(self, tts: undefined.UndefinedOr[bool], /) -> Self:
        """Set whether this response should trigger text-to-speech processing.

        Parameters
        ----------
        tts
            Whether this response should trigger text-to-speech processing.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_mentions_everyone(self, mentions: undefined.UndefinedOr[bool] = undefined.UNDEFINED, /) -> Self:
        """Set whether this response should be able to mention @everyone/@here.

        Parameters
        ----------
        mentions
            Whether this response should be able to mention @everyone/@here.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_role_mentions(
        self,
        mentions: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[guilds.PartialRole] | bool
        ] = undefined.UNDEFINED,
        /,
    ) -> Self:
        """Set whether and what role mentions should be possible for this response.

        Parameters
        ----------
        mentions
            Either a sequence of object/IDs of the roles mentions should be enabled for,
            [`False`][] or [`hikari.undefined.UNDEFINED`][] to disallow any role
            mentions or [`True`][] to allow all role mentions.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_user_mentions(
        self,
        mentions: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[users.PartialUser] | bool
        ] = undefined.UNDEFINED,
        /,
    ) -> Self:
        """Set whether and what user mentions should be possible for this response.

        Parameters
        ----------
        mentions
            Either a sequence of object/IDs of the users mentions should be enabled for,
            [`False`][] or [`hikari.undefined.UNDEFINED`][] to disallow any user
            mentions or [`True`][] to allow all user mentions.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_poll(self, poll: undefined.UndefinedOr[PollBuilder], /) -> Self:
        """Set the poll to include with this response.

        Parameters
        ----------
        poll
            The poll to include with this response, or [`hikari.undefined.UNDEFINED`][]
            to remove a previously added poll.

        Returns
        -------
        InteractionMessageBuilder
            Object of this builder to allow for chained calls.
        """


class InteractionModalBuilder(InteractionResponseBuilder, abc.ABC):
    """Interface of an interaction modal response builder used within REST servers.

    This can be returned by the listener registered to
    [`hikari.api.interaction_server.InteractionServer`][] as a response to the interaction
    create.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[base_interactions.ResponseType.MODAL]:
        """Type of this response."""

    @property
    @abc.abstractmethod
    def title(self) -> str:
        """Title that will show up in the modal."""

    @property
    @abc.abstractmethod
    def custom_id(self) -> str:
        """Developer set custom ID used for identifying interactions with this modal."""

    @property
    @abc.abstractmethod
    def components(self) -> undefined.UndefinedOr[typing.Sequence[ComponentBuilder]]:
        """Sequence of component builders to send in this modal."""

    @abc.abstractmethod
    def set_title(self, title: str, /) -> Self:
        """Set the title that will show up in the modal.

        Parameters
        ----------
        title
            The title that will show up in the modal.
        """

    @abc.abstractmethod
    def set_custom_id(self, custom_id: str, /) -> Self:
        """Set the custom ID used for identifying interactions with this modal.

        Parameters
        ----------
        custom_id
            The developer set custom ID used for identifying interactions with this modal.
        """

    @abc.abstractmethod
    def add_component(self, component: ComponentBuilder, /) -> Self:
        """Add a component to this modal.

        Parameters
        ----------
        component
            The component builder to add to this modal.
        """


class InteractionPremiumRequiredBuilder(InteractionResponseBuilder, abc.ABC):
    """Interface of an interaction premium required response builder used within REST servers.

    This can be returned by the listener registered to
    `hikari.api.interaction_server.InteractionServer` as a response to the interaction
    create.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[base_interactions.ResponseType.PREMIUM_REQUIRED]:
        """Type of this response."""


class CommandBuilder(abc.ABC):
    """Interface of a command builder used when bulk creating commands over REST."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        r"""Name to set for this command.

        !!! warning
            This should match the regex `^[-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$` in Unicode mode
            and must be lowercase.
        """

    @property
    @abc.abstractmethod
    def type(self) -> commands.CommandType:
        """Type of this command."""

    @property
    @abc.abstractmethod
    def id(self) -> undefined.UndefinedOr[snowflakes.Snowflake]:
        """ID of this command."""

    @property
    @abc.abstractmethod
    def default_member_permissions(self) -> undefined.UndefinedType | permissions_.Permissions | int:
        """Member permissions necessary to utilize this command by default.

        If `0`, then it will be available for all members. Note that this doesn't affect
        administrators of the guild and overwrites.
        """

    @property
    @abc.abstractmethod
    def is_nsfw(self) -> undefined.UndefinedOr[bool]:
        """Whether this command age-restricted."""

    @property
    @abc.abstractmethod
    def name_localizations(self) -> typing.Mapping[locales.Locale | str, str]:
        """Name localizations set for this command."""

    @property
    @abc.abstractmethod
    def integration_types(self) -> undefined.UndefinedOr[typing.Sequence[applications.ApplicationIntegrationType]]:
        """The integration types allowed for this command."""

    @property
    @abc.abstractmethod
    def context_types(self) -> undefined.UndefinedOr[typing.Sequence[applications.ApplicationContextType]]:
        """The context types allowed for this command."""

    @abc.abstractmethod
    def set_name(self, name: str, /) -> Self:
        """Set the name of this command.

        Parameters
        ----------
        name
            The name to set for this command.

        Returns
        -------
        CommandBuilder
            Object of this command builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_id(self, id_: undefined.UndefinedOr[snowflakes.Snowflakeish], /) -> Self:
        """Set the ID of this command.

        Parameters
        ----------
        id_
            The ID to set for this command.

        Returns
        -------
        CommandBuilder
            Object of this command builder to allow for chained calls.
        """

    @abc.abstractmethod
    def set_default_member_permissions(
        self, default_member_permissions: undefined.UndefinedType | int | permissions_.Permissions, /
    ) -> Self:
        """Set the member permissions necessary to utilize this command by default.

        Parameters
        ----------
        default_member_permissions
            The default member permissions to utilize this command by default.

            If `0`, then it will be available for all members. Note that this doesn't affect
            administrators of the guild and overwrites.

        Returns
        -------
        CommandBuilder
            Object of this command builder.
        """

    @abc.abstractmethod
    def set_is_nsfw(self, state: undefined.UndefinedOr[bool], /) -> Self:
        """Set whether this command will be age-restricted.

        Parameters
        ----------
        state
            Whether this command is age-restricted.

        Returns
        -------
        CommandBuilder
            Object of this command builder for chained calls.
        """

    @abc.abstractmethod
    def set_name_localizations(self, name_localizations: typing.Mapping[locales.Locale | str, str], /) -> Self:
        """Set the name localizations for this command.

        Parameters
        ----------
        name_localizations
            The name localizations to set for this command.

        Returns
        -------
        CommandBuilder
            Object of this command builder.
        """

    @abc.abstractmethod
    def set_integration_types(
        self, integration_types: undefined.UndefinedOr[typing.Sequence[applications.ApplicationIntegrationType]]
    ) -> Self:
        """Set the integration types for this command.

        Parameters
        ----------
        integration_types
            The integration types to set for this command.

        Returns
        -------
        CommandBuilder
            Object of this command builder.
        """

    @abc.abstractmethod
    def set_context_types(
        self, context_types: undefined.UndefinedOr[typing.Sequence[applications.ApplicationContextType]]
    ) -> Self:
        """Set the context types for this command.

        Parameters
        ----------
        context_types
            The context types to set for this command.

        Returns
        -------
        CommandBuilder
            Object of this command builder.
        """

    @abc.abstractmethod
    def build(self, entity_factory: entity_factory_.EntityFactory, /) -> typing.MutableMapping[str, typing.Any]:
        """Build a JSON object from this builder.

        Parameters
        ----------
        entity_factory
            The entity factory to use to serialize entities within this builder.

        Returns
        -------
        typing.MutableMapping[str, typing.Any]
            The built json object representation of this builder.
        """

    @abc.abstractmethod
    async def create(
        self,
        rest: rest_api.RESTClient,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        /,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.PartialCommand:
        """Create this command through a REST call.

        Parameters
        ----------
        rest
            The REST client to use to make this request.
        application
            The application to create this command for.
        guild
            The guild to create this command for.

            If left undefined then this command will be declared globally.

        Returns
        -------
        hikari.commands.PartialCommand
            The created command.
        """


class SlashCommandBuilder(CommandBuilder):
    """SlashCommandBuilder."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Command's description.

        !!! warning
            This should be inclusively between 1-100 characters in length.
        """

    @property
    @abc.abstractmethod
    def description_localizations(self) -> typing.Mapping[locales.Locale | str, str]:
        """Command's localised descriptions."""

    @property
    @abc.abstractmethod
    def options(self) -> typing.Sequence[commands.CommandOption]:
        """Sequence of up to 25 of the options set for this command."""

    @abc.abstractmethod
    def set_description(self, description: str, /) -> Self:
        """Set the description for this command.

        Parameters
        ----------
        description
            The description to set for this command.

        Returns
        -------
        SlashCommandBuilder
            Object of this command builder.
        """

    @abc.abstractmethod
    def set_description_localizations(
        self, description_localizations: typing.Mapping[locales.Locale | str, str], /
    ) -> Self:
        """Set the localised descriptions for this command.

        Parameters
        ----------
        description_localizations
            The description localizations to set for this command.

        Returns
        -------
        SlashCommandBuilder
            Object of this command builder.
        """

    @abc.abstractmethod
    def add_option(self, option: commands.CommandOption) -> Self:
        """Add an option to this command.

        !!! note
            A command can have up to 25 options.

        Parameters
        ----------
        option
            The option to add to this command.

        Returns
        -------
        SlashCommandBuilder
            Object of this command builder to allow for chained calls.
        """

    @abc.abstractmethod
    @typing_extensions.override
    async def create(
        self,
        rest: rest_api.RESTClient,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        /,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.SlashCommand:
        """Create this command through a REST call.

        This is a shorthand for calling [`hikari.api.rest.RESTClient.create_slash_command`][]
        with the builder's information.

        Parameters
        ----------
        rest
            The REST client to use to make this request.
        application
            The application to create this command for.
        guild
            The guild to create this command for.

            If left undefined then this command will be declared globally.

        Returns
        -------
        hikari.commands.SlashCommand
            The created command.
        """


class ContextMenuCommandBuilder(CommandBuilder):
    """ContextMenuCommandBuilder."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    @typing_extensions.override
    async def create(
        self,
        rest: rest_api.RESTClient,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        /,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.ContextMenuCommand:
        """Create this command through a REST call.

        This is a shorthand for calling
        [`hikari.api.rest.RESTClient.create_context_menu_command`][]
        with the builder's information.

        Parameters
        ----------
        rest
            The REST client to use to make this request.
        application
            The application to create this command for.
        guild
            The guild to create this command for.

            If left undefined then this command will be declared globally.

        Returns
        -------
        hikari.commands.ContextMenuCommand
            The created command.
        """


class ComponentBuilder(abc.ABC):
    """Base class for all component builder classes."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def type(self) -> int | components_.ComponentType:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def id(self) -> undefined.UndefinedOr[int]:
        """ID of the component.

        It will be used to order components in the layout.

        If not provided, it will be auto populated through increment.
        """

    @abc.abstractmethod
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        """Build a JSON object from this builder and collects all attachments added as components.

        Returns
        -------
        tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]
            The built json object representation of this builder, and the attachments added.
        """


class ButtonBuilder(ComponentBuilder, abc.ABC):
    """Builder class for a message button component."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.BUTTON]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def style(self) -> components_.ButtonStyle | int:
        """Button's style."""

    @property
    @abc.abstractmethod
    def emoji(self) -> snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType:
        """Emoji which should appear on this button."""

    @property
    @abc.abstractmethod
    def label(self) -> undefined.UndefinedOr[str]:
        """Text label which should appear on this button.

        !!! note
            The text label to that should appear on this button. This may be
            up to 80 characters long.
        """

    @property
    @abc.abstractmethod
    def is_disabled(self) -> bool:
        """Whether the button should be marked as disabled."""

    @abc.abstractmethod
    def set_emoji(self, emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType, /) -> Self:
        """Set the emoji to display on this button.

        Parameters
        ----------
        emoji
            Object, ID or raw string of the emoji which should be displayed on
            this button.

        Returns
        -------
        ButtonBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_label(self, label: undefined.UndefinedOr[str], /) -> Self:
        """Set the text label which should be displayed on this button.

        Parameters
        ----------
        label
            The text label to show on this button.

            This may be up to 80 characters long.

        Returns
        -------
        ButtonBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_is_disabled(self, state: bool, /) -> Self:  # noqa: FBT001 - Boolean-typed positional argument
        """Set whether this button should be disabled.

        Parameters
        ----------
        state
            Whether this button should be disabled.

        Returns
        -------
        ButtonBuilder
            The builder object to enable chained calls.
        """


class LinkButtonBuilder(ButtonBuilder, abc.ABC):
    """Builder interface for link buttons."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def url(self) -> str:
        """URL this button should link to when pressed."""


class InteractiveButtonBuilder(ButtonBuilder, abc.ABC):
    """Builder interface for interactive buttons."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def custom_id(self) -> str:
        """Developer set custom ID used for identifying interactions with this button."""

    @abc.abstractmethod
    def set_custom_id(self, custom_id: str, /) -> Self:
        """Set the custom ID used for identifying this button.

        Parameters
        ----------
        custom_id
            Developer set custom ID used for identifying this button.

        Returns
        -------
        InteractiveButtonBuilder
            The builder object to enable chained calls.
        """


class SelectOptionBuilder(abc.ABC):
    """Builder class for select menu options."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """User-facing name of the option, max 100 characters."""

    @property
    @abc.abstractmethod
    def value(self) -> str:
        """Developer-defined value of the option, max 100 characters."""

    @property
    @abc.abstractmethod
    def description(self) -> undefined.UndefinedOr[str]:
        """Description of the option, max 100 characters."""

    @property
    @abc.abstractmethod
    def emoji(self) -> snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType:
        """Emoji which should appear on this option."""

    @property
    @abc.abstractmethod
    def is_default(self) -> bool:
        """Whether this option should be marked as selected by default."""

    @abc.abstractmethod
    def set_label(self, label: str, /) -> Self:
        """Set the option's label.

        Parameters
        ----------
        label
            Label to set for this option. This can be up to 100 characters
            long.

        Returns
        -------
        SelectOptionBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_value(self, value: str, /) -> Self:
        """Set the option's value.

        Parameters
        ----------
        value
            Value to set for this option. This can be up to 100 characters
            long.

        Returns
        -------
        SelectOptionBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_description(self, value: undefined.UndefinedOr[str], /) -> Self:
        """Set the option's description.

        Parameters
        ----------
        value
            Description to set for this option. This can be up to 100 characters
            long.

        Returns
        -------
        SelectOptionBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_emoji(self, emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType, /) -> Self:
        """Set the emoji to display on this option.

        Parameters
        ----------
        emoji
            Object, ID or raw string of the emoji which should be displayed on
            this option.

        Returns
        -------
        SelectOptionBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_is_default(self, state: bool, /) -> Self:  # noqa: FBT001 - Boolean-typed positional argument
        """Set whether this option should be selected by default.

        Parameters
        ----------
        state
            Whether this option should be selected by default.

        Returns
        -------
        SelectOptionBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        """Build a JSON object from this builder.

        Returns
        -------
        typing.MutableMapping[str, typing.Any]
            The built json object representation of this builder.
        """


class SelectMenuBuilder(ComponentBuilder, abc.ABC):
    """Builder class for a select menu."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def custom_id(self) -> str:
        """Developer set custom ID used for identifying interactions with this menu."""

    @property
    @abc.abstractmethod
    def is_disabled(self) -> bool:
        """Whether the select menu should be marked as disabled."""

    @property
    @abc.abstractmethod
    def placeholder(self) -> undefined.UndefinedOr[str]:
        """Placeholder text to display when no options are selected."""

    @property
    @abc.abstractmethod
    def min_values(self) -> int:
        """Minimum number of options which must be chosen.

        Defaults to 1.
        Must be less than or equal to [`hikari.api.special_endpoints.SelectMenuBuilder.max_values`][] and greater
        than or equal to 0.
        """

    @property
    @abc.abstractmethod
    def max_values(self) -> int:
        """Maximum number of options which can be chosen.

        Defaults to 1.
        Must be greater than or equal to [`hikari.api.special_endpoints.SelectMenuBuilder.min_values`][] and
        less than or equal to 25.
        """

    @abc.abstractmethod
    def set_custom_id(self, custom_id: str, /) -> Self:
        """Set the custom ID used for identifying this menu.

        Parameters
        ----------
        custom_id
            Developer set custom ID used for identifying this menu.

        Returns
        -------
        SelectMenuBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_is_disabled(self, state: bool, /) -> Self:  # noqa: FBT001 - Boolean-typed positional argument
        """Set whether this option is disabled.

        Parameters
        ----------
        state
            Whether this option is disabled.

        Returns
        -------
        SelectMenuBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_placeholder(self, value: undefined.UndefinedOr[str], /) -> Self:
        """Set place-holder text to be shown when no option is selected.

        Parameters
        ----------
        value
            Place-holder text to be displayed when no option is selected.
            Max 100 characters.

        Returns
        -------
        SelectMenuBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_min_values(self, value: int, /) -> Self:
        """Set the minimum amount of options which need to be selected for this menu.

        !!! note
            This defaults to 1 if not set and must be greater than or equal to 0
            and less than or equal to [`hikari.api.special_endpoints.SelectMenuBuilder.max_values`][].

        Parameters
        ----------
        value
            The minimum amount of options which need to be selected for this menu.

        Returns
        -------
        SelectMenuBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_max_values(self, value: int, /) -> Self:
        """Set the maximum amount of options which can be selected for this menu.

        !!! note
            This defaults to 1 if not set and must be less than or equal to 25
            and greater than or equal to [`hikari.api.special_endpoints.SelectMenuBuilder.min_values`][].

        Parameters
        ----------
        value
            The maximum amount of options which can selected for this menu.

        Returns
        -------
        SelectMenuBuilder
            The builder object to enable chained calls.
        """


class TextSelectMenuBuilder(SelectMenuBuilder, abc.ABC, typing.Generic[_ParentT]):
    """Builder class for a text select menu."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def parent(self) -> _ParentT:
        """Parent object which initialised this builder."""

    @property
    @abc.abstractmethod
    def options(self) -> typing.Sequence[SelectOptionBuilder]:
        """Sequence of the options set for this select menu."""

    @abc.abstractmethod
    def add_option(
        self,
        label: str,
        value: str,
        /,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = undefined.UNDEFINED,
        is_default: bool = False,
    ) -> Self:
        """Add an option to this menu.

        Parameters
        ----------
        label
            The user-facing name of this option, max 100 characters.
        value
            The developer defined value of this option, max 100 characters.
        description
            The option's description.

            This can be up to 100 characters long.
        emoji
            The option's display emoji.
        is_default
            Whether this option should be selected by default.

        Returns
        -------
        TextSelectMenuBuilder
            The select menu builder to enable call chaining.
        """


class ChannelSelectMenuBuilder(SelectMenuBuilder, abc.ABC):
    """Builder class for a channel select menu."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def channel_types(self) -> typing.Sequence[channels.ChannelType]:
        """The channel types that can be selected in this menu."""

    @abc.abstractmethod
    def set_channel_types(self, value: typing.Sequence[channels.ChannelType], /) -> Self:
        """Set the valid channel types for this menu.

        Parameters
        ----------
        value
            The valid channel types for this menu.

        Returns
        -------
        SelectMenuBuilder
            The builder object to enable chained calls.
        """


class TextInputBuilder(ComponentBuilder, abc.ABC):
    """Builder class for text inputs components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.TEXT_INPUT]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def custom_id(self) -> str:
        """Developer set custom ID used for identifying this text input.

        !!! note
            This custom_id is never used in component interaction events.
            It is meant to be used purely for resolving components modal interactions.
        """

    @property
    @abc.abstractmethod
    def label(self) -> str:
        """Label above this text input."""

    @property
    @abc.abstractmethod
    def style(self) -> components_.TextInputStyle:
        """Style to use for the text input."""

    @property
    @abc.abstractmethod
    def placeholder(self) -> undefined.UndefinedOr[str]:
        """Placeholder text for when the text input is empty."""

    @property
    @abc.abstractmethod
    def value(self) -> undefined.UndefinedOr[str]:
        """Pre-filled text that will be sent if the user does not write anything."""

    @property
    @abc.abstractmethod
    def is_required(self) -> bool:
        """Whether this text input is required to be filled-in."""

    @property
    @abc.abstractmethod
    def min_length(self) -> int:
        """Minimum length the text should have."""

    @property
    @abc.abstractmethod
    def max_length(self) -> int:
        """Maximum length the text should have."""

    @abc.abstractmethod
    def set_style(self, style: components_.TextInputStyle | int, /) -> Self:
        """Set the style to use for the text input.

        Parameters
        ----------
        style
            Style to use for the text input.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_custom_id(self, custom_id: str, /) -> Self:
        """Set the custom ID used for identifying this text input.

        Parameters
        ----------
        custom_id
            Developer set custom ID used for identifying this text input.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_label(self, label: str, /) -> Self:
        """Set the label above this text input.

        Parameters
        ----------
        label
            Label above this text input.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_placeholder(self, placeholder: undefined.UndefinedOr[str], /) -> Self:
        """Set the placeholder text for when the text input is empty.

        Parameters
        ----------
        placeholder
            Placeholder text that will disappear when the user types anything.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_value(self, value: undefined.UndefinedOr[str], /) -> Self:
        """Pre-filled text that will be sent if the user does not write anything.

        Parameters
        ----------
        value
            Pre-filled text that will be sent if the user does not write anything.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_required(self, required: bool, /) -> Self:  # noqa: FBT001 - Boolean-typed positional argument
        """Set whether this text input is required to be filled-in.

        Parameters
        ----------
        required
            Whether this text input is required to be filled-in.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_min_length(self, min_length: int, /) -> Self:
        """Set the minimum length the text should have.

        Parameters
        ----------
        min_length
            The minimum length the text should have.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def set_max_length(self, max_length: int, /) -> Self:
        """Set the maximum length the text should have.

        Parameters
        ----------
        max_length
            The maximum length the text should have.

        Returns
        -------
        TextInputBuilder
            The builder object to enable chained calls.
        """


class MessageActionRowBuilder(ComponentBuilder, abc.ABC):
    """Builder class for action row components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.ACTION_ROW]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def components(self) -> typing.Sequence[MessageActionRowBuilderComponentsT]:
        """Sequence of the component builders registered within this action row."""

    @abc.abstractmethod
    def add_component(self, component: MessageActionRowBuilderComponentsT, /) -> Self:
        """Add a component to this action row builder.

        !!! warning
            It is generally better to use
            [`hikari.api.special_endpoints.MessageActionRowBuilder.add_interactive_button`][]
            and [`hikari.api.special_endpoints.MessageActionRowBuilder.add_select_menu`][]
            to add your component to the builder. Those methods utilize this one.

        Parameters
        ----------
        component
            The component builder to add to the action row.

        Returns
        -------
        ActionRowBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_interactive_button(
        self,
        style: components_.InteractiveButtonTypesT,
        custom_id: str,
        /,
        *,
        emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = undefined.UNDEFINED,
        label: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        is_disabled: bool = False,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        """Add an interactive button component to this action row builder.

        Either `emoji` or `label` (exclusively) must be provided to be the button's
        displayed label.

        Parameters
        ----------
        style
            The button's style.
        custom_id
            The developer-defined custom identifier used to identify which button
            triggered component interactions.
        emoji
            The button's display emoji.
        label
            The button's display label.
        is_disabled
            Whether the button should be marked as disabled.
        id
            The ID to give to the button.

            If not provided, auto populated through increment.

        Returns
        -------
        ActionRowBuilder
            The action row builder to enable chained calls.
        """

    @abc.abstractmethod
    def add_link_button(
        self,
        url: str,
        /,
        *,
        emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = undefined.UNDEFINED,
        label: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        is_disabled: bool = False,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        """Add a link button component to this action row builder.

        Either `emoji` or `label` (exclusively) must be provided to be the button's
        displayed label.

        Parameters
        ----------
        url
            The URL the link button should redirect to.
        emoji
            The button's display emoji.
        label
            The button's display label.
        is_disabled
            Whether the button should be marked as disabled.
        id
            The ID to give to the button.

            If not provided, auto populated through increment.

        Returns
        -------
        ActionRowBuilder
            The action row builder to enable chained calls.
        """

    @abc.abstractmethod
    def add_select_menu(
        self,
        type_: components_.ComponentType | int,
        custom_id: str,
        /,
        *,
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        """Add a select menu component to this action row builder.

        For channel select menus and text select menus see
        [`hikari.api.special_endpoints.MessageActionRowBuilder.add_channel_menu`][]
        and [`hikari.api.special_endpoints.MessageActionRowBuilder.add_text_menu`][].

        Parameters
        ----------
        type_
            The type for the select menu.
        custom_id
            A developer-defined custom identifier used to identify which menu
            triggered component interactions.
        placeholder
            Placeholder text to show when no entries have been selected.
        min_values
            The minimum amount of entries which need to be selected.
        max_values
            The maximum amount of entries which can be selected.
        is_disabled
            Whether this select menu should be marked as disabled.
        id
            The ID to give to the menu.

            If not provided, auto populated through increment.

        Returns
        -------
        ActionRowBuilder
            The action row builder to enable chained calls.

        Raises
        ------
        ValueError
            If an invalid select menu type is passed.
        """

    @abc.abstractmethod
    def add_channel_menu(
        self,
        custom_id: str,
        /,
        *,
        channel_types: typing.Sequence[channels.ChannelType] = (),
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        """Add a channel select menu component to this action row builder.

        Parameters
        ----------
        custom_id
            A developer-defined custom identifier used to identify which menu
            triggered component interactions.
        channel_types
            The channel types this select menu should allow.

            If left as an empty sequence then there will be no
            channel type restriction.
        placeholder
            Placeholder text to show when no entries have been selected.
        min_values
            The minimum amount of entries which need to be selected.
        max_values
            The maximum amount of entries which can be selected.
        is_disabled
            Whether this select menu should be marked as disabled.
        id
            The ID to give to the menu.

            If not provided, auto populated through increment.

        Returns
        -------
        ActionRowBuilder
            The action row builder to enable chained calls.

        Raises
        ------
        ValueError
            If an invalid select menu type is passed.
        """

    @abc.abstractmethod
    def add_text_menu(
        self,
        custom_id: str,
        /,
        *,
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> TextSelectMenuBuilder[Self]:
        """Add a select menu component to this action row builder.

        Parameters
        ----------
        custom_id
            A developer-defined custom identifier used to identify which menu
            triggered component interactions.
        placeholder
            Placeholder text to show when no entries have been selected.
        min_values
            The minimum amount of entries which need to be selected.
        max_values
            The maximum amount of entries which can be selected.
        is_disabled
            Whether this select menu should be marked as disabled.
        id
            The ID to give to the menu.

            If not provided, auto populated through increment.

        Returns
        -------
        TextSelectMenuBuilder
            The text select menu builder.

            [`hikari.api.special_endpoints.TextSelectMenuBuilder.add_option`][] should be called to add
            options to the returned builder then
            [`hikari.api.special_endpoints.TextSelectMenuBuilder.parent`][] can be used to return to this
            action row while chaining calls.

        Raises
        ------
        ValueError
            If an invalid select menu type is passed.
        """


class ModalActionRowBuilder(ComponentBuilder, abc.ABC):
    """Builder class for modal action row components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.ACTION_ROW]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def components(self) -> typing.Sequence[ModalActionRowBuilderComponentsT]:
        """Sequence of the component builders registered within this action row."""

    @abc.abstractmethod
    def add_component(self, component: ModalActionRowBuilderComponentsT, /) -> Self:
        """Add a component to this action row builder.

        !!! warning
            It is generally better to use
            [`hikari.api.special_endpoints.MessageActionRowBuilder.add_interactive_button`][]
            and [`hikari.api.special_endpoints.MessageActionRowBuilder.add_select_menu`][]
            to add your component to the builder. Those methods utilize this one.

        Parameters
        ----------
        component
            The component builder to add to the action row.

        Returns
        -------
        ActionRowBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_text_input(
        self,
        custom_id: str,
        label: str,
        /,
        *,
        style: components_.TextInputStyle = components_.TextInputStyle.SHORT,
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        value: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        required: bool = True,
        min_length: int = 0,
        max_length: int = 4000,
    ) -> Self:
        """Add a text input component to this action row builder.

        Parameters
        ----------
        custom_id
            Developer set custom ID used for identifying this text input.
        label
            Label above this text input.
        style
            The text input's style.
        placeholder
            Placeholder text to display when the text input is empty.
        value
            Default text to pre-fill the field with.
        required
            Whether text must be supplied for this text input.
        min_length
            Minimum length the input text can be.

            This can be greater than or equal to 0 and less than or equal to 4000.
        max_length
            Maximum length the input text can be.

            This can be greater than or equal to 1 and less than or equal to 4000.

        Returns
        -------
        ModalActionRowBuilder
            The modal action row builder to enable call chaining.
        """


class SectionComponentBuilder(ComponentBuilder, abc.ABC):
    """Builder class for section components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.SECTION]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def components(self) -> typing.Sequence[SectionBuilderComponentsT]:
        """The components attached to the section."""

    @property
    @abc.abstractmethod
    def accessory(self) -> SectionBuilderAccessoriesT:
        """The accessory attached to the section."""

    @abc.abstractmethod
    def add_component(self, component: SectionBuilderComponentsT) -> Self:
        """Add a component to this section builder.

        !!! warning
            It is generally better to use
            [`hikari.api.special_endpoints.MessageSectionBuilder.add_text_display`][]
            to add your component to the builder. Those methods utilize this one.

        Parameters
        ----------
        component
            The component builder to add to the section.

        Returns
        -------
        SectionComponentBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_text_display(self, content: str, *, id: undefined.UndefinedOr[int] = undefined.UNDEFINED) -> Self:
        """Add a text display component to this section builder.

        Parameters
        ----------
        content
            The content for the text display.
        id
            The ID to give to the text display.

            If not provided, auto populated through increment.

        Returns
        -------
        SectionComponentBuilder
            The builder object to enable chained calls.
        """


class TextDisplayComponentBuilder(ComponentBuilder, abc.ABC):
    """Builder class for text display components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.TEXT_DISPLAY]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def content(self) -> str:
        """The content for the text display."""


class ThumbnailComponentBuilder(ComponentBuilder, abc.ABC):
    """Builder class for thumbnail components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.THUMBNAIL]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def media(self) -> files.Resourceish:
        """The media of this thumbnail."""

    @property
    @abc.abstractmethod
    def description(self) -> undefined.UndefinedOr[str]:
        """The description for the thumbnails media."""

    @property
    @abc.abstractmethod
    def is_spoiler(self) -> bool:
        """Whether the media is marked as a spoiler."""


class MediaGalleryComponentBuilder(ComponentBuilder, abc.ABC):
    """Builder class for media gallery components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.MEDIA_GALLERY]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def items(self) -> typing.Sequence[MediaGalleryItemBuilder]:
        """The items in the media gallery."""

    @abc.abstractmethod
    def add_item(self, item: MediaGalleryItemBuilder) -> Self:
        """Add a component to this media gallery builder.

        !!! warning
            It is generally better to use
            [`hikari.api.special_endpoints.MessageMediaGalleryBuilder.add_media_gallery_item`][]
            to add your component to the builder. Those methods utilize this one.

        Parameters
        ----------
        item
            The media gallery item builder to add to the section.

        Returns
        -------
        MediaGalleryComponentBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_media_gallery_item(
        self,
        media: files.Resourceish,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        spoiler: bool = False,
    ) -> Self:
        """Add a media gallery item component to this media gallery builder.

        Parameters
        ----------
        media
            The media for the gallery item.
        description
            The description for the media gallery item.
        spoiler
            Whether the media has a spoiler.

        Returns
        -------
        MediaGalleryComponentBuilder
            The builder object to enable chained calls.
        """


class MediaGalleryItemBuilder(abc.ABC):
    """Builder class for a media gallery item."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def media(self) -> files.Resourceish:
        """The media for the gallery item."""

    @property
    @abc.abstractmethod
    def description(self) -> undefined.UndefinedOr[str]:
        """The description for the media gallery item."""

    @property
    @abc.abstractmethod
    def is_spoiler(self) -> bool:
        """Whether the media is marked as a spoiler."""

    @abc.abstractmethod
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        """Build a JSON object from this builder and collects all attachments added as components.

        Returns
        -------
        tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]
            The built json object representation of this builder, and the attachments added.
        """


class SeparatorComponentBuilder(ComponentBuilder, abc.ABC):
    """Builder class for separator components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.SEPARATOR]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def spacing(self) -> undefined.UndefinedOr[components_.SpacingType]:
        """The spacing for the separator."""

    @property
    @abc.abstractmethod
    def divider(self) -> undefined.UndefinedOr[bool]:
        """Whether the separator has a divider."""


class FileComponentBuilder(ComponentBuilder, abc.ABC):
    """Builder class for file components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.FILE]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def file(self) -> files.Resourceish:
        """The file to attach."""

    @property
    @abc.abstractmethod
    def is_spoiler(self) -> bool:
        """Whether the file has a spoiler."""


class ContainerComponentBuilder(ComponentBuilder, abc.ABC):
    """Builder class for container components."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[components_.ComponentType.CONTAINER]:
        """Type of component this builder represents."""

    @property
    @abc.abstractmethod
    def accent_color(self) -> undefined.UndefinedOr[colors.Color]:
        """The accent color for the container.

        If undefined, the accent colour is hidden, if None, then no colour is set.
        """

    @property
    @abc.abstractmethod
    def is_spoiler(self) -> bool:
        """Whether the container has a spoiler."""

    @property
    @abc.abstractmethod
    def components(self) -> typing.Sequence[ContainerBuilderComponentsT]:
        """The components attached to the container."""

    @abc.abstractmethod
    def add_component(self, component: ContainerBuilderComponentsT) -> Self:
        """Add a component to this container builder.

        !!! warning
            It is generally better to use
            [`hikari.api.special_endpoints.MessageContainerBuilder.add_action_row`][]
            and [`hikari.api.special_endpoints.MessageContainerBuilder.add_text_display`][]
            and [`hikari.api.special_endpoints.MessageContainerBuilder.add_media_gallery`][]
            and [`hikari.api.special_endpoints.MessageContainerBuilder.add_separator`][]
            and [`hikari.api.special_endpoints.MessageContainerBuilder.add_file`][]
            to add your component to the builder. Those methods utilize this one.

        Parameters
        ----------
        component
            The component builder to add to the container.

        Returns
        -------
        ContainerComponentBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_action_row(
        self,
        components: typing.Sequence[MessageActionRowBuilderComponentsT],
        *,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        """Add a action row component to this container builder.

        Parameters
        ----------
        components
            The components to add to the action row.
        id
            The ID to give to the action row.

            If not provided, auto populated through increment.

        Returns
        -------
        ContainerComponentBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_text_display(self, content: str, *, id: undefined.UndefinedOr[int] = undefined.UNDEFINED) -> Self:
        """Add a text display component to this container builder.

        Parameters
        ----------
        content
            The content of the text display.
        id
            The ID to give to the text display.

            If not provided, auto populated through increment.

        Returns
        -------
        ContainerComponentBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_media_gallery(
        self, items: typing.Sequence[MediaGalleryItemBuilder], *, id: undefined.UndefinedOr[int] = undefined.UNDEFINED
    ) -> Self:
        """Add a media gallery component to this container builder.

        Parameters
        ----------
        items
            The gallery media items to add to the media gallery.
        id
            The ID to give to the media gallery.

            If not provided, auto populated through increment.

        Returns
        -------
        ContainerComponentBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def add_separator(
        self,
        *,
        spacing: components_.SpacingType = components_.SpacingType.SMALL,
        divider: bool = False,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        """Add a separator component to this container builder.

        Parameters
        ----------
        spacing
            The spacing for the separator.
        divider
            Whether the separator has a divider.
        id
            The ID to give to the separator.

            If not provided, auto populated through increment.

        Returns
        -------
        ContainerComponentBuilder
        """

    @abc.abstractmethod
    def add_file(
        self, file: files.Resourceish, *, spoiler: bool = False, id: undefined.UndefinedOr[int] = undefined.UNDEFINED
    ) -> Self:
        """Add a spoiler component to this container builder.

        Parameters
        ----------
        file
            The file.
        spoiler
            Whether the file has a spoiler.
        id
            The ID to give to the file.
            If not provided, auto populated through increment.

        Returns
        -------
        ContainerComponentBuilder
            The builder object to enable chained calls.
        """


class PollBuilder(abc.ABC):
    """Builder class for polls."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def question_text(self) -> str:
        """The question text for the poll."""

    @property
    @abc.abstractmethod
    def answers(self) -> typing.Sequence[PollAnswerBuilder]:
        """The answers for the poll."""

    @property
    @abc.abstractmethod
    def duration(self) -> undefined.UndefinedOr[int]:
        """The duration of the poll in hours."""

    @property
    @abc.abstractmethod
    def allow_multiselect(self) -> bool:
        """Whether a user can select multiple answers."""

    @property
    @abc.abstractmethod
    def layout_type(self) -> undefined.UndefinedOr[polls.PollLayoutType]:
        """The layout type for the poll."""

    @abc.abstractmethod
    def add_answer(
        self,
        *,
        text: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        emoji: undefined.UndefinedOr[emojis.Emoji] = undefined.UNDEFINED,
    ) -> Self:
        """Add an answer to the poll.

        Parameters
        ----------
        text
            The text for the answer.
        emoji
            The emoji for the answer.

        Returns
        -------
        PollAnswerBuilder
            The builder object to enable chained calls.
        """

    @abc.abstractmethod
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        """Build a JSON object from this builder.

        Returns
        -------
        typing.MutableMapping[str, typing.Any]
            The built json object representation of this builder.
        """


class PollAnswerBuilder(abc.ABC):
    """Builder class for poll answers."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def text(self) -> undefined.UndefinedOr[str]:
        """The text for the media object."""

    @property
    @abc.abstractmethod
    def emoji(self) -> undefined.UndefinedOr[emojis.Emoji]:
        """The emoji for the media object."""

    @abc.abstractmethod
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        """Build a JSON object from this builder.

        Returns
        -------
        typing.MutableMapping[str, typing.Any]
            The built json object representation of this builder.
        """


if typing.TYPE_CHECKING:
    MessageActionRowBuilderComponentsT = typing.Union[ButtonBuilder, SelectMenuBuilder]

    ModalActionRowBuilderComponentsT = TextInputBuilder

    ContainerBuilderComponentsT = typing.Union[
        MessageActionRowBuilder,
        TextDisplayComponentBuilder,
        SectionComponentBuilder,
        MediaGalleryComponentBuilder,
        SeparatorComponentBuilder,
        FileComponentBuilder,
    ]

    SectionBuilderAccessoriesT = typing.Union[ButtonBuilder, ThumbnailComponentBuilder]
    SectionBuilderComponentsT = typing.Union[TextDisplayComponentBuilder]


class AutoModActionBuilder(abc.ABC):
    """Builder class for auto mod actions."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def type(self) -> auto_mod.AutoModActionType:
        """Type of action this builder represents."""

    @abc.abstractmethod
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        """Build a JSON object from this builder.

        Returns
        -------
        typing.MutableMapping[str, typing.Any]
            The built json object representation of this builder.
        """


class AutoModBlockMessageActionBuilder(AutoModActionBuilder, abc.ABC):
    """Builder class for auto mod block message action."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.BLOCK_MESSAGE]: ...

    @property
    @abc.abstractmethod
    def custom_message(self) -> str | None:
        """The custom message sent when a message is blocked."""


class AutoModSendAlertMessageActionBuilder(AutoModActionBuilder, abc.ABC):
    """Builder class for auto mod send alert message action."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.SEND_ALERT_MESSAGE]: ...

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """The channel to send the alert message to."""


class AutoModTimeoutActionBuilder(AutoModActionBuilder, abc.ABC):
    """Builder class for auto mod duration seconds action."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.TIMEOUT]: ...

    @property
    @abc.abstractmethod
    def duration_seconds(self) -> int:
        """The amount of seconds to time the user out for."""


class AutoModBlockMemberInteractionActionBuilder(AutoModActionBuilder, abc.ABC):
    """Builder class for auto mod block member interaction action."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.BLOCK_MEMBER_INTERACTION]: ...


class AutoModTriggerBuilder(abc.ABC):
    """Builder class for auto mod triggers."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def type(self) -> auto_mod.AutoModTriggerType:
        """Type of trigger this builder represents."""

    @abc.abstractmethod
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        """Build a JSON object from this builder.

        Returns
        -------
        typing.MutableMapping[str, typing.Any]
            The built json object representation of this builder.
        """


class AutoModKeywordTriggerBuilder(AutoModTriggerBuilder, abc.ABC):
    """Builder class for auto mod keyword trigger."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.KEYWORD]: ...

    @property
    @abc.abstractmethod
    def keyword_filter(self) -> typing.Sequence[str]:
        """The filter strings this trigger checks for.

        This supports a wildcard matching strategy which is documented at
        <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies>.
        """

    @property
    @abc.abstractmethod
    def regex_patterns(self) -> typing.Sequence[str]:
        """The filter regexs this trigger checks for.

        Currently, this only supports rust flavored regular expressions.
        <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-trigger-metadata>
        """

    @property
    @abc.abstractmethod
    def allow_list(self) -> typing.Sequence[str]:
        """A sequence of filters which will be exempt from triggering the preset trigger.

        This supports a wildcard matching strategy which is documented at
        <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies>.
        """


class AutoModSpamTriggerBuilder(AutoModTriggerBuilder, abc.ABC):
    """Builder class for auto mod spam trigger."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.SPAM]: ...


class AutoModKeywordPresetTriggerBuilder(AutoModTriggerBuilder, abc.ABC):
    """Builder class for auto mod keyword preset trigger."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.KEYWORD_PRESET]: ...

    @property
    @abc.abstractmethod
    def presets(self) -> typing.Sequence[auto_mod.AutoModKeywordPresetType]:
        """The predefined presets provided by Discord to match against."""

    @property
    @abc.abstractmethod
    def allow_list(self) -> typing.Sequence[str]:
        """A sequence of filters which will be exempt from triggering the preset trigger.

        This supports a wildcard matching strategy which is documented at
        <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies>.
        """


class AutoModMentionSpamTriggerBuilder(AutoModTriggerBuilder, abc.ABC):
    """Builder class for auto mod mention spam trigger."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.MENTION_SPAM]: ...

    @property
    @abc.abstractmethod
    def mention_total_limit(self) -> int:
        """Total number of unique role and user mentions allowed per message."""

    @property
    @abc.abstractmethod
    def mention_raid_protection_enabled(self) -> bool:
        """Whether to automatically detect mention raids."""


class AutoModMemberProfileTriggerBuilder(AutoModTriggerBuilder, abc.ABC):
    """Builder class for auto mod member profile trigger."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.MEMBER_PROFILE]: ...

    @property
    @abc.abstractmethod
    def keyword_filter(self) -> typing.Sequence[str]:
        """The filter strings this trigger checks for.

        This supports a wildcard matching strategy which is documented at
        <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies>.
        """

    @property
    @abc.abstractmethod
    def regex_patterns(self) -> typing.Sequence[str]:
        """The filter regexs this trigger checks for.

        Currently, this only supports rust flavored regular expressions.
        <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-trigger-metadata>.
        """

    @property
    @abc.abstractmethod
    def allow_list(self) -> typing.Sequence[str]:
        """A sequence of filters which will be exempt from triggering the preset trigger.

        This supports a wildcard matching strategy which is documented at
        <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies>.
        """
