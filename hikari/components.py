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
    "ActionRowComponent",
    "ButtonComponent",
    "ButtonStyle",
    "ChannelSelectMenuComponent",
    "ComponentType",
    "ContainerComponent",
    "ContainerTypesT",
    "FileComponent",
    "InteractiveButtonTypes",
    "InteractiveButtonTypesT",
    "MediaGalleryComponent",
    "MediaGalleryItem",
    "MediaLoadingType",
    "MediaResource",
    "MessageActionRowComponent",
    "MessageComponentTypesT",
    "ModalActionRowComponent",
    "ModalComponentTypesT",
    "PartialComponent",
    "SectionComponent",
    "SelectMenuComponent",
    "SelectMenuOption",
    "SeparatorComponent",
    "SpacingType",
    "TextDisplayComponent",
    "TextInputComponent",
    "TextInputStyle",
    "TextSelectMenuComponent",
    "ThumbnailComponent",
    "TopLevelComponentTypesT",
)

import typing

import attrs

from hikari import channels
from hikari import emojis
from hikari import files
from hikari.internal import enums
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari import channels
    from hikari import colors
    from hikari import emojis
    from hikari import undefined


@typing.final
class ComponentType(int, enums.Enum):
    """Types of components found within Discord."""

    ACTION_ROW = 1
    """A non-interactive container component for other types of components.

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


@typing.final
class SpacingType(int, enums.Enum):
    """Spacing Type.

    The type of spacing for a [SeparatorComponent][]
    """

    SMALL = 1
    """A small separator."""

    LARGE = 2
    """A large separator."""


@typing.final
class MediaLoadingType(int, enums.Enum):
    """Media loading type."""

    UNKNOWN = 0
    """Media is in an unknown loading state."""

    LOADING = 1
    """Media is loading."""

    LOADED_SUCCESS = 2
    """Media has successfully loaded."""

    LOADED_NOT_FOUND = 3
    """Media was not found."""


@attrs.define(kw_only=True, weakref_slot=False)
class PartialComponent:
    """Base class for all component entities."""

    type: ComponentType | int = attrs.field()
    """The type of component this is."""

    id: int = attrs.field()
    """The ID of the interaction."""


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

    def __getitem__(self, index_or_slice: int | slice, /) -> PartialComponent | typing.Sequence[AllowedComponentsT]:
        return self.components[index_or_slice]

    def __iter__(self) -> typing.Iterator[AllowedComponentsT]:
        return iter(self.components)

    def __len__(self) -> int:
        return len(self.components)


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class ButtonComponent(PartialComponent):
    """Represents a button component."""

    style: ButtonStyle | int = attrs.field(eq=False)
    """The button's style."""

    label: str | None = attrs.field(eq=False)
    """Text label which appears on the button."""

    emoji: emojis.Emoji | None = attrs.field(eq=False)
    """Custom or unicode emoji which appears on the button."""

    custom_id: str | None = attrs.field(hash=True)
    """Developer defined identifier for this button (will be <= 100 characters).

    !!! note
        This is required for the following button styles:

        * [`hikari.components.ButtonStyle.PRIMARY`][]
        * [`hikari.components.ButtonStyle.SECONDARY`][]
        * [`hikari.components.ButtonStyle.SUCCESS`][]
        * [`hikari.components.ButtonStyle.DANGER`][]
    """

    url: str | None = attrs.field(eq=False)
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

    description: str | None = attrs.field()
    """Optional description of the option, max 100 characters."""

    emoji: emojis.Emoji | None = attrs.field(eq=False)
    """Custom or unicode emoji which appears on the button."""

    is_default: bool = attrs.field()
    """Whether this option will be selected by default."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class SelectMenuComponent(PartialComponent):
    """Represents a select menu component."""

    custom_id: str = attrs.field(hash=True)
    """Developer defined identifier for this menu (will be <= 100 characters)."""

    placeholder: str | None = attrs.field(eq=False)
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

    channel_types: typing.Sequence[int | channels.ChannelType] = attrs.field(eq=False)
    """The valid channel types for this menu."""


@attrs.define(kw_only=True, weakref_slot=False)
class TextInputComponent(PartialComponent):
    """Represents a text input component."""

    custom_id: str = attrs.field(repr=True)
    """Developer set custom ID used for identifying interactions with this modal."""

    value: str = attrs.field(repr=True)
    """Value provided for this text input."""


@attrs.define(kw_only=True, weakref_slot=False)
class MediaResource(files.Resource[files.AsyncReader]):
    """Represents a media resource."""

    resource: files.Resource[files.AsyncReader] = attrs.field(repr=True)
    """The resource this object wraps around."""

    proxy_resource: files.Resource[files.AsyncReader] | None = attrs.field(default=None, repr=False)
    """The proxied version of the resource, or [`None`][] if not present.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed
        and will be ignored during serialization. Expect this to be
        populated on any received embed attached to a message event.
    """

    width: undefined.UndefinedNoneOr[int] = attrs.field(repr=True)
    """The width of media item."""

    height: undefined.UndefinedNoneOr[int] = attrs.field(repr=True)
    """The height of the media item."""

    content_type: undefined.UndefinedNoneOr[str] = attrs.field(repr=True)
    """The content type of the media item."""

    loading_state: undefined.UndefinedNoneOr[MediaLoadingType] = attrs.field(repr=True)
    """The loading state of the media item."""

    @property
    @typing_extensions.override
    def url(self) -> str:
        """URL of this embed resource."""
        return self.resource.url

    @property
    @typing_extensions.override
    def filename(self) -> str:
        """File name of this embed resource."""
        return self.resource.filename

    @property
    def proxy_url(self) -> str | None:
        """Proxied URL of this embed resource if applicable, else [`None`][]."""
        return self.proxy_resource.url if self.proxy_resource else None

    @property
    def proxy_filename(self) -> str | None:
        """File name of the proxied version of this embed resource if applicable, else [`None`][]."""
        return self.proxy_resource.filename if self.proxy_resource else None

    @typing_extensions.override
    def stream(
        self, *, executor: concurrent.futures.Executor | None = None, head_only: bool = False
    ) -> files.AsyncReaderContextManager[files.AsyncReader]:
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
class SectionComponent(PartialComponent):
    """Represents a section component."""

    components: typing.Sequence[SectionComponentTypesT] = attrs.field()
    """The sections components."""

    accessory: SectionAccessoryTypesT = attrs.field()
    """The sections accessory."""


@attrs.define(kw_only=True, weakref_slot=False)
class ThumbnailComponent(PartialComponent):
    """Represents a thumbnail component."""

    media: MediaResource = attrs.field()
    """The media for the thumbnail."""

    description: str | None = attrs.field()
    """The description of the thumbnail."""

    is_spoiler: bool = attrs.field()
    """Whether the thumbnail is marked as a spoiler."""


@attrs.define(kw_only=True, weakref_slot=False)
class TextDisplayComponent(PartialComponent):
    """Represents a text display component."""

    content: str = attrs.field()
    """The content of the text display."""


@attrs.define(kw_only=True, weakref_slot=False)
class MediaGalleryComponent(PartialComponent):
    """Represents a media gallery component."""

    items: typing.Sequence[MediaGalleryItem] = attrs.field()
    """The media gallery's items."""


