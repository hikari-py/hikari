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
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm.state import base_registry
from hikari.orm.models import audit_logs
from hikari.orm.models import channels
from hikari.orm.models import overwrites
from tests.hikari import _helpers


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=base_registry.BaseRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.fixture
def mock_user_payload():
    return {
        "id": "6978594863",
        "username": "Snabbare",
        "discriminator": "2312",
        "avatar": "1a2b3c4d",
        "locale": "gb",
        "flags": 0b00101101,
        "premium_type": 0,
    }


@pytest.fixture()
def mock_webhook_payload(mock_user_payload):
    return {
        "name": "this is a webhook",
        "channel_id": "3455376576545765",
        "token": "SzDM1S_xaVPsDDXJymo9EQqChjXIenyJ9OpmS27v5p61Czm7LY6lUMFsPaSlezX2DF1i",
        "avatar": None,
        "bot": False,
        "guild_id": "236754234765645",
        "id": "43267879654645387576",
        "user": mock_user_payload,
    }


@pytest.fixture()
def mock_audit_log_payload(mock_user_payload, mock_webhook_payload):
    return {
        "users": [mock_user_payload],
        "webhooks": [mock_webhook_payload],
        "audit_log_entries": [
            {
                "id": "624952949949939",
                "user_id": "115590097100865541",
                "target_id": "39494939485734849",
                "action_type": 25,
                "changes": [{"key": "$add", "new_value": [{"name": "I am a role", "id": "2356343234234"}]}],
                "reason": "Very good reason",
            },
        ],
    }


@pytest.mark.model()
def test_AuditLog(fabric_obj, mock_audit_log_payload, mock_user_payload, mock_webhook_payload):
    audit_log_obj = audit_logs.AuditLog(fabric_obj, mock_audit_log_payload)

    assert audit_log_obj.audit_log_entries[0].id == 624952949949939
    assert audit_log_obj.audit_log_entries[0].user_id == 115590097100865541
    assert audit_log_obj.audit_log_entries[0].target_id == 39494939485734849
    assert audit_log_obj.audit_log_entries[0].action_type is audit_logs.AuditLogEvent.MEMBER_ROLE_UPDATE
    assert audit_log_obj.audit_log_entries[0].changes[0].key is audit_logs.AuditLogChangeKey.ADD_ROLE_TO_MEMBER
    assert audit_log_obj.audit_log_entries[0].changes[0].new_value[2356343234234].name == "I am a role"
    assert audit_log_obj.audit_log_entries[0].changes[0].new_value[2356343234234].id == 2356343234234
    assert audit_log_obj.audit_log_entries[0].reason == "Very good reason"

    fabric_obj.state_registry.parse_user.assert_called_once_with(mock_user_payload)
    fabric_obj.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)


@pytest.mark.model
def test_afk_channel_change():
    entry_obj = audit_logs.AuditLogEntry(
        {
            "id": "647842099676446730",
            "user_id": "115590097100865541",
            "target_id": "561884984214814744",
            "action_type": 1,
            "changes": [
                {"key": "afk_channel_id", "old_value": "561887595798462499", "new_value": "561886693339168770"}
            ],
        }
    )
    assert entry_obj.id == 647842099676446730
    assert entry_obj.user_id == 115590097100865541
    assert entry_obj.target_id == 561884984214814744
    assert entry_obj.action_type is audit_logs.AuditLogEvent.GUILD_UPDATE
    assert entry_obj.changes[0].key is audit_logs.AuditLogChangeKey.AFK_CHANNEL_ID
    assert entry_obj.changes[0].old_value == 561887595798462499
    assert entry_obj.changes[0].new_value == 561886693339168770


@pytest.mark.model
def test_AuditLogEntry___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.AuditLogEntry,
            id=42,
            user_id=69,
            action_type=audit_logs.AuditLogEvent.BOT_ADD,
            reason="obama cares",
            __repr__=audit_logs.AuditLogEntry.__repr__,
        )
    )


@pytest.mark.model
def test_AuditLogEntry___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.AuditLogEntry,
            id=42,
            user_id=69,
            action_type=audit_logs.AuditLogEvent.BOT_ADD,
            reason="obama cares",
        )
    )


@pytest.mark.model
def test_new_sequence_of():
    sequence_lambda = audit_logs._new_sequence_of(int)
    assert sequence_lambda(["6", "0", "1", "3"]) == [6, 0, 1, 3]


@pytest.mark.model
@pytest.mark.parametrize(["type_entity", "expected_result"], [[4, channels.GuildCategory], [str, str], [16, 16]])
def test_type_convert(type_entity, expected_result):
    assert audit_logs._type_converter(type_entity) is expected_result


