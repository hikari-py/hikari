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
"""Models and enums used for Discord's Components interaction flow."""
from __future__ import annotations

__all__: typing.Sequence[str] = [
    "ActionRowComponent",
    "ButtonComponent",
    "ButtonStyle",
    "ComponentInteraction",
    "COMPONENT_RESPONSE_TYPES",
    "ComponentResponseTypesT",
    "ComponentType",
    "PartialComponent",
]

import typing

import attr

from hikari import emojis
from hikari.interactions import bases
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import messages
    from hikari import snowflakes
    from hikari import users
    from hikari.api import special_endpoints


_DEFERRED_TYPES: typing.AbstractSet[_DeferredTypesT] = frozenset(
    [bases.ResponseType.DEFERRED_MESSAGE_CREATE, bases.ResponseType.DEFERRED_MESSAGE_UPDATE]
)
_DeferredTypesT = typing.Union[
    typing.Literal[bases.ResponseType.DEFERRED_MESSAGE_CREATE],
    typing.Literal[5],
    typing.Literal[bases.ResponseType.DEFERRED_MESSAGE_UPDATE],
    typing.Literal[6],
]
_IMMEDIATE_TYPES: typing.AbstractSet[_ImmediateTypesT] = frozenset(
    [bases.ResponseType.MESSAGE_CREATE, bases.ResponseType.MESSAGE_UPDATE]
)
_ImmediateTypesT = typing.Union[
    typing.Literal[bases.ResponseType.MESSAGE_CREATE],
    typing.Literal[4],
    typing.Literal[bases.ResponseType.MESSAGE_UPDATE],
    typing.Literal[7],
]


# This type ignore accounts for a regression introduced to MyPy in v0.900
COMPONENT_RESPONSE_TYPES: typing.Final[typing.AbstractSet[ComponentResponseTypesT]] = frozenset(  # type: ignore[assignment]
    [*_DEFERRED_TYPES, *_IMMEDIATE_TYPES]
)
"""Set of the response types which are valid for a component interaction.

This includes:

* `hikari.interactions.bases.ResponseType.MESSAGE_CREATE`
* `hikari.interactions.bases.ResponseType.DEFERRED_MESSAGE_CREATE`
* `hikari.interactions.bases.ResponseType.DEFERRED_MESSAGE_UPDATE`
* `hikari.interactions.bases.ResponseType.MESSAGE_UPDATE`
"""

ComponentResponseTypesT = typing.Union[_ImmediateTypesT, _DeferredTypesT]
"""Type-hint of the response types which are valid for a component interaction.

The following types are valid for this:

* `hikari.interactions.bases.ResponseType.MESSAGE_CREATE`/`4`
* `hikari.interactions.bases.ResponseType.DEFERRED_MESSAGE_CREATE`/`5`
* `hikari.interactions.bases.ResponseType.DEFERRED_MESSAGE_UPDATE`/`6`
* `hikari.interactions.bases.ResponseType.MESSAGE_UPDATE`/`7`
"""


@typing.final
class ComponentType(int, enums.Enum):
    """Types of components found within Discord."""

    ACTION_ROW = 1
    """A non-interactive container component for other types of components.

    !!! note
        As this is a container component it can never be contained within another
        component and therefore will always be top-level.l
    """

    BUTTON = 2
    """A button component.

    !!! note
        This cannot be top-level and must be within a container component such
        as `ComponentType.ACTION_ROW`.
    """


@typing.final
class ButtonStyle(int, enums.Enum):
    """Enum of the available button styles.

    More information, such as how these look, can be found at
    https://discord.com/developers/docs/interactions/message-components#buttons-button-styles
    """

    PRIMARY = 1
    """A blurple "call to action" button."""

    SECONDARY = 2
    """A grey neutral button."""

    SUCCESS = 3
    """A green button."""

    DANGER = 4
    """A red button (usually indicates a destructive action)."""

    LINK = 5
    """A grey button which navigates to a URL.

    !!! warning
        Unlike the other button styles, clicking this one will not trigger an
        interaction and custom_id shouldn't be included for this style.
    """


@attr.define(kw_only=True, weakref_slot=False)
class PartialComponent:
    """Base class for all component entities."""

    type: typing.Union[ComponentType, int] = attr.field()
    """The type of component this is."""


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class ButtonComponent(PartialComponent):
    """Represents a message button component.

    !!! note
        This is an embedded component and will only ever be found within
        top-level container components such as `ActionRowComponent`.
    """

    style: typing.Union[ButtonStyle, int] = attr.field(eq=False)
    """The button's style."""

    label: typing.Optional[str] = attr.field(eq=False)
    """Text label which appears on the button."""

    emoji: typing.Optional[emojis.Emoji] = attr.field(eq=False)
    """Custom or unicode emoji which appears on the button."""

    custom_id: typing.Optional[str] = attr.field(hash=True)
    """Developer defined identifier for this button (will be >= 100 characters).

    !!! note
        This is required for the following button styles:

        * `ButtonStyle.PRIMARY`
        * `ButtonStyle.SECONDARY`
        * `ButtonStyle.SUCCESS`
        * `ButtonStyle.DANGER`
    """

    url: typing.Optional[str] = attr.field(eq=False)
    """Url for `ButtonStyle.LINK` style buttons."""

    is_disabled: bool = attr.field(eq=False)
    """Whether the button is disabled."""