@attrs.define(kw_only=True, weakref_slot=False)
class MediaGalleryItem:
    """Represents a media gallery item."""

    media: MediaResource = attrs.field()
    """The media for the gallery item."""

    description: str | None = attrs.field()
    """The description of the gallery item."""

    is_spoiler: bool = attrs.field()
    """Whether the gallery item is marked as a spoiler."""


@attrs.define(kw_only=True, weakref_slot=False)
class SeparatorComponent(PartialComponent):
    """Represents the separator component."""

    spacing: SpacingType = attrs.field()
    """The spacing for the separator."""

    divider: bool = attrs.field()
    """If there is a divider for the separator."""


@attrs.define(kw_only=True, weakref_slot=False)
class FileComponent(PartialComponent):
    """Represents a file component."""

    file: MediaResource = attrs.field()
    """The media for the file."""

    is_spoiler: bool = attrs.field()
    """If the file has a spoiler."""


@attrs.define(kw_only=True, weakref_slot=False)
class ContainerComponent(PartialComponent):
    """Represents a container component."""

    accent_color: colors.Color | None = attrs.field()
    """The accent colour for the container."""

    is_spoiler: bool = attrs.field()
    """Whether the container is marked as a spoiler."""

    components: typing.Sequence[ContainerTypesT] = attrs.field()
    """The components within the container."""


TopLevelComponentTypesT = typing.Union[
    ActionRowComponent[PartialComponent],
    TextDisplayComponent,
    SectionComponent,
    MediaGalleryComponent,
    SeparatorComponent,
    FileComponent,
    ContainerComponent,
]
"""Type hints of the values which are valid for top level components.

The following values are valid for this:

* [`hikari.components.ActionRowComponent`][]
* [`hikari.components.TextDisplayComponent`][]
* [`hikari.components.SectionComponent`][]
* [`hikari.components.MediaGalleryComponent`][]
* [`hikari.components.SeparatorComponent`][]
* [`hikari.components.FileComponent`][]
* [`hikari.components.ContainerComponent`][]
"""

ContainerTypesT = typing.Union[
    ActionRowComponent[PartialComponent],
    TextDisplayComponent,
    SectionComponent,
    MediaGalleryComponent,
    SeparatorComponent,
    FileComponent,
]
"""Type hints of the values which are valid for container components.

The following values are valid for this:

* [`hikari.components.ActionRowComponent`][]
* [`hikari.components.TextDisplayComponent`][]
* [`hikari.components.SectionComponent`][]
* [`hikari.components.MediaGalleryComponent`][]
* [`hikari.components.SeparatorComponent`][]
* [`hikari.components.FileComponent`][]
"""

SectionComponentTypesT = TextDisplayComponent
"""Type hints of the values which are valid for section components.

The following values are valid for this:

* [`hikari.components.TextDisplayComponent`][]
"""

SectionAccessoryTypesT = typing.Union[ButtonComponent, ThumbnailComponent]
"""Type hints of the values which are valid for section accessories.

The following values are valid for this:

* [`hikari.components.ButtonComponent`][]
* [`hikari.components.ThumbnailComponent`][]
"""

SelectMenuTypesT = typing.Literal[
    ComponentType.TEXT_SELECT_MENU,
    3,
    ComponentType.USER_SELECT_MENU,
    5,
    ComponentType.ROLE_SELECT_MENU,
    6,
    ComponentType.MENTIONABLE_SELECT_MENU,
    7,
    ComponentType.CHANNEL_SELECT_MENU,
    8,
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

InteractiveButtonTypesT = typing.Literal[
    ButtonStyle.PRIMARY, 1, ButtonStyle.SECONDARY, 2, ButtonStyle.SUCCESS, 3, ButtonStyle.DANGER, 4
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
"""  # noqa: E501
ModalComponentTypesT = TextInputComponent
"""Type hint of the [`hikari.components.PartialComponent`][] that be contained in a [`hikari.components.PartialComponent`][].

The following values are valid for this:

* [`hikari.components.TextInputComponent`][]
"""  # noqa: E501

MessageActionRowComponent = ActionRowComponent[MessageComponentTypesT]
"""A message action row component."""
ModalActionRowComponent = ActionRowComponent[ModalComponentTypesT]
"""A modal action row component."""
