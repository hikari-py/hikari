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
"""Models and enums used for Discord's Modals interaction flow."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ModalInteraction",
    "ModalInteraction",
    "ModalInteractionMetadata",
    "ModalResponseTypesT",
)

import typing

import attrs

from hikari.interactions import base_interactions
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import components as components_
    from hikari import messages
    from hikari import snowflakes
    from hikari.api import special_endpoints

ModalResponseTypesT = typing.Literal[
    base_interactions.ResponseType.MESSAGE_CREATE,
    4,
    base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE,
    5,
    base_interactions.ResponseType.MESSAGE_UPDATE,
    7,
    base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE,
    6,
]
"""Type-hint of the response types which are valid for a modal interaction.

The following types are valid for this:

* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE`][]/`4`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE`][]/`5`
* [`hikari.interactions.base_interactions.ResponseType.MESSAGE_UPDATE`][]/`7`
* [`hikari.interactions.base_interactions.ResponseType.DEFERRED_MESSAGE_UPDATE`][]/`6`
"""


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class ModalInteraction(
    base_interactions.MessageResponseMixin[ModalResponseTypesT], base_interactions.PremiumResponseMixin
):
    """Represents a modal interaction on Discord."""

    custom_id: str = attrs.field(eq=False, hash=False, repr=True)
    """The custom id of the modal."""

    message: messages.Message | None = attrs.field(eq=False, repr=False)
    """The message whose component triggered the modal.

    This will be [`None`][] if the modal was a response to a command.
    """

    components: typing.Sequence[components_.ModalActionRowComponent] = attrs.field(eq=False, hash=False, repr=True)
    """Components in the modal."""

    def build_response(self) -> special_endpoints.InteractionMessageBuilder:
        """Get a message response builder for use in the REST server flow.

        !!! note
            For interactions received over the gateway
            [`hikari.interactions.modal_interactions.ModalInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        Examples
        --------
        ```py
        async def handle_modal_interaction(
            interaction: ModalInteraction,
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
            [`hikari.interactions.modal_interactions.ModalInteraction.create_initial_response`][]
            should be used to set the interaction response message.

        !!! note
            Unlike [`hikari.api.special_endpoints.InteractionMessageBuilder`][],
            the result of this call can be returned as is without any modifications
            being made to it.

        Returns
        -------
        hikari.api.special_endpoints.InteractionDeferredBuilder
            Deferred interaction message response builder object.
        """
        return self.app.rest.interaction_deferred_builder(base_interactions.ResponseType.DEFERRED_MESSAGE_CREATE)


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class ModalInteractionMetadata(base_interactions.PartialInteractionMetadata):
    """The interaction metadata for a modal initiated message."""

    original_response_message_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the original response message, present only on follow-up messages."""

    triggering_interaction_metadata: base_interactions.PartialInteractionMetadata = attrs.field(
        eq=False, hash=False, repr=True
    )
    """The metadata for the interaction that was used to open the modal."""
