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
"""Events that fire for auto-moderation related changes."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "AutoModEvent",
    "AutoModRuleCreateEvent",
    "AutoModRuleUpdateEvent",
    "AutoModRuleDeleteEvent",
    "AutoModActionExecutionEvent",
)

import abc
import typing

import attr

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import auto_mod
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.AUTO_MODERATION_CONFIGURATION, intents.Intents.AUTO_MODERATION_EXECUTION)
class AutoModEvent(shard_events.ShardEvent, abc.ABC):
    """Base class for auto-moderation gateway events."""

    __slots__: typing.Sequence[str] = ()


@base_events.requires_intents(intents.Intents.AUTO_MODERATION_CONFIGURATION)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class AutoModRuleCreateEvent(AutoModEvent):
    """Event that's fired when an auto-moderation rule is created."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    rule: auto_mod.AutoModRule = attr.field()
    """Object of the auto-moderation rule which was created."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from BaseEvent>>.
        return self.rule.app


@base_events.requires_intents(intents.Intents.AUTO_MODERATION_CONFIGURATION)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class AutoModRuleUpdateEvent(AutoModEvent):
    """Event that's fired when an auto-moderation rule is updated."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    rule: auto_mod.AutoModRule = attr.field()
    """Object of the auto-moderation rule which was updated."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from BaseEvent>>.
        return self.rule.app


@base_events.requires_intents(intents.Intents.AUTO_MODERATION_CONFIGURATION)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class AutoModRuleDeleteEvent(AutoModEvent):
    """Event that's fired when an auto-moderation rule is deleted."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    rule: auto_mod.AutoModRule = attr.field()
    """Object of the auto-moderation rule which was deleted."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from BaseEvent>>.
        return self.rule.app


@base_events.requires_intents(intents.Intents.AUTO_MODERATION_EXECUTION)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class AutoModActionExecutionEvent(AutoModEvent):
    """Event that's fired when an auto-mod action is executed."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attr.field(repr=True)
    """ID of the guild this action was executed in."""

    action: auto_mod.PartialAutoModAction = attr.field(repr=False)
    """Object of the action which was executed."""

    rule_id: snowflakes.Snowflake = attr.field()
    """ID of the rule which was triggered."""

    rule_trigger_type: typing.Union[int, auto_mod.AutoModTriggerType] = attr.field(repr=False)
    """Type of the rule which was triggered."""

    user_id: snowflakes.Snowflake = attr.field(repr=False)
    """ID of the user who generated the context which triggered this."""

    channel_id: typing.Optional[snowflakes.Snowflake] = attr.field(repr=False)
    """ID of the channel the matching context was sent to.

    This will be `builtins.None` if the message was blocked by auto-moderation
    of the matched content wasn't in a channel.
    """

    message_id: typing.Optional[snowflakes.Snowflake] = attr.field(repr=False)
    """ID of the message the matching context was sent in.

    This will be `builtins.None` if the message was blocked by auto-moderation
    or the matched content wasn't in a message.
    """

    alert_system_message_id: typing.Optional[snowflakes.Snowflake] = attr.field(repr=False)
    """ID of any system auto-moderation messages posted as a result of this action.

    This will only be provided for `SEND_ALERT_MESSAGE` actions.
    """

    content: typing.Optional[str] = attr.field(repr=False)
    """The user generated content which matched this rule.

    This will only be provided if the `MESSAGE_CONTENT` intent has
    been declared.
    """

    matched_keyword: typing.Optional[str] = attr.field(repr=False)
    """The word or phrase configured in the rule which was triggered, if it's a keyword trigger."""

    matched_content: typing.Optional[str] = attr.field(repr=False)
    """The substring in content which triggered the rule.

    This will only be provided if the `MESSAGE_CONTENT` intent has
    been declared and this is a keyword or keyword preset trigger.
    """
