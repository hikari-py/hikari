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
import contextlib
import datetime

import mock
import pytest

from hikari import application
from hikari.models import audit_logs
from hikari.models import channels
from hikari.models import guilds
from hikari.models import users
from hikari.models import webhooks


@pytest.fixture()
def mock_app():
    return mock.MagicMock(application.Application)


class TestAuditLogChangeKey:
    def test___str__(self):
        assert str(audit_logs.AuditLogChangeKey.ID) == "ID"

    def test___repr__(self):
        assert repr(audit_logs.AuditLogChangeKey.ID) == "ID"


def test__deserialize_seconds_timedelta():
    assert audit_logs._deserialize_seconds_timedelta(30) == datetime.timedelta(seconds=30)


def test__deserialize_partial_roles(mock_app):
    test_role_payloads = [
        {"id": "24", "name": "roleA", "hoisted": True},
        {"id": "48", "name": "roleA", "hoisted": True},
    ]
    mock_role_objs = [mock.MagicMock(guilds.PartialGuildRole, id=24), mock.MagicMock(guilds.PartialGuildRole, id=48)]
    with mock.patch.object(guilds.PartialGuildRole, "deserialize", side_effect=mock_role_objs):
        result = audit_logs._deserialize_partial_roles(test_role_payloads, app=mock_app)
        assert result == {24: mock_role_objs[0], 48: mock_role_objs[1]}
        guilds.PartialGuildRole.deserialize.assert_has_calls(
            [mock.call(test_role_payloads[0], app=mock_app), mock.call(test_role_payloads[1], app=mock_app),]
        )


def test__deserialize_day_timedelta():
    assert audit_logs._deserialize_day_timedelta("4") == datetime.timedelta(days=4)


def test__deserialize_overwrites(mock_app):
    test_overwrite_payloads = [{"id": "24", "allow": 21, "deny": 0}, {"id": "48", "deny": 42, "allow": 0}]
    mock_overwrite_objs = [
        mock.MagicMock(guilds.PartialGuildRole, id=24),
        mock.MagicMock(guilds.PartialGuildRole, id=48),
    ]
    with mock.patch.object(channels.PermissionOverwrite, "deserialize", side_effect=mock_overwrite_objs):
        result = audit_logs._deserialize_overwrites(test_overwrite_payloads, app=mock_app)
        assert result == {24: mock_overwrite_objs[0], 48: mock_overwrite_objs[1]}
        channels.PermissionOverwrite.deserialize.assert_has_calls(
            [mock.call(test_overwrite_payloads[0], app=mock_app), mock.call(test_overwrite_payloads[1], app=mock_app),]
        )


def test__deserialize_max_uses_returns_int():
    assert audit_logs._deserialize_max_uses(120) == 120


def test__deserialize_max_uses_returns_infinity():
    assert audit_logs._deserialize_max_uses(0) == float("inf")


def test__deserialize_max_age_returns_timedelta():
    assert audit_logs._deserialize_max_age(120) == datetime.timedelta(seconds=120)


def test__deserialize_max_age_returns_null():
    assert audit_logs._deserialize_max_age(0) is None


@pytest.fixture()
def test_audit_log_change_payload():
    return {
        "key": "$add",
        "old_value": [{"id": "568651298858074123", "name": "Casual"}],
        "new_value": [{"id": "123123123312312", "name": "aRole"}],
    }


