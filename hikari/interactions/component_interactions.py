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
"""Models and enums used for Discord's Components interaction flow."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "COMPONENT_RESPONSE_TYPES",
    "ComponentInteraction",
    "ComponentInteractionMetadata",
    "ComponentResponseTypesT",
)

import typing

import attrs

from hikari.interactions import base_interactions

if typing.TYPE_CHECKING:
    from hikari import components as components_
    from hikari import messages
    from hikari import snowflakes
    from hikari.api import special_endpoints


_DEFERRED_TYPES: typing.AbstractSet[_DeferredTypesT] = frozenset(
    [base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE, base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE]
)
_DeferredTypesT = typing.Literal[
    base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE, 5, base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE, 6
]
_IMMEDIATE_TYPES: typing.AbstractSet[_ImmediateTypesT] = frozenset(
    [base_interactions.ResponseType.MESSAGE_CREATE, base_interactions.ResponseType.MESSAGE_UPDATE]
)
_ImmediateTypesT = typing.Literal[
    base_interactions.ResponseType.MESSAGE_CREATE, 4, base_interactions.ResponseType.MESSAGE_UPDATE, 7
]


COMPONENT_RESPONSE_TYPES: typing.Final[typing.AbstractSet[ComponentResponseTypesT]] = frozenset(
    [*_DEFERRED_TYPES, *_IMMEDIATE_TYPES]
)
"""Set of the response types which are valid for a component interaction.

This includes:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`][]
* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`][]
"""

ComponentResponseTypesT = typing.Union[_ImmediateTypesT, _DeferredTypesT]
"""Type-hint of the response types which are valid for a component interaction.

The following types are valid for this:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]/`4`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]/`5`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`][]/`6`
* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`][]/`7`
"""


@attrs.define(unsafe_hash=True, weakref_slot=False)
class ComponentInteraction(
    base_interactions.MessageResponseMixin[ComponentResponseTypesT],
    base_interactions.ModalResponseMixin,
    base_interactions.PremiumResponseMixin,
):
    """Represents a component interaction on Discord."""

    component_type: components_.ComponentType | int = attrs.field(eq=False)
    """The type of component which triggers this interaction.

    !!! note
        This will never be [`hikari.components.ButtonStyle.LINK`][] as link buttons don't trigger
        interactions.
    """

    custom_id: str = attrs.field(eq=False)
    """Developer defined ID of the component which triggered this interaction."""

    values: typing.Sequence[str] = attrs.field(eq=False)
    """Sequence of the values which were selected for a select menu component."""

    resolved: base_interactions.ResolvedOptionData | None = attrs.field(eq=False, hash=False, repr=False)
    """Mappings of the objects resolved for the provided command options."""

    message: messages.Message = attrs.field(eq=False, repr=False)
    """Object of the message the components for this interaction are attached to."""

    def build_response(self, type_: _ImmediateTypesT, /) -> special_endpoints.InteractionMessageBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            [`hikari.interactions.component_interactions.ComponentInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        Parameters
        ----------
        type_
            The type of immediate response this should be.

            This may be one of the following:

            * [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]
            * [`hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`][]

        Examples
        --------
        ```py
        async def handle_component_interaction(
            interaction: ComponentInteraction,
        ) -> InteractionMessageBuilder:
            return (
                interaction.build_response(ResponseType.MESSAGE_UPDATE)
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
            msg = "Invalid type passed for an immediate response"
            raise ValueError(msg)

        return self.app.rest.interaction_message_builder(type_)

    def build_deferred_response(self, type_: _DeferredTypesT, /) -> special_endpoints.InteractionDeferredBuilder:
        """Get a deferred message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            [`hikari.interactions.component_interactions.ComponentInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        !!! note
            Unlike [`hikari.api.special_endpoints.InteractionMessageBuilder`][],
            the result of this call can be returned as is without any modifications
            being made to it.

        Parameters
        ----------
        type_
            The type of deferred response this should be.

            This may be one of the following:

            * [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]
            * [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`][]

        Returns
        -------
        hikari.api.special_endpoints.InteractionDeferredBuilder
            Deferred interaction message response builder object.
        """
        if type_ not in _DEFERRED_TYPES:
            msg = "Invalid type passed for a deferred response"
            raise ValueError(msg)

        return self.app.rest.interaction_deferred_builder(type_)


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class ComponentInteractionMetadata(base_interactions.PartialInteractionMetadata):
    """The interaction metadata for a component belonging to a message."""

    original_response_message_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the original response message, present only on follow-up messages."""

    interacted_message_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the message that contained the interactive component"""
