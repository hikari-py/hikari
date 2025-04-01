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
"""Models and enums used for Discord's Slash Commands interaction flow."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "COMMAND_RESPONSE_TYPES",
    "AutocompleteInteraction",
    "AutocompleteInteractionOption",
    "BaseCommandInteraction",
    "CommandInteraction",
    "CommandInteractionMetadata",
    "CommandInteractionOption",
    "CommandResponseTypesT",
)

import typing

import attrs

from hikari import commands
from hikari import snowflakes
from hikari import undefined
from hikari.interactions import base_interactions
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from typing_extensions import Self

    from hikari import permissions as permissions_
    from hikari import users as users_
    from hikari.api import special_endpoints


COMMAND_RESPONSE_TYPES: typing.Final[typing.AbstractSet[CommandResponseTypesT]] = frozenset(
    [base_interactions.ResponseType.MESSAGE_CREATE, base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE]
)
"""Set of the response types which are valid for a command interaction.

This includes:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]
"""

CommandResponseTypesT = typing.Literal[
    base_interactions.ResponseType.MESSAGE_CREATE, 4, base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE, 5
]
"""Type-hint of the response types which are valid for a command interaction.

The following types are valid for this:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]/`4`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]/`5`
"""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class CommandInteractionOption:
    """Represents the options passed for a command interaction."""

    name: str = attrs.field(repr=True)
    """Name of this option."""

    type: commands.OptionType | int = attrs.field(repr=True)
    """Type of this option."""

    value: snowflakes.Snowflake | str | int | float | bool | None = attrs.field(repr=True)
    """Value provided for this option.

    Either [`hikari.interactions.command_interactions.CommandInteractionOption.value`][]
    or [`hikari.interactions.command_interactions.CommandInteractionOption.options`][]
    will be provided with `value` being provided when an option is provided as a
    parameter with a value and `options` being provided when an option donates a
    subcommand or group.
    """

    options: typing.Sequence[Self] | None = attrs.field(repr=True)
    """Options provided for this option.

    Either [`hikari.interactions.command_interactions.CommandInteractionOption.value`][]
    or [`hikari.interactions.command_interactions.CommandInteractionOption.options`][]
    will be provided with `value` being provided when an option is provided as a
    parameter with a value and `options` being provided when an option donates a
    subcommand or group.
    """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class AutocompleteInteractionOption(CommandInteractionOption):
    """Represents the options passed for a command autocomplete interaction."""

    is_focused: bool = attrs.field(default=False, repr=True)
    """Whether this option is the currently focused option for autocomplete.

    Focused options are not guaranteed to be parsed so the value may be a string
    even if the option type says otherwise.
    """


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class BaseCommandInteraction(base_interactions.PartialInteraction):
    """Represents a base command interaction on Discord.

    May be a command interaction or an autocomplete interaction.
    """

    command_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the command being invoked."""

    command_name: str = attrs.field(eq=False, hash=False, repr=True)
    """Name of the command being invoked."""

    command_type: commands.CommandType | int = attrs.field(eq=False, hash=False, repr=True)
    """The type of the command."""

    registered_guild_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """ID of the guild the command is registered to."""

    async def fetch_command(self) -> commands.PartialCommand:
        """Fetch the command which triggered this interaction.

        Returns
        -------
        hikari.commands.PartialCommand
            Object of this interaction's command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the target command.
        hikari.errors.NotFoundError
            If the command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_application_command(
            application=self.application_id, command=self.id, guild=self.guild_id or undefined.UNDEFINED
        )


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class CommandInteraction(
    BaseCommandInteraction,
    base_interactions.MessageResponseMixin[CommandResponseTypesT],
    base_interactions.ModalResponseMixin,
    base_interactions.PremiumResponseMixin,
):
    """Represents a command interaction on Discord."""

    app_permissions: permissions_.Permissions = attrs.field(eq=False, hash=False, repr=False)
    """Permissions the bot has in this interaction's channel."""

    options: typing.Sequence[CommandInteractionOption] = attrs.field(eq=False, hash=False, repr=True)
    """Parameter values provided by the user invoking this command."""

    resolved: base_interactions.ResolvedOptionData | None = attrs.field(eq=False, hash=False, repr=False)
    """Mappings of the objects resolved for the provided command options."""

    target_id: snowflakes.Snowflake | None = attrs.field(default=None, eq=False, hash=False, repr=True)
    """The target of the command. Only available if the command is a context menu command."""

    def build_response(self) -> special_endpoints.InteractionMessageBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            [`hikari.interactions.command_interactions.CommandInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        Examples
        --------
        ```py
        async def handle_command_interaction(
            interaction: CommandInteraction,
        ) -> InteractionMessageBuilder:
            return (
                interaction.build_response()
                .add_embed(Embed(description="Hi there"))
                .set_content("Konnichiwa")
            )
        ```

        Returns
        -------
        hikari.api.special_endpoints.InteractionMessageBuilder
            Interaction message response builder object.
        """
        return self.app.rest.interaction_message_builder(base_interactions.ResponseType.MESSAGE_CREATE)

    def build_deferred_response(self) -> special_endpoints.InteractionDeferredBuilder:
        """Get a deferred message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            [`hikari.interactions.command_interactions.CommandInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        !!! note
            Unlike [`hikari.api.special_endpoints.InteractionMessageBuilder`][],
            the result of this call can be returned as is without any modifications
            being made to it.

        Examples
        --------
        ```py
        async def handle_command_interaction(
            interaction: CommandInteraction,
        ) -> InteractionMessageBuilder:
            yield interaction.build_deferred_response()

            await interaction.edit_initial_response("Pong!")
        ```

        Returns
        -------
        hikari.api.special_endpoints.InteractionMessageBuilder
            Deferred interaction message response builder object.
        """
        return self.app.rest.interaction_deferred_builder(base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE)


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class AutocompleteInteraction(BaseCommandInteraction):
    """Represents an autocomplete interaction on Discord."""

    options: typing.Sequence[AutocompleteInteractionOption] = attrs.field(eq=False, hash=False, repr=True)
    """Parameter values provided by the user invoking this command."""

    def build_response(
        self, choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder]
    ) -> special_endpoints.InteractionAutocompleteBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            [`hikari.interactions.command_interactions.AutocompleteInteraction.create_response`][]
            should be used to set the interaction response.

        Parameters
        ----------
        choices
            The choices for the autocomplete.

        Examples
        --------
        ```py
        async def handle_autocomplete_interaction(
            interaction: AutocompleteInteraction,
        ) -> InteractionAutocompleteBuilder:
            return interaction.build_response(
                [
                    AutocompleteChoiceBuilder(name="foo", value="a"),
                    AutocompleteChoiceBuilder(name="bar", value="b"),
                    AutocompleteChoiceBuilder(name="baz", value="c"),
                ]
            )
        ```

        Returns
        -------
        hikari.api.special_endpoints.InteractionAutocompleteBuilder
            Interaction autocomplete response builder object.
        """
        return self.app.rest.interaction_autocomplete_builder(choices)

    async def create_response(self, choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder]) -> None:
        """Create a response for this autocomplete interaction.

        Parameters
        ----------
        choices
            The choices for the autocomplete.
        """
        await self.app.rest.create_autocomplete_response(self.id, self.token, choices)


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class CommandInteractionMetadata(base_interactions.PartialInteractionMetadata):
    """The interaction metadata for a command initiated message."""

    target_user: users_.User | None = attrs.field(eq=False, hash=False, repr=True)
    """The user the command was run on, present only on user command interactions."""

    target_message_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the message the command was run on, present only on message command interactions."""