class TestAuditLogChange:
    def test_deserialize_with_known_component_less_converter_and_values(self, mock_app):
        test_audit_log_change_payload = {"key": "rate_limit_per_user", "old_value": "0", "new_value": "60"}
        mock_role_zero = mock.MagicMock(guilds.PartialGuildRole, id=123123123312312)
        mock_role_one = mock.MagicMock(guilds.PartialGuildRole, id=568651298858074123)
        with mock.patch.object(guilds.PartialGuildRole, "deserialize", side_effect=[mock_role_zero, mock_role_one]):
            audit_log_change_obj = audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload, app=mock_app)
        assert audit_log_change_obj._app is mock_app
        assert audit_log_change_obj.key is audit_logs.AuditLogChangeKey.RATE_LIMIT_PER_USER
        assert audit_log_change_obj.old_value == datetime.timedelta(seconds=0)
        assert audit_log_change_obj.new_value == datetime.timedelta(seconds=60)

    def test_deserialize_with_known_component_full_converter_and_values(self, test_audit_log_change_payload, mock_app):
        mock_role_zero = mock.MagicMock(guilds.PartialGuildRole, id=123123123312312)
        mock_role_one = mock.MagicMock(guilds.PartialGuildRole, id=568651298858074123)
        with mock.patch.object(guilds.PartialGuildRole, "deserialize", side_effect=[mock_role_zero, mock_role_one]):
            audit_log_change_obj = audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload, app=mock_app)
            guilds.PartialGuildRole.deserialize.assert_has_calls(
                [
                    mock.call({"id": "123123123312312", "name": "aRole"}, app=mock_app),
                    mock.call({"id": "568651298858074123", "name": "Casual"}, app=mock_app),
                ]
            )
        assert audit_log_change_obj._app is mock_app
        assert audit_log_change_obj.key is audit_logs.AuditLogChangeKey.ADD_ROLE_TO_MEMBER
        assert audit_log_change_obj.old_value == {568651298858074123: mock_role_one}
        assert audit_log_change_obj.new_value == {123123123312312: mock_role_zero}

    def test_deserialize_with_known_component_full_converter_and_no_values(
        self, test_audit_log_change_payload, mock_app
    ):
        test_audit_log_change_payload = {"key": "$add"}
        with mock.patch.object(guilds.PartialGuildRole, "deserialize"):
            audit_log_change_obj = audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload, app=mock_app)
            guilds.PartialGuildRole.deserialize.assert_not_called()
        assert audit_log_change_obj._app is mock_app
        assert audit_log_change_obj.key is audit_logs.AuditLogChangeKey.ADD_ROLE_TO_MEMBER
        assert audit_log_change_obj.old_value is None
        assert audit_log_change_obj.new_value is None

    def test_deserialize_with_known_component_less_converter_and_no_values(
        self, test_audit_log_change_payload, mock_app
    ):
        test_audit_log_change_payload = {"key": "rate_limit_per_user"}
        with mock.patch.object(guilds.PartialGuildRole, "deserialize"):
            audit_log_change_obj = audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload, app=mock_app)
            guilds.PartialGuildRole.deserialize.assert_not_called()
        assert audit_log_change_obj._app is mock_app
        assert audit_log_change_obj.key is audit_logs.AuditLogChangeKey.RATE_LIMIT_PER_USER
        assert audit_log_change_obj.old_value is None
        assert audit_log_change_obj.new_value is None

    def test_deserialize_with_unknown_converter_and_values(self, test_audit_log_change_payload, mock_app):
        test_audit_log_change_payload["key"] = "aUnknownKey"
        audit_log_change_obj = audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload, app=mock_app)
        assert audit_log_change_obj._app is mock_app
        assert audit_log_change_obj.key == "aUnknownKey"
        assert audit_log_change_obj.old_value == test_audit_log_change_payload["old_value"]
        assert audit_log_change_obj.new_value == test_audit_log_change_payload["new_value"]

    def test_deserialize_with_unknown_converter_and_no_values(self, test_audit_log_change_payload, mock_app):
        test_audit_log_change_payload["key"] = "aUnknownKey"
        del test_audit_log_change_payload["old_value"]
        del test_audit_log_change_payload["new_value"]
        audit_log_change_obj = audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload, app=mock_app)
        assert audit_log_change_obj._app is mock_app
        assert audit_log_change_obj.key == "aUnknownKey"
        assert audit_log_change_obj.old_value is None
        assert audit_log_change_obj.new_value is None


