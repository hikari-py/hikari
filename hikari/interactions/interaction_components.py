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
"""Models and enums used for Discord's Components used in interactions."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ButtonInteractionComponent",
    "ChannelSelectMenuInteractionComponent",
    "FileUploadInteractionComponent",
    "InteractionComponentTypesT",
    "InteractionLabelTypesT",
    "LabelInteractionComponent",
    "PartialInteractionComponent",
    "SelectMenuInteractionComponent",
    "TextInputInteractionComponent",
    "TextSelectMenuInteractionComponent",
)

import typing

import attrs

if typing.TYPE_CHECKING:
    from hikari import components
    from hikari import snowflakes


@attrs.define(kw_only=True, weakref_slot=False)
class PartialInteractionComponent:
    """Base class for all component entities."""

    type: components.ComponentType | int = attrs.field()
    """The type of component this is."""

    id: int = attrs.field()
    """The ID of the interaction."""


AllowedComponentsT = typing.TypeVar("AllowedComponentsT", bound="PartialInteractionComponent")


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class ButtonInteractionComponent(PartialInteractionComponent):
    """Represents a button interaction component."""

    custom_id: str = attrs.field(hash=True)
    """Developer defined identifier for this button (will be <= 100 characters)."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class SelectMenuInteractionComponent(PartialInteractionComponent):
    """Represents a select menu interaction component."""

    custom_id: str = attrs.field(hash=True)
    """Developer defined identifier for this menu (will be <= 100 characters)."""


@attrs.define(kw_only=True, weakref_slot=False)
class TextSelectMenuInteractionComponent(SelectMenuInteractionComponent):
    """Represents a text select menu interaction component."""

    values: typing.Sequence[str] = attrs.field(eq=True)
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class UserSelectMenuInteractionComponent(SelectMenuInteractionComponent):
    """Represents a user select menu interaction component."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=True)
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class RoleSelectMenuInteractionComponent(SelectMenuInteractionComponent):
    """Represents a role select menu interaction component."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=True)
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class MentionableSelectMenuInteractionComponent(SelectMenuInteractionComponent):
    """Represents a mentionable select menu interaction component."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=True)
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class ChannelSelectMenuInteractionComponent(SelectMenuInteractionComponent):
    """Represents a channel select menu interaction component."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=True)
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class TextInputInteractionComponent(PartialInteractionComponent):
    """Represents a text input component."""

    custom_id: str = attrs.field(repr=True)
    """Developer set custom ID used for identifying interactions with this modal."""

    value: str = attrs.field(repr=True)
    """Value provided for this text input."""


@attrs.define(kw_only=True, weakref_slot=False)
class LabelInteractionComponent(PartialInteractionComponent):
    """Represents a label component."""

    component: InteractionLabelTypesT = attrs.field()
    """The component within the label."""


@attrs.define(kw_only=True, weakref_slot=False)
class FileUploadInteractionComponent(PartialInteractionComponent):
    """Represents a file upload component."""

    custom_id: str = attrs.field()
    """Developer set custom ID used for identifying interactions with this file upload."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field()
    """A list of snowflakes in relation to the attachments, that can be found in the resolved interaction data."""


InteractionComponentTypesT = typing.Union[LabelInteractionComponent]
"""Type hints of the values which are valid for interaction components.

The following values are valid for this:

* [`hikari.interaction.interaction_components.LabelInteractionComponent`][]
"""

InteractionLabelTypesT = typing.Union[
    TextInputInteractionComponent,
    TextSelectMenuInteractionComponent,
    UserSelectMenuInteractionComponent,
    RoleSelectMenuInteractionComponent,
    MentionableSelectMenuInteractionComponent,
    ChannelSelectMenuInteractionComponent,
    FileUploadInteractionComponent,
]
"""Type hints of the values which are valid for interaction label components.

The following values are valid for this:

* [`hikari.interaction.interaction_components.TextInputInteractionComponent`][]
* [`hikari.interaction.interaction_components.TextSelectMenuInteractionComponent`][]
* [`hikari.interaction.interaction_components.UserSelectMenuInteractionComponent`][]
* [`hikari.interaction.interaction_components.RoleSelectMenuInteractionComponent`][]
* [`hikari.interaction.interaction_components.MentionableSelectMenuInteractionComponent`][]
* [`hikari.interaction.interaction_components.ChannelSelectMenuInteractionComponent`][]
* [`hikari.interaction.interaction_components.FileUploadInteractionComponent`][]
"""
