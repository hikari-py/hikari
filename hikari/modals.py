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
"""Models for the components Discord sends back when a modal is submitted."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ModalChannelSelectMenuComponent",
    "ModalComponentTypesT",
    "ModalFileUploadComponent",
    "ModalLabelComponent",
    "ModalLabelComponentTypesT",
    "ModalMentionableSelectMenuComponent",
    "ModalRoleSelectMenuComponent",
    "ModalSelectMenuComponent",
    "ModalTextInputComponent",
    "ModalTextSelectMenuComponent",
    "ModalUserSelectMenuComponent",
    "PartialModalComponent",
)

import typing

import attrs

if typing.TYPE_CHECKING:
    from hikari import components
    from hikari import snowflakes


@attrs.define(kw_only=True, weakref_slot=False)
class PartialModalComponent:
    """Base class for all components submitted through a modal."""

    type: components.ComponentType | int = attrs.field()
    """The type of component this is."""

    id: int = attrs.field()
    """The ID of the component, unique within the modal it was submitted from."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalSelectMenuComponent(PartialModalComponent):
    """Represents a select menu component submitted through a modal."""

    custom_id: str = attrs.field()
    """Developer defined identifier for this menu (will be <= 100 characters)."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalTextSelectMenuComponent(ModalSelectMenuComponent):
    """Represents a text select menu component submitted through a modal."""

    values: typing.Sequence[str] = attrs.field()
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalUserSelectMenuComponent(ModalSelectMenuComponent):
    """Represents a user select menu component submitted through a modal."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field()
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalRoleSelectMenuComponent(ModalSelectMenuComponent):
    """Represents a role select menu component submitted through a modal."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field()
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalMentionableSelectMenuComponent(ModalSelectMenuComponent):
    """Represents a mentionable select menu component submitted through a modal."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field()
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalChannelSelectMenuComponent(ModalSelectMenuComponent):
    """Represents a channel select menu component submitted through a modal."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field()
    """The values that have been selected."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalTextInputComponent(PartialModalComponent):
    """Represents a text input component submitted through a modal."""

    custom_id: str = attrs.field()
    """Developer set custom ID used for identifying this text input."""

    value: str = attrs.field()
    """Value provided for this text input."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalLabelComponent(PartialModalComponent):
    """Represents a label component submitted through a modal."""

    component: ModalLabelComponentTypesT = attrs.field()
    """The component within the label."""


@attrs.define(kw_only=True, weakref_slot=False)
class ModalFileUploadComponent(PartialModalComponent):
    """Represents a file upload component submitted through a modal."""

    custom_id: str = attrs.field()
    """Developer set custom ID used for identifying interactions with this file upload."""

    values: typing.Sequence[snowflakes.Snowflake] = attrs.field()
    """A list of snowflakes in relation to the attachments, that can be found in the resolved interaction data."""


ModalComponentTypesT = ModalLabelComponent
"""Type hints of the top-level components a submitted modal can contain.

The following values are valid for this:

* [`hikari.modals.ModalLabelComponent`][]
"""

ModalLabelComponentTypesT = (
    ModalTextInputComponent
    | ModalTextSelectMenuComponent
    | ModalUserSelectMenuComponent
    | ModalRoleSelectMenuComponent
    | ModalMentionableSelectMenuComponent
    | ModalChannelSelectMenuComponent
    | ModalFileUploadComponent
)
"""Type hints of the components a submitted modal label can contain.

The following values are valid for this:

* [`hikari.modals.ModalTextInputComponent`][]
* [`hikari.modals.ModalTextSelectMenuComponent`][]
* [`hikari.modals.ModalUserSelectMenuComponent`][]
* [`hikari.modals.ModalRoleSelectMenuComponent`][]
* [`hikari.modals.ModalMentionableSelectMenuComponent`][]
* [`hikari.modals.ModalChannelSelectMenuComponent`][]
* [`hikari.modals.ModalFileUploadComponent`][]
"""