class TestChannelOverwriteEntryInfo:
    @pytest.fixture()
    def test_overwrite_info_payload(self):
        return {"id": "123123123", "type": "role", "role_name": "aRole"}

    def test_deserialize(self, test_overwrite_info_payload, mock_app):
        overwrite_entry_info = audit_logs.ChannelOverwriteEntryInfo.deserialize(
            test_overwrite_info_payload, app=mock_app
        )
        assert overwrite_entry_info.id == 123123123
        assert overwrite_entry_info.type is channels.PermissionOverwriteType.ROLE
        assert overwrite_entry_info.role_name == "aRole"


class TestMessagePinEntryInfo:
    @pytest.fixture()
    def test_message_pin_info_payload(self):
        return {
            "channel_id": "123123123",
            "message_id": "69696969",
        }

    def test_deserialize(self, test_message_pin_info_payload, mock_app):
        message_pin_info_obj = audit_logs.MessagePinEntryInfo.deserialize(test_message_pin_info_payload, app=mock_app)
        assert message_pin_info_obj.channel_id == 123123123
        assert message_pin_info_obj.message_id == 69696969


class TestMemberPruneEntryInfo:
    @pytest.fixture()
    def test_member_prune_info_payload(self):
        return {
            "delete_member_days": "7",
            "members_removed": "1",
        }

    def test_deserialize(self, test_member_prune_info_payload, mock_app):
        member_prune_info_obj = audit_logs.MemberPruneEntryInfo.deserialize(
            test_member_prune_info_payload, app=mock_app
        )
        assert member_prune_info_obj.delete_member_days == datetime.timedelta(days=7)
        assert member_prune_info_obj.members_removed == 1


class TestMessageDeleteEntryInfo:
    @pytest.fixture()
    def test_message_delete_info_payload(self):
        return {"count": "42", "channel_id": "4206942069"}

    def test_deserialize(self, test_message_delete_info_payload, mock_app):
        message_delete_entry_info = audit_logs.MessageDeleteEntryInfo.deserialize(
            test_message_delete_info_payload, app=mock_app
        )
        assert message_delete_entry_info.channel_id == 4206942069


class TestMessageBulkDeleteEntryInfo:
    @pytest.fixture()
    def test_message_bulk_delete_info_payload(self):
        return {"count": "42"}

    def test_deserialize(self, test_message_bulk_delete_info_payload, mock_app):
        message_bulk_delete_entry_info = audit_logs.MessageBulkDeleteEntryInfo.deserialize(
            test_message_bulk_delete_info_payload, app=mock_app
        )
        assert message_bulk_delete_entry_info.count == 42


class TestMemberDisconnectEntryInfo:
    @pytest.fixture()
    def test_member_disconnect_info_payload(self):
        return {"count": "42"}

    def test_deserialize(self, test_member_disconnect_info_payload, mock_app):
        member_disconnect_entry_info = audit_logs.MemberDisconnectEntryInfo.deserialize(
            test_member_disconnect_info_payload, app=mock_app
        )
        assert member_disconnect_entry_info.count == 42


class TestMemberMoveEntryInfo:
    @pytest.fixture()
    def test_member_move_info_payload(self):
        return {"count": "42", "channel_id": "22222222"}

    def test_deserialize(self, test_member_move_info_payload, mock_app):
        member_move_entry_info = audit_logs.MemberMoveEntryInfo.deserialize(test_member_move_info_payload, app=mock_app)
        assert member_move_entry_info.channel_id == 22222222


class TestUnrecognisedAuditLogEntryInfo:
    @pytest.fixture()
    def test_unrecognised_audit_log_entry(self):
        return {"count": "5412", "action": "nyaa'd"}

    def test_deserialize(self, test_unrecognised_audit_log_entry, mock_app):
        unrecognised_info_obj = audit_logs.UnrecognisedAuditLogEntryInfo.deserialize(
            test_unrecognised_audit_log_entry, app=mock_app
        )
        assert unrecognised_info_obj.count == "5412"
        assert unrecognised_info_obj.action == "nyaa'd"


