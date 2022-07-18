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
"""Application and entities that are used to describe guild auto moderation on Discord."""

import typing
import attr

from hikari import snowflakes
from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import traits


class AutoModerationTriggerType(int, enums.Enum):
    """Enum of the Auto Moderation trigger types."""

    KEYWORD = 1
    """Check if content contains words from a user defined list of keywords."""

    HARMFUL_LINK = 2
    """Check if content contains any harmful links."""

    SPAM = 3
    """Check if content represents generic spam."""

    KEYWORD_PRESET = 4
    """Check if content contains words from internal pre-defined wordsets."""


class KeywordPresetType(int, enums.Enum):
    """Enum of the Auto Moderation keyword preset types."""

    PROFANITY = 1
    """Words that may be considered forms of swearing or cursing."""

    SEXUAL_CONTENT = 2
    """Words that refer to sexually explicit behavior or activity."""

    SLURS = 3
    """Personal insults or words that may be considered hate speech."""



class AutoModerationEventType(int, enums.Enum):
    """Enum of the Auto Moderation event types."""

    MESSAGE_SEND = 1
    """When a member sends or edits a message in the guild."""


class AutoModerationActionType(int, enums.Enum):
    """Enum of the Auto Moderation action types."""

    BLOCK_MESSAGE = 1
    """Blocks the content of a message according to the rule."""

    SEND_ALERT_MESSAGE = 2
    """Logs user content to a specified channel."""

    TIMEOUT = 3
    """Timeout user for a specified duration."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class AutoModerationAction:
    """Represents an action which will execute whenever an auto moderation rule is triggered."""

    type: AutoModerationActionType = attr.field(hash=True, repr=False)
    """Type of this auto moderation action."""

    channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(hash=False, repr=True)
    """ID of channel to which user content should be logged

    This field is associated with the `hikari.AutoModerationActionType.SEND_ALERT_MESSAGE` type.
    """

    duration_seconds: typing.Optional[int] = attr.field(hash=False, repr=True)
    """Timeout duration in seconds

    Maximum of 2419200 seconds (4 weeks)

    This field is associated with the `hikari.AutoModerationActionType.TIMEOUT` type.
    """


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class AutoModeration(snowflakes.Unique):
    """Base class for auto moderation."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """ID of this auto moderation rule."""

    guild_id: snowflakes.Snowflake = attr.field(hash=False, repr=True)
    """ID of the guild which this auto moderation rule belongs to."""

    name: str = attr.field(hash=False, repr=True)
    """Name of this auto moderation rule."""

    creator_id: snowflakes.Snowflake = attr.field(hash=False, repr=True)
    """ID of the user that created this auto moderation rule."""

    event_type: AutoModerationEventType = attr.field(hash=False, repr=True)
    """Event type of this auto moderation rule."""

    trigger_type: AutoModerationTriggerType = attr.field(hash=False, repr=True)
    """Trigger type of this auto moderation rule."""
    
    keyword_filter: typing.Optional[typing.List[str]] = attr.field(factory=list, hash=False, repr=False)
    """List of substrings which will be searched for in content.
    
    This field is associated with the `hikari.AutoModerationTriggerType.KEYWORD` type.
    """

    presets: typing.List[KeywordPresetType] = attr.field(factory=list, hash=False, repr=False)
    """List of the internally pre-defined wordsets which will be searched for in content.
    
    This field is associated with the `hikari.AutoModerationTriggerType.KEYWORD_PRESET` type.
    """

    actions: typing.List[AutoModerationAction]

    enabled: bool = attr.field(hash=False, repr=False)
    """Whether the rule is enabled or not."""

    exempt_roles: typing.List[snowflakes.Snowflake] = attr.field(factory=list, hash=False, repr=False)
    """The role IDs that should not be affected by this auto moderation rule (Maximum of 20)."""

    exempt_channels: typing.List[snowflakes.Snowflake] = attr.field(factory=list, hash=False, repr=False)
    """The channel IDs that should not be affected by this auto moderation rule (Maximum of 50)."""

