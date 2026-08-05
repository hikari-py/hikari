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

__all__: typing.Sequence[str] = (
    "SKU",
    "Entitlement",
    "EntitlementOwnerType",
    "EntitlementType",
    "SKUFlags",
    "SKUType",
    "Subscription",
    "SubscriptionStatus",
)

import typing

import attrs

from hikari import snowflakes
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime


@typing.final
class SKUType(int, enums.Enum):
    """Represents the type of a SKU."""

    DURABLE = 2
    """Durable one-time purchase"""

    CONSUMABLE = 3
    """Consumable one-time purchase"""

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

    PURCHASE = 1
    """Entitlement was purchased by user"""

    PREMIUM_SUBSCRIPTION = 2
    """Entitlement for Discord Nitro subscription"""

    DEVELOPER_GIFT = 3
    """Entitlement was gifted by developer"""

    TEST_MODE_PURCHASE = 4
    """Entitlement was purchased by a dev in application test mode"""

    FREE_PURCHASE = 5
    """Entitlement was granted when the SKU was free"""

    USER_GIFT = 6
    """Entitlement was gifted by another user"""

    PREMIUM_PURCHASE = 7
    """Entitlement was claimed by user for free as a Nitro Subscriber"""

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

    type: SKUType | int = attrs.field(eq=False, hash=False, repr=True)
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

    user_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """ID of the user that is granted access to the entitlement's SKU"""

    type: EntitlementType | int = attrs.field(eq=False, hash=False, repr=True)
    """Type of entitlement"""

    is_deleted: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the entitlement has been deleted"""

    is_consumed: bool = attrs.field(eq=False, hash=False, repr=False)
    """For consumable items, whether the entitlement has been consumed"""

    starts_at: datetime.datetime | None = attrs.field(eq=False, hash=False, repr=False)
    """Start date at which the entitlement is valid. Not present when using test entitlements."""

    ends_at: datetime.datetime | None = attrs.field(eq=False, hash=False, repr=False)
    """Date at which the entitlement is no longer valid. Not present when using test entitlements."""

    guild_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """ID of the guild that is granted access to the entitlement's SKU"""

    # Only partially documented by Discord
    subscription_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the subscription that this entitlement is associated with.

    Not present when using test entitlements.
    """


@typing.final
class SubscriptionStatus(int, enums.Enum):
    """Represents the status of a subscription."""

    ACTIVE = 0
    """The subscription is active and scheduled to renew"""

    INACTIVE = 1
    """The subscription is inactive and not being charged"""

    ENDING = 2
    """The subscription is active but will not renew"""


@attrs.define(kw_only=True, weakref_slot=False)
class Subscription(snowflakes.Unique):
    """Represents a user making recurring payments for at least one SKU.

    !!! note
        The subscription status should not be used to grant perks. Use
        [`hikari.monetization.Entitlement`][]s as an indication of whether a
        user should have access to a specific SKU.
    """

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """ID of the subscription"""

    user_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the user who is subscribed"""

    sku_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=True)
    """List of SKUs subscribed to"""

    entitlement_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """List of entitlements granted for this subscription"""

    renewal_sku_ids: typing.Sequence[snowflakes.Snowflake] | None = attrs.field(eq=False, hash=False, repr=False)
    """List of SKUs that this user will be subscribed to at renewal, if known"""

    current_period_start: datetime.datetime = attrs.field(eq=False, hash=False, repr=False)
    """Start of the current subscription period"""

    current_period_end: datetime.datetime = attrs.field(eq=False, hash=False, repr=False)
    """End of the current subscription period"""

    status: SubscriptionStatus | int = attrs.field(eq=False, hash=False, repr=True)
    """Current status of the subscription"""

    canceled_at: datetime.datetime | None = attrs.field(eq=False, hash=False, repr=False)
    """When the subscription was canceled, if it was"""

    country: str | None = attrs.field(eq=False, hash=False, repr=False)
    """ISO3166-1 alpha-2 country code of the payment source used to purchase the subscription.

    This will be [`None`][] unless queried with a private OAuth scope.
    """
