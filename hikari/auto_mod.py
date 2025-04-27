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
    "AutoModBlockMessage",
    "AutoModEventType",
    "AutoModKeywordPresetType",
    "AutoModRule",
    "AutoModSendAlertMessage",
    "AutoModTimeout",
    "AutoModTriggerType",
    "KeywordPresetTrigger",
    "KeywordTrigger",
    "MemberProfileTrigger",
    "MentionSpamTrigger",
    "PartialAutoModAction",
    "PartialAutoModTrigger",
    "SpamTrigger",
)

import typing

import attrs

from hikari import snowflakes
from hikari.internal import attrs_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    import datetime

    from hikari import traits


class AutoModActionType(int, enums.Enum):
    """The type of an auto-moderation rule action."""

    BLOCK_MESSAGE = 1
    """Block the content of the triggering message."""

    SEND_ALERT_MESSAGE = 2
    """Log the triggering user content to a specified channel."""

    TIMEOUT = 3
    """Timeout the triggering message's author for a specified duration.

    This type can only be set for `KEYWORD` and `MENTION_SPAM` rules.

    Requires the `MODERATE_MEMBERS` permission to use.
    """

    BLOCK_MEMBER_INTERACTION = 4
    """Prevents a member from using text, voice, or other interactions."""


class AutoModEventType(int, enums.Enum):
    """Type of event to check for an auto-moderation rule."""

    MESSAGE_SEND = 1
    """When a member sends or edits a message in the guild."""

    MEMBER_UPDATE = 2
    """When a member updates their guild or user profile."""


class AutoModTriggerType(int, enums.Enum):
    """Type of trigger for an auto-moderation rule."""

    KEYWORD = 1
    """Match message content against a list of keywords and regexes."""

    SPAM = 3
    """Discord's guild anti-spam system."""

    KEYWORD_PRESET = 4
    """Discord's preset keyword triggers."""

    MENTION_SPAM = 5
    """Match messages that exceed the allowed limit of role or user mentions."""

    MEMBER_PROFILE = 6
    """Match user profiles against a list of keywords and regexes."""


class AutoModKeywordPresetType(int, enums.Enum):
    """Discord's KEYWORD_PRESET type."""

    PROFANITY = 1
    """Trigger on words which may be considered forms of swearing or cursing."""

    SEXUAL_CONTENT = 2
    """Trigger on words that refer to explicit behaviour or activity."""

    SLURS = 3
    """Trigger on personal insults and words which "may be considered hate speech"."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class PartialAutoModAction:
    """Base class for an action which is executed when a rule is triggered."""

    type: AutoModActionType = attrs.field()
    """The type of auto-moderation action."""


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModBlockMessage(PartialAutoModAction):
    """Block the content of the triggering message."""


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModSendAlertMessage(PartialAutoModAction):
    """Log the triggering content to a specific channel."""

    channel_id: snowflakes.Snowflake = attrs.field()
    """ID of the channel to log trigger events to."""


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModTimeout(PartialAutoModAction):
    """Timeout the triggering message's author for a specified duration.

    This type can only be set for `KEYWORD` and `MENTION_SPAM` rules.
    """

    duration: datetime.timedelta = attrs.field()
    """The total seconds to timeout the user for (max 2419200 seconds/4 weeks)."""


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModBlockMemberAction(PartialAutoModAction):
    """Prevents a member from using text, voice, or other interactions."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class PartialAutoModTrigger:
    """Base class representing the content a rule triggers on."""

    type: AutoModTriggerType = attrs.field(eq=False, hash=False, repr=False)
    """The type action this triggers."""


@attrs.define(kw_only=True, weakref_slot=False)
class KeywordTrigger(PartialAutoModTrigger):
    """A trigger based on matching message content against a list of keywords."""

    keyword_filter: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=False)
    """The filter strings this trigger checks for."""

    regex_patterns: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=False)
    """The filter regexes this trigger checks for."""

    allow_list: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=False)
    """A sequence of filters which will be exempt from triggering the preset trigger."""


@attrs.define(kw_only=True, weakref_slot=False)
class SpamTrigger(PartialAutoModTrigger):
    """A trigger based on Discord's spam detection."""


@attrs.define(kw_only=True, weakref_slot=False)
class KeywordPresetTrigger(PartialAutoModTrigger):
    """A trigger based on a predefined set of presets provided by Discord."""

    allow_list: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=False)
    """A sequence of filters which will be exempt from triggering the preset trigger."""

    presets: typing.Sequence[AutoModKeywordPresetType | int] = attrs.field(eq=False, hash=False, repr=False)
    """The predefined presets provided by Discord to match against."""


@attrs.define(kw_only=True, weakref_slot=False)
class MentionSpamTrigger(PartialAutoModTrigger):
    """A trigger based on matching mention spams in message content."""

    mention_total_limit: int = attrs.field(eq=False, hash=False, repr=False)
    """Total number of unique role and user mentions allowed per message."""

    mention_raid_protection_enabled: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether to automatically detect mention raids."""


@attrs.define(kw_only=True, weakref_slot=False)
class MemberProfileTrigger(PartialAutoModTrigger):
    """A trigger based on matching user profile content against a list of keywords."""

    keyword_filter: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=False)
    """The filter strings this trigger checks for.

    This supports a wildcard matching strategy which is documented at
    <https://discord.com/developers/docs/resources/auto-moderation#auto-moderation-rule-object-keyword-matching-strategies>.
    """

    regex_patterns: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=False)
    """The filter regexes this trigger checks for."""

    allow_list: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=False)
    """A sequence of filters which will be exempt from triggering the preset trigger."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class AutoModRule(snowflakes.Unique):
    """Auto moderation rule which defines how user content is filtered."""

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attrs.field(eq=True, hash=True, repr=True)
    """The ID of this entity."""

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the guild this rule belongs to."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The rule's name."""

    creator_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the user who originally created this rule."""

    event_type: AutoModEventType = attrs.field(eq=False, hash=False, repr=True)
    """The type of event this rule triggers on."""

    trigger: PartialAutoModTrigger = attrs.field(eq=False, hash=False, repr=False)
    """The content this rule triggers on."""

    actions: typing.Sequence[PartialAutoModAction] = attrs.field(eq=False, hash=False, repr=False)
    """Sequence of the actions which will execute when this rule is triggered."""

    is_enabled: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this rule is enabled."""

    exempt_role_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """A sequence of IDs of (up to 50) roles which aren't effected by this rule."""

    exempt_channel_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """A sequence of IDs of (up to 20) channels which aren't effected by this rule."""
