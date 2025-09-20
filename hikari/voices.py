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
"""Application and entities that are used to describe voice state on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("VoiceRegion", "VoiceState")

import typing

import attrs

from hikari.internal import attrs_extensions
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class VoiceState:
    """Represents a user's voice connection status."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    channel_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the channel this user is connected to.

    This will be [`None`][] if they are leaving voice.
    """

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the guild this voice state is in."""

    is_guild_deafened: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this user is deafened by the guild."""

    is_guild_muted: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this user is muted by the guild."""

    is_self_deafened: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this user is deafened by their client."""

    is_self_muted: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this user is muted by their client."""

    is_streaming: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this user is streaming using "Go Live"."""

    is_suppressed: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this user is considered to be "suppressed" in a voice context.

    In the context of a voice channel this may mean that the user is muted by
    the current user and in the context of a stage channel this means that the
    user is not a speaker."""

    is_video_enabled: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this user's camera is enabled."""

    user_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the user this voice state is for."""

    member: guilds.Member | None = attrs.field(eq=False, hash=False, repr=False)
    """The guild member this voice state is for.

    This can be [`None`][] in cases where the Discord backend fails to
    resolve the member object from the user ID. This can sometimes happen
    when a user is kicked from the server.
    """

    session_id: str = attrs.field(hash=True, repr=True)
    """The string ID of this voice state's session."""

    requested_to_speak_at: datetime.datetime | None = attrs.field(eq=False, hash=False, repr=True)
    """When the user requested to speak in a stage channel.

    Will be [`None`][] if they have not requested to speak.
    """


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class VoiceRegion:
    """Represents a voice region server."""

    id: str = attrs.field(hash=True, repr=True)
    """The string ID of this region.

    !!! note
        Unlike most parts of this API, this ID will always be a string type.
        This is intentional.
    """

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The name of this region."""

    is_optimal_location: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this region's server is closest to the current user's client."""

    is_deprecated: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this region is deprecated."""

    is_custom: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this region is custom (e.g. used for events)."""

    @typing_extensions.override
    def __str__(self) -> str:
        return self.id
