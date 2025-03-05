# cython: language_level=3
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
"""Application and entities that are used to describe components on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ComponentType",
    "PartialComponent",
    "ActionRowComponent",
    "ButtonStyle",
    "ButtonComponent",
    "SelectMenuOption",
    "SelectMenuComponent",
    "TextSelectMenuComponent",
    "ChannelSelectMenuComponent",
    "TextInputStyle",
    "TextInputComponent",
    "InteractiveButtonTypes",
    "InteractiveButtonTypesT",
    "MessageComponentTypesT",
    "ModalComponentTypesT",
    "MessageActionRowComponent",
    "ModalActionRowComponent",
    "PartialComponentV2",
    "SectionComponent",
    "ThumbnailComponent",
    "TextDisplayComponent",
    "MediaGalleryComponent",
    "MediaGalleryItem",
    "SeparatorComponent",
    "SpacingType",
    "FileComponent",
    "ContainerComponent",
    "TopLevelComponentTypesT",
    "ContainerTypesT"
)

import typing

import attrs
import concurrent.futures

from hikari import channels
from hikari import emojis
from hikari import files
from hikari import colors
from hikari.internal import enums


@typing.final
class ComponentType(int, enums.Enum):
    """Types of components found within Discord."""

    ACTION_ROW = 1
    """A non-interactive container component for other types of components.

    !!! note
        As this is a container component it can never be contained within another
        component and therefore will always be top-level.

    !!! note
        As of writing this can only contain one component type.
    """

    BUTTON = 2
    """A button component.

    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.ACTION_ROW`][].
    """

    TEXT_SELECT_MENU = 3
    """A text select component.

    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.ACTION_ROW`][].
    """

    TEXT_INPUT = 4
    """A text input component.

    !!! note
        This component may only be used inside a modal container.

    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.ACTION_ROW`][].
    """

    USER_SELECT_MENU = 5
    """A user select component.

    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.ACTION_ROW`][].
    """

    ROLE_SELECT_MENU = 6
    """A role select component.

    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.ACTION_ROW`][].
    """

    MENTIONABLE_SELECT_MENU = 7
    """A mentionable (users and roles) select component.

    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.ACTION_ROW`][].
    """

    CHANNEL_SELECT_MENU = 8
    """A channel select component.

    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.ACTION_ROW`][].
    """

    SECTION = 9
    """A section component.
    
    !!! note
        As this is a container component it can never be contained within another
        component and therefore will always be top-level.
    """
    
    TEXT_DISPLAY = 10
    """A text display component."""
    
    THUMBNAIL = 11
    """A thumbnail component.
    
    !!! note
        This cannot be top-level and must be within a container component such
        as [`hikari.components.ComponentType.SECTION`][].
    """

    MEDIA_GALLERY = 12
    """A media gallery component."""
    
    FILE = 13
    """A file component."""
    
    SEPARATOR = 14
    """A separator component."""
    
    CONTAINER = 17
    """A container component.
    
    !!! note
        As this is a container component it can never be contained within another
        component and therefore will always be top-level.
    """


@typing.final
class ButtonStyle(int, enums.Enum):
    """Enum of the available button styles.

    More information, such as how these look, can be found at
    https://discord.com/developers/docs/interactions/message-components#button-object-button-styles
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


@typing.final
class TextInputStyle(int, enums.Enum):
    """A text input style."""

    SHORT = 1
    """Intended for short single-line text."""

    PARAGRAPH = 2
    """Intended for much longer inputs."""


@attrs.define(kw_only=True, weakref_slot=False)
class PartialComponent:
    """Base class for all component entities."""

    type: typing.Union[ComponentType, int] = attrs.field()
    """The type of component this is."""


AllowedComponentsT = typing.TypeVar("AllowedComponentsT", bound="PartialComponent")


@attrs.define(weakref_slot=False)
class ActionRowComponent(typing.Generic[AllowedComponentsT], PartialComponent):
    """Represents a row of components."""

    components: typing.Sequence[AllowedComponentsT] = attrs.field()
    """Sequence of the components contained within this row."""

    @typing.overload
    def __getitem__(self, index: int, /) -> PartialComponent: ...

    @typing.overload
    def __getitem__(self, slice_: slice, /) -> typing.Sequence[AllowedComponentsT]: ...

    def __getitem__(
        self, index_or_slice: typing.Union[int, slice], /
    ) -> typing.Union[PartialComponent, typing.Sequence[AllowedComponentsT]]:
        return self.components[index_or_slice]

    def __iter__(self) -> typing.Iterator[AllowedComponentsT]:
        return iter(self.components)

    def __len__(self) -> int:
        return len(self.components)


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class ButtonComponent(PartialComponent):
    """Represents a button component."""

    style: typing.Union[ButtonStyle, int] = attrs.field(eq=False)
    """The button's style."""

    label: typing.Optional[str] = attrs.field(eq=False)
    """Text label which appears on the button."""

    emoji: typing.Optional[emojis.Emoji] = attrs.field(eq=False)
    """Custom or unicode emoji which appears on the button."""

    custom_id: typing.Optional[str] = attrs.field(hash=True)
    """Developer defined identifier for this button (will be <= 100 characters).

    !!! note
        This is required for the following button styles:

        * [`hikari.components.ButtonStyle.PRIMARY`][]
        * [`hikari.components.ButtonStyle.SECONDARY`][]
        * [`hikari.components.ButtonStyle.SUCCESS`][]
        * [`hikari.components.ButtonStyle.DANGER`][]
    """

    url: typing.Optional[str] = attrs.field(eq=False)
    """Url for [`hikari.components.ButtonStyle.LINK`][] style buttons."""

    is_disabled: bool = attrs.field(eq=False)
    """Whether the button is disabled."""


@attrs.define(kw_only=True, weakref_slot=False)
class SelectMenuOption:
    """Represents an option for a [`hikari.components.SelectMenuComponent`][]."""

    label: str = attrs.field()
    """User-facing name of the option, max 100 characters."""

    value: str = attrs.field()
    """Dev-defined value of the option, max 100 characters."""

    description: typing.Optional[str] = attrs.field()
    """Optional description of the option, max 100 characters."""

    emoji: typing.Optional[emojis.Emoji] = attrs.field(eq=False)
    """Custom or unicode emoji which appears on the button."""

    is_default: bool = attrs.field()
    """Whether this option will be selected by default."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class SelectMenuComponent(PartialComponent):
    """Represents a select menu component."""

    custom_id: str = attrs.field(hash=True)
    """Developer defined identifier for this menu (will be <= 100 characters)."""

    placeholder: typing.Optional[str] = attrs.field(eq=False)
    """Custom placeholder text shown if nothing is selected, max 100 characters."""

    min_values: int = attrs.field(eq=False)
    """The minimum amount of options which must be chosen for this menu.

    This will be greater than or equal to 0 and will be less than or equal to
    [`hikari.components.SelectMenuComponent.max_values`][].
    """

    max_values: int = attrs.field(eq=False)
    """The minimum amount of options which can be chosen for this menu.

    This will be less than or equal to 25 and will be greater than or equal to
    [`hikari.components.SelectMenuComponent.min_values`][].
    """

    is_disabled: bool = attrs.field(eq=False)
    """Whether the select menu is disabled."""


@attrs.define(kw_only=True, weakref_slot=False)
class TextSelectMenuComponent(SelectMenuComponent):
    """Represents a text select menu component."""

    options: typing.Sequence[SelectMenuOption] = attrs.field(eq=False)
    """Sequence of up to 25 of the options set for this menu."""


@attrs.define(kw_only=True, weakref_slot=False)
class ChannelSelectMenuComponent(SelectMenuComponent):
    """Represents a channel select menu component."""

    channel_types: typing.Sequence[typing.Union[int, channels.ChannelType]] = attrs.field(eq=False)
    """The valid channel types for this menu."""


@attrs.define(kw_only=True, weakref_slot=False)
class TextInputComponent(PartialComponent):
    """Represents a text input component."""

    custom_id: str = attrs.field(repr=True)
    """Developer set custom ID used for identifying interactions with this modal."""

    value: str = attrs.field(repr=True)
    """Value provided for this text input."""


@attrs.define(kw_only=True, weakref_slot=False)
class PartialComponentV2(PartialComponent): # FIXME: This defo needs changing.
    """FIXME: Document me."""

    id: typing.Optional[int] = attrs.field()
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class MediaResource:
    resource: files.WebResource = attrs.field(repr=True)
    """The resource this object wraps around."""

    @property
    @typing.final
    def url(self) -> str:
        """URL of this embed resource."""
        return self.resource.url

    @property
    def filename(self) -> str:
        """File name of this embed resource."""
        return self.resource.filename

    def stream(
        self, *, executor: typing.Optional[concurrent.futures.Executor] = None, head_only: bool = False
    ) -> files.AsyncReaderContextManager[files.WebReader]:
        """Produce a stream of data for the resource.

        Parameters
        ----------
        executor
            The executor to run in for blocking operations.
            If [`None`][], then the default executor is used for the
            current event loop.
        head_only
            If [`True`][], then the implementation may only retrieve
            HEAD information if supported. This currently only has
            any effect for web requests.
        """
        return self.resource.stream(executor=executor, head_only=head_only)


@attrs.define(kw_only=True, weakref_slot=False)
class SectionComponent(PartialComponentV2):
    """FIXME: Document me."""

    components: typing.Sequence[TextDisplayComponent] = attrs.field() # FIXME: Told not to hardcode this, as it could change? what should it be?
    """FIXME: Document me."""

    accessory: typing.Union[ButtonComponent, ThumbnailComponent] = attrs.field() # FIXME: Told not to hardcode this, as it could change? what should it be?
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class ThumbnailComponent(PartialComponentV2):
    """FIXME: Document me."""

    media: MediaResource = attrs.field()
    """FIXME: Document me."""

    description: typing.Optional[str] = attrs.field()
    """FIXME: Document me."""

    spoiler: typing.Optional[bool] = attrs.field()
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class TextDisplayComponent(PartialComponentV2):
    """FIXME: Document me."""
    
    content: str = attrs.field()
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class MediaGalleryComponent(PartialComponentV2):
    """FIXME: Document me."""

    items: typing.Sequence[MediaGalleryItem] = attrs.field()
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class MediaGalleryItem:
    """FIXME: Document me."""
    
    media: MediaResource = attrs.field()
    """FIXME: Document me."""

    description: typing.Optional[str] = attrs.field()
    """FIXME: Document me."""

    spoiler: typing.Optional[bool] = attrs.field()
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class SeparatorComponent(PartialComponentV2):
    """FIXME: Document me."""

    spacing: typing.Optional[SpacingType] = attrs.field()
    """FIXME: Document me."""

    divider: typing.Optional[bool] = attrs.field()
    """FIXME: Document me."""


@typing.final
class SpacingType(int, enums.Enum):
    """FIXME: Document me."""

    SMALL = 1
    """FIXME: Document me."""

    LARGE = 2
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class FileComponent(PartialComponentV2):
    """FIXME: Document me."""

    file: MediaResource = attrs.field()
    """FIXME: Document me."""
    
    spoiler: typing.Optional[bool] = attrs.field()
    """FIXME: Document me."""


@attrs.define(kw_only=True, weakref_slot=False)
class ContainerComponent(PartialComponentV2):
    """FIXME: Document me."""

    accent_color: typing.Optional[colors.Color] = attrs.field()
    """FIXME: Document me."""

    spoiler: typing.Optional[bool] = attrs.field()
    """FIXME: Document me."""

    components: typing.Sequence[ContainerTypesT] = attrs.field()

TopLevelComponentTypesT = typing.Union[
    ActionRowComponent[PartialComponent],
    TextDisplayComponent,
    SectionComponent,
    MediaGalleryComponent,
    SeparatorComponent,
    FileComponent,
    ContainerComponent
]
"""FIXME: Document me."""

ContainerTypesT = typing.Union[
    ActionRowComponent[PartialComponent],
    TextDisplayComponent,
    SectionComponent,
    MediaGalleryComponent,
    SeparatorComponent,
    FileComponent
]
"""FIXME: Document me."""

SelectMenuTypesT = typing.Union[
    typing.Literal[ComponentType.TEXT_SELECT_MENU],
    typing.Literal[3],
    typing.Literal[ComponentType.USER_SELECT_MENU],
    typing.Literal[5],
    typing.Literal[ComponentType.ROLE_SELECT_MENU],
    typing.Literal[6],
    typing.Literal[ComponentType.MENTIONABLE_SELECT_MENU],
    typing.Literal[7],
    typing.Literal[ComponentType.CHANNEL_SELECT_MENU],
    typing.Literal[8],
]
"""Type hints of the [`hikari.components.ComponentType`][] values which are valid for select menus.

The following values are valid for this:

* [`hikari.components.ComponentType.TEXT_SELECT_MENU`][]/`3`
* [`hikari.components.ComponentType.USER_SELECT_MENU`][]/`5`
* [`hikari.components.ComponentType.ROLE_SELECT_MENU`][]/`6`
* [`hikari.components.ComponentType.MENTIONABLE_SELECT_MENU`][]`/`7`
* [`hikari.components.ComponentType.CHANNEL_SELECT_MENU`][]`/`8`
"""

SelectMenuTypes: typing.AbstractSet[SelectMenuTypesT] = frozenset(
    (
        ComponentType.TEXT_SELECT_MENU,
        ComponentType.USER_SELECT_MENU,
        ComponentType.ROLE_SELECT_MENU,
        ComponentType.MENTIONABLE_SELECT_MENU,
        ComponentType.CHANNEL_SELECT_MENU,
    )
)
"""Set of the [`hikari.components.ComponentType`][] values which are valid for select menus.

The following values are included in this:

* [`hikari.components.ComponentType.TEXT_SELECT_MENU`][]
* [`hikari.components.ComponentType.USER_SELECT_MENU`][]
* [`hikari.components.ComponentType.ROLE_SELECT_MENU`][]
* [`hikari.components.ComponentType.MENTIONABLE_SELECT_MENU`][]
* [`hikari.components.ComponentType.CHANNEL_SELECT_MENU`][]
"""

InteractiveButtonTypesT = typing.Union[
    typing.Literal[ButtonStyle.PRIMARY],
    typing.Literal[1],
    typing.Literal[ButtonStyle.SECONDARY],
    typing.Literal[2],
    typing.Literal[ButtonStyle.SUCCESS],
    typing.Literal[3],
    typing.Literal[ButtonStyle.DANGER],
    typing.Literal[4],
]
"""Type hints of the [`hikari.components.ButtonStyle`][] values which are valid for interactive buttons.

The following values are valid for this:

* [`hikari.components.ButtonStyle.PRIMARY`][]
* [`hikari.components.ButtonStyle.SECONDARY`][]
* [`hikari.components.ButtonStyle.SUCCESS`][]
* [`hikari.components.ButtonStyle.DANGER`][]
"""

InteractiveButtonTypes: typing.AbstractSet[InteractiveButtonTypesT] = frozenset(
    [ButtonStyle.PRIMARY, ButtonStyle.SECONDARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]
)
"""Set of the [`hikari.components.ButtonStyle`][] which are valid for interactive buttons.

The following values are included in this:

* [`hikari.components.ButtonStyle.PRIMARY`][]
* [`hikari.components.ButtonStyle.SECONDARY`][]
* [`hikari.components.ButtonStyle.SUCCESS`][]
* [`hikari.components.ButtonStyle.DANGER`][]
"""

MessageComponentTypesT = typing.Union[ButtonComponent, SelectMenuComponent]
"""Type hint of the [`hikari.components.PartialComponent`][] that be contained in a [`hikari.components.PartialComponent`][].

The following values are valid for this:

* [`hikari.components.ButtonComponent`][]
* [`hikari.components.SelectMenuComponent`][]
"""
ModalComponentTypesT = TextInputComponent
"""Type hint of the [`hikari.components.PartialComponent`][] that be contained in a [`hikari.components.PartialComponent`][].

The following values are valid for this:

* [`hikari.components.TextInputComponent`][]
"""

MessageActionRowComponent = ActionRowComponent[MessageComponentTypesT]
"""A message action row component."""
ModalActionRowComponent = ActionRowComponent[ModalComponentTypesT]
"""A modal action row component."""
