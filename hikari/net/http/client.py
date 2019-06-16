#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Client mix of all mixin components.
"""
from . import audit_log
from . import channel
from . import emoji
from . import guild
from . import invite
from . import user
from . import webhook


class HTTPClient(
    webhook.base.BaseHTTPClient,
    audit_log.AuditLogMixin,
    channel.ChannelMixin,
    emoji.EmojiMixin,
    guild.GuildMixin,
    invite.InviteMixin,
    user.UserMixin,
    webhook.WebhookMixin,
):
    """
    Combination of all components for API handling logic for the V7 Discord HTTP API.
    """

    __slots__ = ()