@pytest.mark.parametrize(
    ("type_", "expected_entity"),
    [
        (13, audit_logs.ChannelOverwriteEntryInfo),
        (14, audit_logs.ChannelOverwriteEntryInfo),
        (15, audit_logs.ChannelOverwriteEntryInfo),
        (74, audit_logs.MessagePinEntryInfo),
        (75, audit_logs.MessagePinEntryInfo),
        (21, audit_logs.MemberPruneEntryInfo),
        (72, audit_logs.MessageDeleteEntryInfo),
        (73, audit_logs.MessageBulkDeleteEntryInfo),
        (27, audit_logs.MemberDisconnectEntryInfo),
        (26, audit_logs.MemberMoveEntryInfo),
    ],
)
def test_get_audit_log_entry_info_entity(type_, expected_entity):
    assert audit_logs.get_entry_info_entity(type_) is expected_entity


@pytest.fixture()
def test_audit_log_option_payload():
    return {
        "id": "115590097100865541",
        "type": "member",
    }


@pytest.fixture()
def test_audit_log_entry_payload(test_audit_log_change_payload, test_audit_log_option_payload):
    return {
        "action_type": 14,
        "changes": [test_audit_log_change_payload],
        "id": "694026906592477214",
        "options": test_audit_log_option_payload,
        "target_id": "115590097100865541",
        "user_id": "560984860634644482",
        "reason": "An artificial insanity.",
    }


class TestAuditLogEntry:
    def test_deserialize_with_options_and_target_id_and_known_type(
        self, test_audit_log_entry_payload, test_audit_log_option_payload, test_audit_log_change_payload, mock_app,
    ):
        audit_log_entry_obj = audit_logs.AuditLogEntry.deserialize(test_audit_log_entry_payload, app=mock_app)
        assert audit_log_entry_obj._app is mock_app
        assert audit_log_entry_obj.changes == [audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload)]
        assert audit_log_entry_obj.options == audit_logs.ChannelOverwriteEntryInfo.deserialize(
            test_audit_log_option_payload
        )
        assert audit_log_entry_obj.options._app is mock_app
        assert audit_log_entry_obj.target_id == 115590097100865541
        assert audit_log_entry_obj.user_id == 560984860634644482
        assert audit_log_entry_obj.id == 694026906592477214
        assert audit_log_entry_obj.action_type is audit_logs.AuditLogEventType.CHANNEL_OVERWRITE_UPDATE
        assert audit_log_entry_obj.reason == "An artificial insanity."

    def test_deserialize_with_known_type_without_options_or_target_(
        self, test_audit_log_entry_payload, test_audit_log_change_payload, mock_app
    ):
        del test_audit_log_entry_payload["options"]
        del test_audit_log_entry_payload["target_id"]
        audit_log_entry_obj = audit_logs.AuditLogEntry.deserialize(test_audit_log_entry_payload, app=mock_app)
        assert audit_log_entry_obj.changes == [audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload)]
        assert audit_log_entry_obj.options is None
        assert audit_log_entry_obj.target_id is None
        assert audit_log_entry_obj.user_id == 560984860634644482
        assert audit_log_entry_obj.id == 694026906592477214
        assert audit_log_entry_obj.action_type is audit_logs.AuditLogEventType.CHANNEL_OVERWRITE_UPDATE
        assert audit_log_entry_obj.reason == "An artificial insanity."

    def test_deserialize_with_options_and_target_id_and_unknown_type(
        self, test_audit_log_entry_payload, test_audit_log_option_payload, test_audit_log_change_payload, mock_app,
    ):
        test_audit_log_entry_payload["action_type"] = 123123123
        audit_log_entry_obj = audit_logs.AuditLogEntry.deserialize(test_audit_log_entry_payload, app=mock_app)
        assert audit_log_entry_obj.changes == [audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload)]
        assert audit_log_entry_obj.options == audit_logs.UnrecognisedAuditLogEntryInfo.deserialize(
            test_audit_log_option_payload
        )
        assert audit_log_entry_obj.target_id == 115590097100865541
        assert audit_log_entry_obj.user_id == 560984860634644482
        assert audit_log_entry_obj.id == 694026906592477214
        assert audit_log_entry_obj.action_type == 123123123
        assert audit_log_entry_obj.reason == "An artificial insanity."

    def test_deserialize_without_options_or_target_id_and_unknown_type(
        self, test_audit_log_entry_payload, test_audit_log_option_payload, test_audit_log_change_payload, mock_app,
    ):
        del test_audit_log_entry_payload["options"]
        del test_audit_log_entry_payload["target_id"]
        test_audit_log_entry_payload["action_type"] = 123123123
        audit_log_entry_obj = audit_logs.AuditLogEntry.deserialize(test_audit_log_entry_payload, app=mock_app)
        assert audit_log_entry_obj.changes == [audit_logs.AuditLogChange.deserialize(test_audit_log_change_payload)]
        assert audit_log_entry_obj.options is None
        assert audit_log_entry_obj.target_id is None
        assert audit_log_entry_obj.user_id == 560984860634644482
        assert audit_log_entry_obj.id == 694026906592477214
        assert audit_log_entry_obj.action_type == 123123123
        assert audit_log_entry_obj.reason == "An artificial insanity."


