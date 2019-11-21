from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import audit_logs


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=state_registry.IStateRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.fixture
def mock_user_payload():
    return {
        "id": "123456",
        "username": "Boris Johnson",
        "discriminator": "6969",
        "avatar": "1a2b3c4d",
        "locale": "gb",
        "flags": 0b00101101,
        "premium_type": 0b1101101,
    }


@pytest.fixture()
def mock_webhook_payload(mock_user_payload):
    return {
        "name": "test webhook",
        "channel_id": "199737254929760256",
        "token": "3d89bb7572e0fb30d8128367b3b1b44fecd1726de135cbe28a41f8b2f777c372ba2939e72279b94526ff5d1bd4358d65cf11",
        "avatar": None,
        "bot": False,
        "guild_id": "199737254929760256",
        "id": "223704706495545344",
        "user": mock_user_payload,
    }


@pytest.fixture()
def mock_audit_log_payload(mock_user_payload, mock_webhook_payload):
    return {
        "users": [mock_user_payload],
        "webhooks": [mock_webhook_payload],
        "audit_log_entries": [
            {
                "id": "123453243234234234234",
                "user_id": "34869834987234089",
                "target_id": "3949683045830942342",
                "action_type": 60,
                "changes": [{"key": "name", "new_value": "eevee"}],
                "reason": "Very good reason",
            },
            {
                "id": "624952949949939",
                "user_id": "115590097100865541",
                "target_id": "39494939485734849",
                "action_type": 25,
                "changes": [{"key": "$add", "new_value": [{"name": "I am a role", "id": "2356343234234"}]}],
            },
        ],
    }


@pytest.mark.model()
def test_audit_log(fabric_obj, mock_audit_log_payload, mock_user_payload, mock_webhook_payload):
    audit_log_obj = audit_logs.AuditLog(fabric_obj, mock_audit_log_payload)
    # Check first overwrite.
    assert audit_log_obj.audit_log_entries[0].id == 123453243234234234234
    assert audit_log_obj.audit_log_entries[0].user_id == 34869834987234089
    assert audit_log_obj.audit_log_entries[0].target_id == 3949683045830942342
    assert audit_log_obj.audit_log_entries[0].action_type is audit_logs.AuditLogEvent.EMOJI_CREATE
    # Check role on second overwrite.
    assert audit_log_obj.audit_log_entries[1].changes[0].new_value[2356343234234].name == "I am a role"
    assert audit_log_obj.audit_log_entries[1].changes[0].new_value[2356343234234].id == 2356343234234

    fabric_obj.state_registry.parse_user.assert_called_once_with(mock_user_payload)
    fabric_obj.state_registry.parse_webhook.assert_called_once_with(mock_webhook_payload)
