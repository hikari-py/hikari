#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Event handling logic for more info."""

from __future__ import annotations

__all__ = ["EventManagerImpl"]

import typing

from hikari.impl import event_manager_core

if typing.TYPE_CHECKING:
    from hikari.net import gateway
    from hikari.utilities import data_binding


class EventManagerImpl(event_manager_core.EventManagerCore):
    """Provides event handling logic for Discord events."""

    async def on_connect(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """Handle connection events.

        This is a synthetic event produced by the gateway implementation in
        Hikari.
        """

    async def on_disconnect(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """Handle disconnection events.

        This is a synthetic event produced by the gateway implementation in
        Hikari.
        """

    async def on_ready(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#ready for more info."""

    async def on_resumed(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#resumed for more info."""

    async def on_channel_create(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-create for more info."""

    async def on_channel_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-update for more info."""

    async def on_channel_delete(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-delete for more info."""

    async def on_channel_pins_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-pins-update for more info."""

    async def on_guild_create(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-create for more info."""

    async def on_guild_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-update for more info."""

    async def on_guild_delete(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-delete for more info."""

    async def on_guild_ban_add(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-add for more info."""

    async def on_guild_ban_remove(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-remove for more info."""

    async def on_guild_emojis_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-emojis-update for more info."""

    async def on_guild_integrations_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-integrations-update for more info."""

    async def on_guild_member_add(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-add for more info."""

    async def on_guild_member_remove(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-remove for more info."""

    async def on_guild_member_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-update for more info."""

    async def on_guild_members_chunk(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-members-chunk for more info."""

    async def on_guild_role_create(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-create for more info."""

    async def on_guild_role_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-update for more info."""

    async def on_guild_role_delete(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-delete for more info."""

    async def on_invite_create(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-create for more info."""

    async def on_invite_delete(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-delete for more info."""

    async def on_message_create(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-create for more info."""

    async def on_message_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-update for more info."""

    async def on_message_delete(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete for more info."""

    async def on_message_delete_bulk(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete-bulk for more info."""

    async def on_message_reaction_add(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-add for more info."""

    async def on_message_reaction_remove(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove for more info."""

    async def on_message_reaction_remove_all(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-all for more info."""

    async def on_message_reaction_remove_emoji(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-emoji for more info."""

    async def on_presence_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#presence-update for more info."""

    async def on_typing_start(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#typing-start for more info."""

    async def on_user_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#user-update for more info."""

    async def on_voice_state_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-state-update for more info."""

    async def on_voice_server_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-server-update for more info."""

    async def on_webhooks_update(self, shard: gateway.Gateway, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#webhooks-update for more info."""