class TestAuditLog:
    @pytest.fixture()
    def test_integration_payload(self):
        return {"id": 33590653072239123, "name": "A Name", "type": "twitch", "account": {}}

    @pytest.fixture()
    def test_user_payload(self):
        return {"id": "92929292", "username": "A USER", "discriminator": "6969", "avatar": None}

    @pytest.fixture()
    def test_webhook_payload(self):
        return {"id": "424242", "type": 1, "channel_id": "2020202"}

    @pytest.fixture()
    def test_audit_log_payload(
        self, test_audit_log_entry_payload, test_integration_payload, test_user_payload, test_webhook_payload
    ):
        return {
            "audit_log_entries": [test_audit_log_entry_payload],
            "integrations": [test_integration_payload],
            "users": [test_user_payload],
            "webhooks": [test_webhook_payload],
        }

    def test_deserialize(
        self,
        test_audit_log_payload,
        test_audit_log_entry_payload,
        test_integration_payload,
        test_user_payload,
        test_webhook_payload,
        mock_app,
    ):
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook, id=424242)
        mock_user_obj = mock.MagicMock(users.User, id=92929292)
        mock_integration_obj = mock.MagicMock(guilds.PartialGuildIntegration, id=33590653072239123)

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj))
        stack.enter_context(mock.patch.object(users.User, "deserialize", return_value=mock_user_obj))
        stack.enter_context(
            mock.patch.object(guilds.PartialGuildIntegration, "deserialize", return_value=mock_integration_obj)
        )

        with stack:
            audit_log_obj = audit_logs.AuditLog.deserialize(test_audit_log_payload, app=mock_app)
            webhooks.Webhook.deserialize.assert_called_once_with(test_webhook_payload, app=mock_app)
            users.User.deserialize.assert_called_once_with(test_user_payload, app=mock_app)
            guilds.PartialGuildIntegration.deserialize.assert_called_once_with(test_integration_payload, app=mock_app)
        assert audit_log_obj.entries == {
            694026906592477214: audit_logs.AuditLogEntry.deserialize(test_audit_log_entry_payload)
        }
        assert audit_log_obj.entries[694026906592477214]._app is mock_app
        assert audit_log_obj.webhooks == {424242: mock_webhook_obj}
        assert audit_log_obj.users == {92929292: mock_user_obj}
        assert audit_log_obj.integrations == {33590653072239123: mock_integration_obj}