@attr.define(weakref_slot=False)
class ActionRowComponent(PartialComponent):
    """Represents a row of components attached to a message.

    !!! note
        This is a top-level container component and will never be found within
        another component.
    """

    components: typing.Sequence[PartialComponent] = attr.field()
    """Sequence of the components contained within this row."""

    @typing.overload
    def __getitem__(self, index: int, /) -> PartialComponent:
        ...

    @typing.overload
    def __getitem__(self, slice_: slice, /) -> typing.Sequence[PartialComponent]:
        ...

    def __getitem__(
        self, index_or_slice: typing.Union[int, slice], /
    ) -> typing.Union[PartialComponent, typing.Sequence[PartialComponent]]:
        return self.components[index_or_slice]

    def __iter__(self) -> typing.Iterator[PartialComponent]:
        return iter(self.components)

    def __len__(self) -> int:
        return len(self.components)


@attr.define(hash=True, weakref_slot=False)
class ComponentInteraction(bases.MessageResponseMixin[ComponentResponseTypesT]):
    """Represents a component interaction on Discord."""

    channel_id: snowflakes.Snowflake = attr.field(eq=False)
    """ID of the channel this interaction was triggered in."""

    component_type: typing.Union[ComponentType, int] = attr.field(eq=False)
    """The type of component which triggers this interaction.

    !!! note
        This will never be `ButtonStyle.LINK` as link buttons don't trigger
        interactions.
    """

    custom_id: str = attr.field(eq=False)
    """Developer defined ID of the component which triggered this interaction."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False)
    """ID of the guild this interaction was triggered in.

    This will be `builtins.None` for command interactions triggered in DMs.
    """
    message: typing.Optional[messages.Message] = attr.field(eq=False, repr=False)
    """Object of the message the components for this interaction are attached to.

    !!! note
        This will be `builtins.None` for ephemeral message component interactions.
    """

    message_id: snowflakes.Snowflake = attr.field(eq=False, repr=False)
    """ID of the message the components for this interaction are attached to."""

    message_flags: messages.MessageFlag = attr.field(eq=False, repr=False)
    """Flags of the message the components for this interaction are attached to."""

    member: typing.Optional[bases.InteractionMember] = attr.field(eq=False, hash=False, repr=True)
    """The member who triggered this interaction.

    This will be `builtins.None` for interactions triggered in DMs.

    !!! note
        This member object comes with the extra field `permissions` which
        contains the member's permissions in the current channel.
    """

    user: users.User = attr.field(eq=False, hash=False, repr=True)
    """The user who triggered this interaction."""

    def build_response(self, type_: _ImmediateTypesT, /) -> special_endpoints.InteractionMessageBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            `ComponentInteraction.create_initial_response` should be used to set
            the interaction response message.

        Parameters
        ----------
        type_ : typing.Union[builtins.int, hikari.interactions.bases.ResponseType]
            The type of immediate response this should be.

            This may be one of the following:

            * `hikari.interactions.bases.ResponseType.MESSAGE_CREATE`
            * `hikari.interactions.bases.ResponseType.MESSAGE_UPDATE`

        Examples
        --------
        ```py
        async def handle_component_interaction(interaction: ComponentInteraction) -> InteractionMessageBuilder:
            return (
                interaction
                .build_response(ResponseType.MESSAGE_UPDATE)
                .add_embed(Embed(description="Hi there"))
                .set_content("Konnichiwa")
            )
        ```

        Returns
        -------
        hikari.api.special_endpoints.InteractionMessageBuilder
            Interaction message response builder object.
        """
        if type_ not in _IMMEDIATE_TYPES:
            raise ValueError("Invalid type passed for an immediate response")

        return self.app.rest.interaction_message_builder(type_)

    def build_deferred_response(self, type_: _DeferredTypesT, /) -> special_endpoints.InteractionDeferredBuilder:
        """Get a deferred message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            `ComponentInteraction.create_initial_response` should be used to set
            the interaction response message.

        !!! note
            Unlike `hikari.api.special_endpoints.InteractionMessageBuilder`,
            the result of this call can be returned as is without any modifications
            being made to it.

        Parameters
        ----------
        type_ : typing.Union[builtins.int, hikari.interactions.bases.ResponseType]
            The type of deferred response this should be.

            This may be one of the following:

            * `hikari.interactions.bases.ResponseType.DEFERRED_MESSAGE_CREATE`
            * `hikari.interactions.bases.ResponseType.DEFERRED_MESSAGE_UPDATE`

        Returns
        -------
        hikari.api.special_endpoints.InteractionDeferredBuilder
            Deferred interaction message response builder object.
        """
        if type_ not in _DEFERRED_TYPES:
            raise ValueError("Invalid type passed for a deferred response")

        return self.app.rest.interaction_deferred_builder(type_)
