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
"""Entities that are used to describe auto-moderation on Discord."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "AutoModActionType",
    "PartialAutoModAction",
    "AutoModBlockMessage",
    "AutoModSendAlertMessage",
    "AutoModTimeout",
    "AutoModEventType",
    "AutoModTriggerType",
    "AutoModKeywordPresetType",
    "PartialAutoModTrigger",
    "KeywordTrigger",
    "HarmfulLinkTrigger",
    "SpamTrigger",
    "KeywordPresetTrigger",
    "AutoModRule",
)

import typing

import attr

from hikari import snowflakes
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime

    from hikari import traits


class AutoModActionType(int, enums.Enum):
    """The type of an auto-moderation rule action."""

    BLOCK_MESSAGES = 1
    """Block the content of the triggering message."""

    SEND_ALERT_MESSAGE = 2
    """Log the triggering user content to a specified channel."""

    TIMEOUT = 3
    """Timeout the triggering message's author for a specified duration.

    This type can only be set for `KEYWORD` rules and requires the `MODERATE_MEMBERS`
    permission to use.
    """


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class PartialAutoModAction:
    """Base class for an action which is executed when a rule is triggered."""

    type: AutoModActionType = attr.field()
    """The type of auto-moderation action."""


@attr.define(kw_only=True, weakref_slot=False)
class AutoModBlockMessage(PartialAutoModAction):
    """Block the content of the triggering message."""


@attr.define(kw_only=True, weakref_slot=False)
class AutoModSendAlertMessage(PartialAutoModAction):
    """Log the triggering content to a specific channel."""

    channel_id: snowflakes.Snowflake = attr.field()
    """ID of the channel to log trigger events to."""


@attr.define(kw_only=True, weakref_slot=False)
class AutoModTimeout(PartialAutoModAction):
    """Timeout the triggering message's author for a specified duration.

    This type can only be set for `KEYWORD` rules and requires the `MODERATE_MEMBERS`
    permission to use.
    """

    duration: datetime.timedelta = attr.field()
    """The total seconds to timeout the user for (max 2419200 seconds/4 weeks)."""


class AutoModEventType(int, enums.Enum):
    """Type of event to check for an auto-moderation rule."""

    MESSAGE_SEND = 1
    """When a member sends or edits a message in the guild."""


class AutoModTriggerType(int, enums.Enum):
    """Type of trigger for an auto-moderation rule."""

    KEYWORD = 1
    """Match message content against a list of keywords."""

    HARMFUL_LINK = 2
    """Scan messages for links which are deemed "harmful" by Discord."""

    SPAM = 3
    """Discord's guild anti-spam system."""

    KEYWORD_PRESET = 4
    """Discord's preset keyword triggers."""


class AutoModKeywordPresetType(int, enums.Enum):
    """Discord's KEYWORD_PRESET type."""

    PROFANITY = 1
    """Trigger on words which may be considered forms of swearing or cursing."""

    SEXUAL_CONTENT = 2
    """Trigger on words that refer to explicit behaviour or activity."""

    SLURS = 3
    """Trigger on personal insults and words which "may be considered hate speech"."""


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class PartialAutoModTrigger:
    """Base class representing the content a rule triggers on."""

    type: AutoModTriggerType = attr.field(eq=False, hash=False, repr=False)
    """The type action this triggers."""


@attr.define(kw_only=True, weakref_slot=False)
class KeywordTrigger(PartialAutoModTrigger):
    """A trigger based on matching message content against a list of keywords."""

    keyword_filter: typing.Sequence[str] = attr.field(eq=False, hash=False, repr=False)
    """The filter strings this trigger checks for.

    This supports a wildcard matching strategy which is documented at
    https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies.
    """


class HarmfulLinkTrigger(PartialAutoModTrigger):
    """A trigger based on Discord's own list of links deemed "harmful"."""

    __slots__: typing.Sequence[str] = []


class SpamTrigger(PartialAutoModTrigger):
    """A trigger based on Discord's spam detection."""

    __slots__: typing.Sequence[str] = []


@attr.define(kw_only=True, weakref_slot=False)
class KeywordPresetTrigger(PartialAutoModTrigger):
    """A trigger based on a predefined set of presets provided by Discord."""

    allow_list: typing.Sequence[str] = attr.field(eq=False, factory=list, hash=False, repr=False)
    """A sequence of filters which will be exempt from triggering the preset trigger.

    This supports a wildcard matching strategy which is documented at
    https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies.
    """

    presets: typing.Sequence[typing.Union[int, AutoModKeywordPresetType]] = attr.field(eq=False, hash=False, repr=False)
    """The predefined presets provided by Discord to match against."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class AutoModRule(snowflakes.Unique):
    """Auto moderation rule which defines how user content is filtered."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    guild_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the guild this rule belongs to."""

    name: str = attr.field(eq=False, hash=False, repr=True)
    """The rule's name."""

    creator_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the user who originally created this rule."""

    event_type: AutoModEventType = attr.field(eq=False, hash=False, repr=True)
    """The type of event this rule triggers on."""

    trigger: PartialAutoModTrigger = attr.field(eq=False, hash=False, repr=False)
    """The content this rule triggers on."""

    actions: typing.Sequence[PartialAutoModAction] = attr.field(eq=False, hash=False, repr=False)
    """Sequence of the actions which will execute when this rule is triggered."""

    is_enabled: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether this rule is enabled."""

    exempt_channel_ids: typing.Sequence[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """A sequence of IDs of (up to 20) channels which aren't effected by this rule."""

    exempt_role_ids: typing.Sequence[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """A sequence of IDs of (up to 50) roles which aren't effected by this rule."""