class TestAuditLogIterator:
    @pytest.mark.asyncio
    async def test__fill_when_entities_returned(self, mock_app):
        mock_webhook_payload = {"id": "292393993", "channel_id": "43242"}
        mock_webhook_obj = mock.MagicMock(webhooks.Webhook, id=292393993)
        mock_user_payload = {"id": "929292", "public_flags": "22222"}
        mock_user_obj = mock.MagicMock(users.User, id=929292)
        mock_audit_log_entry_payload = {"target_id": "202020", "id": "222"}
        mock_integration_payload = {"id": "123123123", "account": {}}
        mock_integration_obj = mock.MagicMock(guilds.PartialGuildIntegration, id=123123123)
        mock_request = mock.AsyncMock(
            return_value={
                "webhooks": [mock_webhook_payload],
                "users": [mock_user_payload],
                "audit_log_entries": [mock_audit_log_entry_payload],
                "integrations": [mock_integration_payload],
            }
        )
        audit_log_iterator = audit_logs.AuditLogIterator(app=mock_app, request=mock_request, before="123", limit=None,)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(users.User, "deserialize", return_value=mock_user_obj))
        stack.enter_context(mock.patch.object(webhooks.Webhook, "deserialize", return_value=mock_webhook_obj))
        stack.enter_context(
            mock.patch.object(guilds.PartialGuildIntegration, "deserialize", return_value=mock_integration_obj)
        )

        with stack:
            assert await audit_log_iterator._fill() is None
            users.User.deserialize.assert_called_once_with(mock_user_payload, app=mock_app)
            webhooks.Webhook.deserialize.assert_called_once_with(mock_webhook_payload, app=mock_app)
            guilds.PartialGuildIntegration.deserialize.assert_called_once_with(mock_integration_payload, app=mock_app)
        assert audit_log_iterator.webhooks == {292393993: mock_webhook_obj}
        assert audit_log_iterator.users == {929292: mock_user_obj}
        assert audit_log_iterator.integrations == {123123123: mock_integration_obj}
        assert audit_log_iterator._buffer == [mock_audit_log_entry_payload]
        assert audit_log_iterator._app is mock_app
        mock_request.assert_called_once_with(
            before="123", limit=100,
        )

    @pytest.mark.asyncio
    async def test__fill_when_resource_exhausted(self, mock_app):
        mock_request = mock.AsyncMock(
            return_value={"webhooks": [], "users": [], "audit_log_entries": [], "integrations": []}
        )
        audit_log_iterator = audit_logs.AuditLogIterator(
            app=mock_app, request=mock_request, before="222222222", limit=None,
        )
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(users.User, "deserialize", return_value=...))
        stack.enter_context(mock.patch.object(webhooks.Webhook, "deserialize", return_value=...))
        stack.enter_context(mock.patch.object(guilds.PartialGuildIntegration, "deserialize", return_value=...))

        with stack:
            assert await audit_log_iterator._fill() is None
            users.User.deserialize.assert_not_called()
            webhooks.Webhook.deserialize.assert_not_called()
            guilds.PartialGuildIntegration.deserialize.assert_not_called()
        assert audit_log_iterator.webhooks == {}
        assert audit_log_iterator.users == {}
        assert audit_log_iterator.integrations == {}
        assert audit_log_iterator._buffer == []
        mock_request.assert_called_once_with(
            before="222222222", limit=100,
        )

    @pytest.mark.asyncio
    async def test__fill_when_before_and_limit_not_set(self, mock_app):
        mock_request = mock.AsyncMock(
            return_value={
                "webhooks": [],
                "users": [],
                "audit_log_entries": [{"id": "123123123"}, {"id": "123123123"}],
                "integrations": [],
            }
        )
        audit_log_iterator = audit_logs.AuditLogIterator(app=mock_app, request=mock_request, before="123", limit=None,)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(users.User, "deserialize", return_value=...))
        stack.enter_context(mock.patch.object(webhooks.Webhook, "deserialize", return_value=...))
        stack.enter_context(mock.patch.object(guilds.PartialGuildIntegration, "deserialize", return_value=...))

        with stack:
            assert await audit_log_iterator._fill() is None
        mock_request.assert_called_once_with(
            before="123", limit=100,
        )
        assert audit_log_iterator._limit is None

    @pytest.mark.asyncio
    async def test__fill_when_before_and_limit_set(self, mock_app):
        mock_request = mock.AsyncMock(
            return_value={
                "webhooks": [],
                "users": [],
                "audit_log_entries": [{"id": "123123123"}, {"id": "123123123"}],
                "integrations": [],
            }
        )
        audit_log_iterator = audit_logs.AuditLogIterator(
            app=mock_app, request=mock_request, before="222222222", limit=44,
        )
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(users.User, "deserialize", return_value=...))
        stack.enter_context(mock.patch.object(webhooks.Webhook, "deserialize", return_value=...))
        stack.enter_context(mock.patch.object(guilds.PartialGuildIntegration, "deserialize", return_value=...))

        with stack:
            assert await audit_log_iterator._fill() is None
        mock_request.assert_called_once_with(
            before="222222222", limit=44,
        )
        assert audit_log_iterator._limit == 42

    @pytest.mark.asyncio
    async def test___anext___when_not_filled_and_resource_is_exhausted(self, mock_app):
        mock_request = mock.AsyncMock(
            return_value={"webhooks": [], "users": [], "audit_log_entries": [], "integrations": []}
        )
        iterator = audit_logs.AuditLogIterator(app=mock_app, request=mock_request, before="123", limit=None)
        with mock.patch.object(audit_logs.AuditLogEntry, "deserialize", return_value=...):
            async for _ in iterator:
                assert False, "Iterator shouldn't have yielded anything."
            audit_logs.AuditLogEntry.deserialize.assert_not_called()
        assert iterator._front == "123"

    @pytest.mark.asyncio
    async def test___anext___when_not_filled(self, mock_app):
        mock_request = mock.AsyncMock(
            side_effect=[{"webhooks": [], "users": [], "audit_log_entries": [{"id": "666666"}], "integrations": []}]
        )
        mock_audit_log_entry = mock.MagicMock(audit_logs.AuditLogEntry, id=666666)
        iterator = audit_logs.AuditLogIterator(app=mock_app, request=mock_request, before="123", limit=None)
        with mock.patch.object(audit_logs.AuditLogEntry, "deserialize", side_effect=[mock_audit_log_entry]):
            async for result in iterator:
                assert result is mock_audit_log_entry
                break
            audit_logs.AuditLogEntry.deserialize.assert_called_once_with({"id": "666666"}, app=mock_app)
        mock_request.assert_called_once_with(
            before="123", limit=100,
        )
        assert iterator._front == "666666"

    @pytest.mark.asyncio
    async def test___anext___when_not_filled_and_limit_exhausted(self, mock_app):
        mock_request = mock.AsyncMock(
            side_effect=[{"webhooks": [], "users": [], "audit_log_entries": [], "integrations": []}]
        )
        mock_audit_log_entry = mock.MagicMock(audit_logs.AuditLogEntry, id=666666)
        iterator = audit_logs.AuditLogIterator(app=mock_app, request=mock_request, before="123", limit=None)
        with mock.patch.object(audit_logs.AuditLogEntry, "deserialize", side_effect=[mock_audit_log_entry]):
            async for _ in iterator:
                assert False, "Iterator shouldn't have yielded anything."
            audit_logs.AuditLogEntry.deserialize.assert_not_called()
        mock_request.assert_called_once_with(
            before="123", limit=100,
        )
        assert iterator._front == "123"

    @pytest.mark.asyncio
    async def test___anext___when_filled(self, mock_app):
        mock_request = mock.AsyncMock(side_effect=[])
        mock_audit_log_entry = mock.MagicMock(audit_logs.AuditLogEntry, id=4242)
        iterator = audit_logs.AuditLogIterator(app=mock_app, request=mock_request, before="123",)
        iterator._buffer = [{"id": "123123"}]
        with mock.patch.object(audit_logs.AuditLogEntry, "deserialize", side_effect=[mock_audit_log_entry]):
            async for result in iterator:
                assert result is mock_audit_log_entry
                break
            audit_logs.AuditLogEntry.deserialize.assert_called_once_with({"id": "123123"}, app=mock_app)
        mock_request.assert_not_called()
        assert iterator._front == "4242"
