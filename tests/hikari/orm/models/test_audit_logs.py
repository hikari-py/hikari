from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import audit_logs
from hikari.orm.models import roles

@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=state_registry.IStateRegistry)


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
        "premium_type": 0b1101101,
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
    assert audit_log_obj.audit_log_entries[0].changes[0].key == "$add"
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
    assert entry_obj.changes[0].key == "afk_channel_id"
    assert entry_obj.changes[0].old_value == 561887595798462499
    assert entry_obj.changes[0].new_value == 561886693339168770


@pytest.mark.model
def test_new_sequence_of():
    sequence_lambda = audit_logs._new_sequence_of(int)
    assert sequence_lambda(["6", "0", "1", "3"]) == [6, 0, 1, 3]


@pytest.mark.model
def test_AuditLogEntryCountInfo():
    info_obj = audit_logs.parse_audit_log_entry_info({"count": 64}, audit_logs.AuditLogEvent.MESSAGE_BULK_DELETE)
    assert isinstance(info_obj, audit_logs.AuditLogEntryCountInfo)
    assert info_obj.count == 64


@pytest.mark.model
def test_MemberMoveAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"count": 44, "channel_id": "234123312213321"}, audit_logs.AuditLogEvent.MEMBER_MOVE
    )
    assert isinstance(info_obj, audit_logs.MemberMoveAuditLogEntryInfo)
    assert info_obj.count == 44
    assert info_obj.channel_id == 234123312213321


@pytest.mark.model
def test_MemberPruneAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"delete_member_days": 7, "members_removed": 49}, audit_logs.AuditLogEvent.MEMBER_PRUNE
    )
    assert isinstance(info_obj, audit_logs.MemberPruneAuditLogEntryInfo)
    assert info_obj.delete_member_days == 7
    assert info_obj.members_removed == 49


@pytest.mark.model
def test_MessageDeleteAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"count": 7, "channel_id": "4949494949494949"}, audit_logs.AuditLogEvent.MESSAGE_DELETE
    )
    assert isinstance(info_obj, audit_logs.MessageDeleteAuditLogEntryInfo)
    assert info_obj.count == 7
    assert info_obj.channel_id == 4949494949494949


@pytest.mark.model
def test_MessagePinAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"channel_id": "3333333333333", "message_id": "4949494949494949"}, audit_logs.AuditLogEvent.MESSAGE_PIN
    )
    assert isinstance(info_obj, audit_logs.MessagePinAuditLogEntryInfo)
    assert info_obj.channel_id == 3333333333333
    assert info_obj.message_id == 4949494949494949


@pytest.mark.model
def test_ChannelOverwriteAuditLogEntryInfo():
    info_obj = audit_logs.parse_audit_log_entry_info(
        {"id": "115590097100865541", "type": "ROLE"}, audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_DELETE
    )
    assert isinstance(info_obj, audit_logs.ChannelOverwriteAuditLogEntryInfo)
    assert info_obj.id == 115590097100865541
    assert info_obj.type.value is roles.Role
