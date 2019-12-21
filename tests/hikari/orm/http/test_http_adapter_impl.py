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
import asyncmock as mock
import pytest

from hikari.internal_utilities import unspecified
from hikari.net import http_api
from hikari.orm import fabric
from hikari.orm.http import http_adapter_impl as _http_adapter_impl
from hikari.orm.state import base_registry
from hikari.orm.models import applications
from hikari.orm.models import audit_logs
from hikari.orm.models import channels
from hikari.orm.models import connections
from hikari.orm.models import gateway_bot
from hikari.orm.models import guilds
from hikari.orm.models import invites
from hikari.orm.models import users
from hikari.orm.models import voices
from hikari.orm.models import webhooks
from tests.hikari import _helpers


# noinspection PyDunderSlots
@pytest.mark.orm
class TestHTTPAdapterImpl:
    @pytest.fixture()
    def fabric_impl(self):
        fabric_impl = fabric.Fabric()

        http_client_impl = mock.MagicMock(spec_set=http_api.HTTPAPIImpl)
        state_registry_impl = mock.MagicMock(spec_set=base_registry.BaseRegistry)
        http_adapter_impl = _http_adapter_impl.HTTPAdapterImpl(fabric_impl)

        fabric_impl.state_registry = state_registry_impl
        fabric_impl.http_api = http_client_impl
        fabric_impl.http_adapter = http_adapter_impl

        return fabric_impl

    @pytest.mark.asyncio
    async def test_gateway_url(self, fabric_impl):
        fabric_impl.http_api.get_gateway = mock.AsyncMock(return_value="wss://some-site.com")

        for _ in range(15):
            assert await fabric_impl.http_adapter.gateway_url == "wss://some-site.com"

        fabric_impl.http_api.get_gateway.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_gateway_bot(self, fabric_impl):
        mock_model = _helpers.mock_model(gateway_bot.GatewayBot)
        mock_payload = mock.MagicMock(spec_set=dict)
        fabric_impl.http_api.get_gateway_bot = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_gateway_bot.return_value = mock_model

        result = await fabric_impl.http_adapter.fetch_gateway_bot()

        assert result is mock_model
        fabric_impl.http_api.get_gateway_bot.assert_called_once_with()
        fabric_impl.state_registry.parse_gateway_bot.assert_called_once_with(mock_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    async def test_fetch_audit_log_with_default_args(self, fabric_impl, guild):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_api.get_guild_audit_log = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_audit_log.return_value = mock_audit_log

        result = await fabric_impl.http_adapter.fetch_audit_log(guild)

        fabric_impl.http_api.get_guild_audit_log.assert_called_once_with(
            guild_id="112233",
            user_id=unspecified.UNSPECIFIED,
            action_type=unspecified.UNSPECIFIED,
            limit=unspecified.UNSPECIFIED,
        )

        fabric_impl.state_registry.parse_audit_log.assert_called_once_with(mock_payload)

        assert result is mock_audit_log

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("user", 334455, users.User, users.OAuth2User)
    async def test_fetch_audit_log_with_optional_args_specified(self, fabric_impl, guild, user):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_api.get_guild_audit_log = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_audit_log.return_value = mock_audit_log

        result = await fabric_impl.http_adapter.fetch_audit_log(
            guild, user=user, action_type=audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE, limit=69,
        )

        fabric_impl.http_api.get_guild_audit_log.assert_called_once_with(
            guild_id="112233",
            user_id="334455",
            action_type=int(audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE),
            limit=69,
        )

        fabric_impl.state_registry.parse_audit_log.assert_called_once_with(mock_payload)

        assert result is mock_audit_log

    @_helpers.todo_implement
    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 112233, channels.Channel)
    async def test_fetch_channel(self, fabric_impl, channel):
        mock_channel = _helpers.mock_model(channels.Channel)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_api.get_channel = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_channel = mock.AsyncMock(return_value=mock_channel)

        result = await fabric_impl.http_adapter.fetch_channel(channel)

        fabric_impl.http_api.get_guild_audit_log.assert_called_once_with(channel_id="112233")
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_payload)
        assert result is mock_channel

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("integration", 115590097100865541, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_delete_integration(self, fabric_impl, guild, integration):
        fabric_impl.http_api.delete_guild_integration = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_integration(guild, integration) is None
        fabric_impl.http_api.delete_guild_integration.assert_called_once_with(guild_id="379953393319542784", integration_id="115590097100865541")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("integration", 115590097100865541, guilds.Guild)
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_sync_guild_integration(self, fabric_impl, guild, integration):
        fabric_impl.http_api.sync_guild_integration = mock.AsyncMock()
        assert await fabric_impl.http_adapter.sync_guild_integration(guild, integration) is None
        fabric_impl.http_api.sync_guild_integration.assert_called_once_with(guild_id="379953393319542784", integration_id="115590097100865541")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_fetch_guild_embed(self, fabric_impl, guild):
        mock_guild_embed_payload = {"channel_id": "379953393319542784"}
        mock_guild_embed = mock.MagicMock(guilds.GuildEmbed)
        fabric_impl.http_api.get_guild_embed = mock.AsyncMock(return_value=mock_guild_embed_payload)
        with _helpers.mock_patch(guilds.GuildEmbed.from_dict, return_value=mock_guild_embed) as mock_guild_embed.from_dict:
            assert await fabric_impl.http_adapter.fetch_guild_embed(guild=guild) is mock_guild_embed
        fabric_impl.http_api.get_guild_embed.assert_called_once_with(guild_id="379953393319542784")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 379953393319542784, guilds.Guild)
    async def test_modify_guild_embed(self, fabric_impl, guild):
        mock_guild_embed = mock.MagicMock(guilds.GuildEmbed)
        fabric_impl.http_api.modify_guild_embed = mock.AsyncMock()
        assert (
            await fabric_impl.http_adapter.modify_guild_embed(guild, mock_guild_embed, reason="OK") is None
        )
        fabric_impl.http_api.modify_guild_embed.assert_called_once_with(
            guild_id="379953393319542784", embed=mock_guild_embed.to_dict(), reason="OK"
        )

    @_helpers.todo_implement
    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    async def test_fetch_guild_vanity_url(self, fabric_impl, guild):
        mock_vanity_url = "this-is-not-a-vanity-url"
        fabric_impl.http_api.get_guild_vanity_url = mock.AsyncMock(return_value=mock_vanity_url)
        assert await fabric_impl.http_adapter.fetch_guild_vanity_url(guild) is mock_vanity_url
        fabric_impl.http_api.get_guild_vanity_url.assert_called_once_with(guild_id="112233")

    @_helpers.parametrize_valid_id_formats_for_models("guild", 574921006817476608, guilds.Guild)
    def test_fetch_guild_widget_image(self, fabric_impl, guild):
        mock_guild_widget = "https://discordapp.com/api/v7/guilds/574921006817476608/widget.png?style=banner2"
        fabric_impl.http_api.get_guild_widget_image.return_value = mock_guild_widget
        assert fabric_impl.http_adapter.fetch_guild_widget_image(guild, style="banner2") is mock_guild_widget
        fabric_impl.http_api.get_guild_widget_image.assert_called_once_with(
            guild_id="574921006817476608", style="banner2"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invite",
        [
            "gfawxcz",
            _helpers.mock_model(invites.Invite, code="gfawxcz", __str__=invites.Invite.__str__),
            _helpers.mock_model(invites.InviteWithMetadata, code="gfawxcz", __str__=invites.InviteWithMetadata.__str__),
        ],
    )
    async def test_fetch_invite(self, fabric_impl, invite):
        mock_invite_payload = {
            "code": "discord-api",
            "guild": {
                "id": "81384788765712384",
                "name": "Discord API",
                "splash": None,
                "banner": None,
                "description": None,
                "icon": None,
                "features": [],
                "verification_level": 3,
                "vanity_url_code": "discord-api",
            },
            "channel": {"id": "242538455840718849", "name": "general", "type": 0},
            "approximate_member_count": 49240,
            "approximate_presence_count": 17993,
        }
        mock_invite = mock.MagicMock(invites.Invite)
        fabric_impl.http_api.get_invite = mock.AsyncMock(return_value=mock_invite_payload)
        fabric_impl.state_registry.parse_invite.return_value = mock_invite
        assert await fabric_impl.http_adapter.fetch_invite(invite, with_counts=True) is mock_invite
        fabric_impl.http_api.get_invite.assert_called_once_with(invite_code="gfawxcz", with_counts=True)
        fabric_impl.state_registry.parse_invite.assert_called_once_with(mock_invite_payload)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invite",
        [
            "gfawxcz",
            _helpers.mock_model(invites.Invite, code="gfawxcz", __str__=invites.Invite.__str__),
            _helpers.mock_model(invites.InviteWithMetadata, code="gfawxcz", __str__=invites.InviteWithMetadata.__str__),
        ],
    )
    async def test_delete_invite(self, fabric_impl, invite):
        fabric_impl.http_api.delete_invite = mock.AsyncMock()
        await fabric_impl.http_adapter.delete_invite(invite)
        fabric_impl.http_api.delete_invite.assert_called_once_with(invite_code="gfawxcz")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 33333333, users.User)
    async def test_fetch_user(self, fabric_impl, user):
        mock_user = mock.MagicMock(users.User)
        fabric_impl.http_api.get_user = mock.AsyncMock()
        fabric_impl.state_registry.parse_user.return_value = mock_user
        assert await fabric_impl.http_adapter.fetch_user(user) is mock_user
        fabric_impl.http_api.get_user.assert_called_once_with(user_id="33333333")

    @pytest.mark.asyncio
    async def test_fetch_application_info(self, fabric_impl):
        mock_application_info_payload = {}
        mock_application_info = mock.MagicMock(applications.Application)
        fabric_impl.http_api.get_current_application_info = mock.AsyncMock(return_value=mock_application_info_payload)
        fabric_impl.state_registry.parse_application.return_value = mock_application_info
        assert await fabric_impl.http_adapter.fetch_application_info() is mock_application_info
        fabric_impl.http_api.get_current_application_info.assert_called_once()
        fabric_impl.state_registry.parse_application.assert_called_once_with(mock_application_info_payload)

    @pytest.mark.asyncio
    async def test_fetch_me(self, fabric_impl):
        mock_user_payload = {
            "id": "45465632334123",
            "username": "Nekocord",
            "avatar": None,
            "discriminator": "7280",
            "bot": True,
            "email": None,
            "verified": True,
            "locale": "en-US",
            "mfa_enabled": True,
            "flags": 0,
        }
        mock_user = mock.MagicMock(users.OAuth2User)
        fabric_impl.http_api.get_current_user = mock.AsyncMock(return_value=mock_user_payload)
        fabric_impl.state_registry.parse_application_user.return_value = mock_user
        assert await fabric_impl.http_adapter.fetch_me() is mock_user
        fabric_impl.http_api.get_current_user.assert_called_once()
        fabric_impl.state_registry.parse_application_user.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_update_me_without_optionals(self, fabric_impl):
        mock_user_payload = {
            "id": "45465632334123",
            "username": "Nekocord",
            "avatar": None,
            "discriminator": "7280",
            "token": "odsk342SDOIJ.23IJDOWoijk2",
            "bot": True,
            "email": None,
            "verified": True,
            "locale": "en-US",
            "mfa_enabled": True,
            "flags": 0,
        }
        fabric_impl.http_api.modify_current_user = mock.AsyncMock(return_value=mock_user_payload)
        await fabric_impl.http_adapter.update_me()
        fabric_impl.http_api.modify_current_user.assert_called_once_with(
            username=unspecified.UNSPECIFIED, avatar=unspecified.UNSPECIFIED
        )
        fabric_impl.state_registry.parse_user.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_update_me_with_all_optionals(self, fabric_impl):
        mock_user_payload = {
            "id": "45465632334123",
            "username": "Nekocord",
            "avatar": "f416049374de081ea5ff47d1e8328f74",
            "discriminator": "7280",
            "token": "odsk342SDOIJ.23IJDOWoijk2",
            "bot": True,
            "email": None,
            "verified": True,
            "locale": "en-US",
            "mfa_enabled": True,
            "flags": 0,
        }
        fabric_impl.http_api.modify_current_user = mock.AsyncMock(return_value=mock_user_payload)
        await fabric_impl.http_adapter.update_me(avatar="f416049374de081ea5ff47d1e8328f74", username="OWO")
        fabric_impl.http_api.modify_current_user.assert_called_once_with(
            avatar="f416049374de081ea5ff47d1e8328f74", username="OWO"
        )
        fabric_impl.state_registry.parse_user.assert_called_once_with(mock_user_payload)

    @pytest.mark.asyncio
    async def test_fetch_my_connections(self, fabric_impl):
        mock_user_connections_payload = {
            "type": "twitch",
            "id": "534231",
            "name": "neko_speeding",
            "visibility": 0,
            "friend_sync": False,
            "show_activity": True,
            "verified": True,
        }
        mock_user_connections = mock.MagicMock(connections.Connection)
        fabric_impl.http_api.get_current_user_connections = mock.AsyncMock(return_value=[mock_user_connections_payload])
        fabric_impl.state_registry.parse_connection.return_value = mock_user_connections
        assert await fabric_impl.http_adapter.fetch_my_connections() == [mock_user_connections]
        fabric_impl.http_api.get_current_user_connections.assert_called_once()
        fabric_impl.state_registry.parse_connection.assert_called_once_with(mock_user_connections_payload)

    @_helpers.todo_implement
    def test_fetch_my_guilds(self):
        raise NotImplementedError

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 190007233919057920, guilds.Guild)
    async def test_leave_guild_when_not_cached(self, fabric_impl, guild):
        fabric_impl.http_api.leave_guild = mock.AsyncMock()
        await fabric_impl.http_adapter.leave_guild(guild)
        fabric_impl.http_api.leave_guild.assert_called_once_with(guild_id="190007233919057920")

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("recipient", 33333333, users.User)
    async def test_create_dm_channel(self, fabric_impl, recipient):
        mock_dm_payload = {"id": 3323232, "type": 2, "last_message_id": "3343820033257021450", "recipients": []}
        mock_dm = mock.MagicMock(channels.DMChannel)
        fabric_impl.http_api.create_dm = mock.AsyncMock(return_value=mock_dm_payload)
        fabric_impl.state_registry.parse_channel.return_value = mock_dm
        assert await fabric_impl.http_adapter.create_dm_channel(recipient) is mock_dm
        fabric_impl.http_api.create_dm.assert_called_once_with(recipient_id="33333333")
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_dm_payload)

    @pytest.mark.asyncio
    async def test_fetch_voice_regions(self, fabric_impl):
        mock_voice_region_payload = {
            "id": "London",
            "name": "London",
            "vip": True,
            "optimal": True,
            "deprecated": True,
            "custom": False,
        }
        mock_voice_region = mock.MagicMock(voices.VoiceRegion)
        fabric_impl.http_api.list_voice_regions = mock.AsyncMock(return_value=[mock_voice_region_payload])
        with _helpers.mock_patch(voices.VoiceRegion) as mock_voice_region:
            voices.VoiceRegion.return_value = mock_voice_region
            assert await fabric_impl.http_adapter.fetch_voice_regions() == (mock_voice_region,)
        fabric_impl.http_api.list_voice_regions.assert_called()
        mock_voice_region.assert_called_once_with(mock_voice_region_payload)

    @pytest.fixture
    def mock_webhook_payload(self):
        return {"id": "4325321123653"}

    @pytest.fixture
    def mock_webhook(self):
        return _helpers.mock_model(webhooks.Webhook)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.Channel)
    async def test_create_webhook_with_all_optionals(self, fabric_impl, mock_webhook_payload, mock_webhook, channel):
        fabric_impl.http_api.create_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook
        assert (
            await fabric_impl.http_adapter.create_webhook(channel, "OK", avatar=b"239isadjiu83e24io", reason="A reason")
            is mock_webhook
        )
        fabric_impl.http_api.create_webhook.assert_called_once_with(
            channel_id="33333333", name="OK", avatar=b"239isadjiu83e24io", reason="A reason",
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.Channel)
    async def test_create_webhook_without_optionals(self, fabric_impl, mock_webhook_payload, mock_webhook, channel):
        fabric_impl.http_api.create_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook
        assert await fabric_impl.http_adapter.create_webhook(channel, "OK") is mock_webhook
        fabric_impl.http_api.create_webhook.assert_called_once_with(
            channel_id="33333333", name="OK", avatar=unspecified.UNSPECIFIED, reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("channel", 33333333, channels.Channel)
    async def test_fetch_channel_webhooks(self, fabric_impl, mock_webhook_payload, mock_webhook, channel):
        fabric_impl.http_api.get_channel_webhooks = mock.AsyncMock(return_value=[mock_webhook_payload])
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook
        assert await fabric_impl.http_adapter.fetch_channel_webhooks(channel) == (mock_webhook,)
        fabric_impl.http_api.get_channel_webhooks.assert_called_once_with(channel_id="33333333")
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("guild", 878787, guilds.Guild)
    async def test_fetch_guild_webhooks(self, fabric_impl, mock_webhook_payload, mock_webhook, guild):
        fabric_impl.http_api.get_guild_webhooks = mock.AsyncMock(return_value=[mock_webhook_payload])
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert await fabric_impl.http_adapter.fetch_guild_webhooks(guild) == (mock_webhook,)
        fabric_impl.http_api.get_guild_webhooks.assert_called_once_with(guild_id="878787")
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 878787, webhooks.Webhook)
    async def test_fetch_webhook(self, fabric_impl, mock_webhook_payload, mock_webhook, webhook):
        fabric_impl.http_api.get_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert await fabric_impl.http_adapter.fetch_webhook(webhook) is mock_webhook
        fabric_impl.http_api.get_webhook.assert_called_once_with(webhook_id="878787")
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 646464, webhooks.Webhook)
    async def test_update_webhook_when_all_unspecified(self, fabric_impl, mock_webhook_payload, mock_webhook, webhook):
        fabric_impl.http_api.modify_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert await fabric_impl.http_adapter.update_webhook(webhook) is mock_webhook
        fabric_impl.http_api.modify_webhook.assert_called_once_with(
            webhook_id="646464",
            name=unspecified.UNSPECIFIED,
            avatar=unspecified.UNSPECIFIED,
            channel_id=unspecified.UNSPECIFIED,
            reason=unspecified.UNSPECIFIED,
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 646464, webhooks.Webhook)
    async def test_update_webhook_when_filled(self, fabric_impl, mock_webhook_payload, mock_webhook, webhook):
        mock_channel = _helpers.mock_model(channels.GuildTextChannel, id=42)
        fabric_impl.http_api.modify_webhook = mock.AsyncMock(return_value=mock_webhook_payload)
        fabric_impl.state_registry.parse_webhook.return_value = mock_webhook

        assert (
            await fabric_impl.http_adapter.update_webhook(
                webhook, name="Nekohook", avatar=b"dookx0o2", channel=mock_channel, reason="We need more cats."
            )
            is mock_webhook
        )
        fabric_impl.http_api.modify_webhook.assert_called_once_with(
            webhook_id="646464", name="Nekohook", avatar=b"dookx0o2", channel_id="42", reason="We need more cats.",
        )
        fabric_impl.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("webhook", 33331111, webhooks.Webhook)
    async def test_delete_webhook(self, fabric_impl, webhook):
        fabric_impl.http_api.delete_webhook = mock.AsyncMock()
        assert await fabric_impl.http_adapter.delete_webhook(webhook) is None
        fabric_impl.http_api.delete_webhook.assert_called_once_with(webhook_id="33331111")