@pytest.mark.model
def test_AuditLogEntryCountInfo():
    info_obj = audit_logs.parse_audit_log_entry_info({"count": 64}, audit_logs.AuditLogEvent.MESSAGE_BULK_DELETE)
    assert isinstance(info_obj, audit_logs.AuditLogEntryCountInfo)
    assert info_obj.count == 64


@pytest.mark.model
def test_AuditLogEntryCountInfo___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.AuditLogEntryCountInfo, count=42, __repr__=audit_logs.AuditLogEntryCountInfo.__repr__
        )
    )


@pytest.mark.model
def test_MemberMoveAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"count": 44, "channel_id": "234123312213321"}, audit_logs.AuditLogEvent.MEMBER_MOVE
    )
    assert isinstance(info_obj, audit_logs.MemberMoveAuditLogEntryInfo)
    assert info_obj.count == 44
    assert info_obj.channel_id == 234123312213321


@pytest.mark.model
def test_MemberMoveAuditLogEntryInfo___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.MemberMoveAuditLogEntryInfo,
            count=42,
            channel_id=69,
            __repr__=audit_logs.MemberMoveAuditLogEntryInfo.__repr__,
        )
    )


@pytest.mark.model
def test_MemberPruneAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"delete_member_days": 7, "members_removed": 49}, audit_logs.AuditLogEvent.MEMBER_PRUNE
    )
    assert isinstance(info_obj, audit_logs.MemberPruneAuditLogEntryInfo)
    assert info_obj.delete_member_days == 7
    assert info_obj.members_removed == 49


@pytest.mark.model
def test_MemberPruneAuditLogEntryInfo___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.MemberPruneAuditLogEntryInfo,
            delete_member_days=42,
            members_removed=69,
            __repr__=audit_logs.MemberPruneAuditLogEntryInfo.__repr__,
        )
    )


@pytest.mark.model
def test_MessageDeleteAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"count": 7, "channel_id": "4949494949494949"}, audit_logs.AuditLogEvent.MESSAGE_DELETE
    )
    assert isinstance(info_obj, audit_logs.MessageDeleteAuditLogEntryInfo)
    assert info_obj.count == 7
    assert info_obj.channel_id == 4949494949494949


@pytest.mark.model
def test_MessageDeleteAuditLogEntryInfo___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.MessageDeleteAuditLogEntryInfo,
            count=42,
            channel_id=69,
            __repr__=audit_logs.MessageDeleteAuditLogEntryInfo.__repr__,
        )
    )


@pytest.mark.model
def test_MessagePinAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"channel_id": "3333333333333", "message_id": "4949494949494949"}, audit_logs.AuditLogEvent.MESSAGE_PIN
    )
    assert isinstance(info_obj, audit_logs.MessagePinAuditLogEntryInfo)
    assert info_obj.channel_id == 3333333333333
    assert info_obj.message_id == 4949494949494949


@pytest.mark.model
def test_MessagePinAuditLogEntryInfo___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.MessagePinAuditLogEntryInfo,
            channel_id=42,
            message_id=69,
            __repr__=audit_logs.MessagePinAuditLogEntryInfo.__repr__,
        )
    )


@pytest.mark.model
def test_ChannelOverwriteAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"id": "115590097100865541", "type": "ROLE"}, audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_DELETE
    )
    assert isinstance(info_obj, audit_logs.ChannelOverwriteAuditLogEntryInfo)
    assert info_obj.id == 115590097100865541
    assert info_obj.type is overwrites.OverwriteEntityType.ROLE


@pytest.mark.model
def test_ChannelOverwriteAuditLogEntryInfo___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.ChannelOverwriteAuditLogEntryInfo,
            id=42,
            type=overwrites.OverwriteEntityType.ROLE,
            __repr__=audit_logs.ChannelOverwriteAuditLogEntryInfo.__repr__,
        )
    )


@pytest.mark.model
def test_AuditLogChange_without_converter():
    audit_log_change_obj = audit_logs.AuditLogChange(
        {
            "key": "avatar_hash",
            "old_value": "0e2aad94b8c086865c4e62009b925e0f",
            "new_value": "a_d3f77f408fb58925024e887ddc4a555d",
        }
    )
    assert audit_log_change_obj.key is audit_logs.AuditLogChangeKey.AVATAR_HASH
    assert str(audit_log_change_obj.key) == "AVATAR_HASH"
    assert audit_log_change_obj.old_value == "0e2aad94b8c086865c4e62009b925e0f"
    assert audit_log_change_obj.new_value == "a_d3f77f408fb58925024e887ddc4a555d"


@pytest.mark.model
def test_AuditLogChange___repr__():
    assert repr(
        _helpers.mock_model(
            audit_logs.AuditLogChange,
            key=audit_logs.AuditLogChangeKey.NAME,
            old_value="foo",
            new_value="bar",
            __repr__=audit_logs.AuditLogChange.__repr__,
        )
    )
