# -*- coding: utf-8 -*-
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
"""Models for monetized apps & premium features."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("SKUType", "SKUFlags", "EntitlementType", "EntitlementOwnerType", "SKU", "Entitlement")

import datetime
import typing

import attrs

from hikari import snowflakes
from hikari.internal import enums


@typing.final
class SKUType(int, enums.Enum):
    """Represents the type of an entitlement."""

    SUBSCRIPTION = 5
    """Represents a recurring subscription"""

    SUBSCRIPTION_GROUP = 6
    """System-generated group for each SUBSCRIPTION SKU created"""


@typing.final
class SKUFlags(enums.Flag):
    """Represents the flags of a SKU."""

    NONE = 0
    """No flags set"""

    AVAILABLE = 1 << 2
    """SKU is available for purchase"""

    GUILD_SUBSCRIPTION = 1 << 7
    """	Recurring SKU that can be purchased by a user and applied to a single server.

    Grants access to every user in that server.
    """

    USER_SUBSCRIPTION = 1 << 8
    """Recurring SKU purchased by a user for themselves.

    Grants access to the purchasing user in every server.
    """


@typing.final
class EntitlementType(int, enums.Enum):
    """Represents the type of an entitlement."""

    APPLICATION_SUBSCRIPTION = 8
    """Entitlement was purchased as an app subscription"""


@typing.final
class EntitlementOwnerType(int, enums.Enum):
    """Represents the type of an entitlement owner."""

    GUILD = 1
    """Entitlement is owned by a guild"""

    USER = 2
    """Entitlement is owned by a user"""


@attrs.define(kw_only=True, weakref_slot=False)
class SKU(snowflakes.Unique):
    """Represents an SKU (stock-keeping unit).

    SKUs on Discord represent premium offerings that can be
    made available to your application's users or guilds.
    """

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of the SKU"""

    type: typing.Union[SKUType, int] = attrs.field(eq=False, hash=False, repr=True)
    """The type of the SKU"""

    application_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """The ID of the parent application"""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """Customer-facing name of the SKU"""

    slug: str = attrs.field(eq=False, hash=False, repr=True)
    """Discord-generated URL slug based on the SKU's name"""

    flags: SKUFlags = attrs.field(eq=False, hash=False, repr=True)
    """The flags for the SKU"""


@attrs.define(kw_only=True, weakref_slot=False)
class Entitlement(snowflakes.Unique):
    """An entitlement represents that a user or guild has access to a premium offering in your application."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """ID of the entitlement"""

    sku_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the SKU"""

    application_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the parent application"""

    user_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=True)
    """ID of the user that is granted access to the entitlement's SKU"""

    type: typing.Union[EntitlementType, int] = attrs.field(eq=False, hash=False, repr=True)
    """Type of entitlement"""

    is_deleted: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the entitlement has been deleted"""

    starts_at: typing.Optional[datetime.datetime] = attrs.field(eq=False, hash=False, repr=False)
    """Start date at which the entitlement is valid. Not present when using test entitlements."""

    ends_at: typing.Optional[datetime.datetime] = attrs.field(eq=False, hash=False, repr=False)
    """Date at which the entitlement is no longer valid. Not present when using test entitlements."""

    guild_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """ID of the guild that is granted access to the entitlement's SKU"""

    # Only partially documented by Discord
    subscription_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the subscription that this entitlement is associated with.

    Not present when using test entitlements.
    """
