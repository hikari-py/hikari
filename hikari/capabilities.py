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
"""Gateway capabilities for opting the application into gateway behaviors."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("GatewayCapabilities",)

import typing

from hikari.internal import enums


@typing.final
class GatewayCapabilities(enums.Flag):
    """Represents a gateway capability.

    This is a bitfield representation of the gateway behaviors you wish to
    opt into. Unlike [`hikari.intents.Intents`][], which control which events
    your application receives, capabilities change how existing gateway
    behaviors work.

    This enum is an [`enum.IntFlag`][], which means that you can use bitwise
    operators to join and splice multiple capabilities into one value.

    For example, if we wish to only refer to the
    [`hikari.capabilities.GatewayCapabilities.CHANNEL_OBFUSCATION`][]
    capability, then it is simply a case of accessing it normally.

    ```py
    my_capabilities = GatewayCapabilities.CHANNEL_OBFUSCATION
    ```

    If we wanted to have several capabilities grouped together, we would use
    the bitwise-or operator to combine them (`|`). This can be done in-place
    with the `|=` operator if needed.
    """

    NONE = 0
    """Opts into no gateway capabilities."""

    CHANNEL_OBFUSCATION = 1 << 15
    """Opts the application into receiving obfuscated channel metadata for channels it can't view.

    When declared, guild channels the application doesn't have permission to
    view will still be dispatched over the gateway, but with their sensitive
    fields obfuscated: the channel's name becomes `"___hidden___"`, other
    sensitive fields are nulled or reduced,
    [`hikari.channels.ChannelFlag.CHANNEL_OBFUSCATED`][] is set on the
    channel's flags, and the permission overwrites will contain a single
    overwrite denying [`hikari.permissions.Permissions.VIEW_CHANNEL`][] for
    the guild's `@everyone` role.

    !!! warning
        This is a temporary, testing-only opt-in for channel obfuscation.
        Discord plans to change this opt-in mechanism before the feature
        reaches general availability, at which point obfuscation will apply
        to all applications automatically (planned for November 16, 2026),
        even when they don't declare this capability.
    """
