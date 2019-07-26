#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import pytest

from hikari.model import audit_log

from .testdata import *


@pytest.fixture
@with_test_data(json("audit_log"))
def audit_log_object(test_data):
    audit_log_object = audit_log.AuditLog.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_edit_channel"))
def audit_log_entry_edit_channel(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_invite_create"))
def audit_log_entry_invite_create(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_message_delete"))
def audit_log_entry_message_delete(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_overwrites_add"))
def audit_log_entry_overwrites_add(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_overwrites_delete"))
def audit_log_entry_overwrites_delete(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_overwrites_update"))
def audit_log_entry_overwrites_update(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_role_add"))
def audit_log_entry_role_add(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.fixture
@with_test_data(json("audit_log_entry_role_remove"))
def audit_log_entry_role_remove(test_data):
    audit_log_object = audit_log.AuditLogEntry.from_dict(test_data)
    assert audit_log_object is not None
    return audit_log_object


@pytest.mark.model
class TestAuditLog:
    def test_AuditLog_has_three_specified_keys(self, audit_log_object):
        assert audit_log_object.users is not None
        assert audit_log_object.entries is not None
        assert audit_log_object.webhooks is not None

    def test_AuditLog_has_correct_number_of_users(self, audit_log_object):
        assert len(audit_log_object.users) == 2
        assert audit_log_object.users[0] is not None
        assert audit_log_object.users[1] is not None

    def test_AuditLog_has_correct_number_of_webhooks(self, audit_log_object):
        assert len(audit_log_object.webhooks) == 1
        assert audit_log_object.webhooks[0] is not None

    def test_AuditLog_has_correct_number_of_entries(self, audit_log_object):
        assert len(audit_log_object.entries) == 8
        for number, entry in enumerate(audit_log_object.entries, start=1):
            assert entry is not None

    def test_AuditLogEntry_edit_channel(self, audit_log_entry_edit_channel):
        assert audit_log_entry_edit_channel.target_id == 574921092926537729

        assert isinstance(audit_log_entry_edit_channel.changes, list)
        assert len(audit_log_entry_edit_channel.changes) == 1
        changes0 = audit_log_entry_edit_channel.changes[0]
        assert isinstance(changes0, audit_log.AuditLogChange)
        assert changes0.old_value == "Testing snake pit"
        assert (
            changes0.new_value == "tmpod had a really fancy message here full of bloody invisible special characters "
            "and it pained me so i changed it to this."
        )
        assert changes0.key == audit_log.AuditLogChangeKey.TOPIC
        assert audit_log_entry_edit_channel.options is None
        assert audit_log_entry_edit_channel.user_id == 159053372010266624
        assert audit_log_entry_edit_channel.id == 596296565837135892
        assert audit_log_entry_edit_channel.action_type == 11
        assert audit_log_entry_edit_channel.action_type == audit_log.AuditLogEvent.CHANNEL_UPDATE

    def test_AuditLogEntry_invite_create(self, audit_log_entry_invite_create):
        assert audit_log_entry_invite_create.target_id is None
        assert audit_log_entry_invite_create.changes is not None
        assert audit_log_entry_invite_create.options is None
        assert len(audit_log_entry_invite_create.changes) == 7

        assert (
            audit_log.AuditLogChange(old_value=None, new_value=86400, key=audit_log.AuditLogChangeKey.MAX_AGE)
            in audit_log_entry_invite_create.changes
        )

        assert (
            audit_log.AuditLogChange(old_value=None, new_value=False, key=audit_log.AuditLogChangeKey.TEMPORARY)
            in audit_log_entry_invite_create.changes
        )

        assert (
            audit_log.AuditLogChange(
                old_value=None, new_value=537340989808050216, key=audit_log.AuditLogChangeKey.INVITER_ID
            )
            in audit_log_entry_invite_create.changes
        )

        assert (
            audit_log.AuditLogChange(
                old_value=None, new_value=577602779410071575, key=audit_log.AuditLogChangeKey.CHANNEL_ID
            )
            in audit_log_entry_invite_create.changes
        )

        assert (
            audit_log.AuditLogChange(old_value=None, new_value=0, key=audit_log.AuditLogChangeKey.USES)
            in audit_log_entry_invite_create.changes
        )

        assert (
            audit_log.AuditLogChange(old_value=None, new_value=0, key=audit_log.AuditLogChangeKey.MAX_USES)
            in audit_log_entry_invite_create.changes
        )

        assert (
            audit_log.AuditLogChange(old_value=None, new_value="gbPccV", key=audit_log.AuditLogChangeKey.CODE)
            in audit_log_entry_invite_create.changes
        )

    def test_AuditLogEntry_message_delete(self, audit_log_entry_message_delete):
        assert audit_log_entry_message_delete.target_id == 293567313985273856
        assert audit_log_entry_message_delete.user_id == 537340989808050216
        assert audit_log_entry_message_delete.id == 594908821345009674
        assert audit_log_entry_message_delete.action_type == 72 == audit_log.AuditLogEvent.MESSAGE_DELETE
        assert audit_log_entry_message_delete.changes == []
        assert isinstance(audit_log_entry_message_delete.options, audit_log.MessageDeletedAuditLogEntryInfo)
        assert audit_log_entry_message_delete.options.count == 1
        assert audit_log_entry_message_delete.options.channel_id == 574921006817476610

    def test_AuditLogEntry_overwrites_add(self, audit_log_entry_overwrites_add):
        assert audit_log_entry_overwrites_add.user_id == 159053372010266624
        assert audit_log_entry_overwrites_add.target_id == 574921766808584222
        assert audit_log_entry_overwrites_add.id == 592720122141999124
        assert audit_log_entry_overwrites_add.action_type == 13 == audit_log.AuditLogEvent.CHANNEL_OVERWRITE_CREATE
        assert audit_log_entry_overwrites_add.changes is not None

        assert (
            audit_log.AuditLogChange(old_value=None, new_value=2048, key=audit_log.AuditLogChangeKey.DENY)
            in audit_log_entry_overwrites_add.changes
        )

        assert (
            audit_log.AuditLogChange(old_value=None, new_value="role", key=audit_log.AuditLogChangeKey.TYPE)
            in audit_log_entry_overwrites_add.changes
        )

        assert (
            audit_log.AuditLogChange(old_value=None, new_value=574921006817476608, key=audit_log.AuditLogChangeKey.ID)
            in audit_log_entry_overwrites_add.changes
        )

        assert (
            audit_log.AuditLogChange(old_value=None, new_value=0, key=audit_log.AuditLogChangeKey.ALLOW)
            in audit_log_entry_overwrites_add.changes
        )

        assert isinstance(audit_log_entry_overwrites_add.options, audit_log.ChannelOverwriteAuditLogEntryInfo)
        assert audit_log_entry_overwrites_add.options.role_name == "@everyone"
        assert audit_log_entry_overwrites_add.options.type.name.lower() == "role"
        assert audit_log_entry_overwrites_add.options.id == 574921006817476608
        assert audit_log_entry_overwrites_add.reason == "mass outbreak of diarrhea"

    def test_AuditLogEntry_overwrites_update(self, audit_log_entry_overwrites_update):
        assert audit_log_entry_overwrites_update.user_id == 159053372010266624
        assert audit_log_entry_overwrites_update.target_id == 574921766808584222
        assert audit_log_entry_overwrites_update.id == 592719168898465792
        assert audit_log_entry_overwrites_update.action_type == 14 == audit_log.AuditLogEvent.CHANNEL_OVERWRITE_UPDATE
        assert audit_log_entry_overwrites_update.changes is not None

        assert (
            audit_log.AuditLogChange(old_value=2048, new_value=0, key=audit_log.AuditLogChangeKey.DENY)
            in audit_log_entry_overwrites_update.changes
        )

        assert isinstance(audit_log_entry_overwrites_update.options, audit_log.ChannelOverwriteAuditLogEntryInfo)
        assert audit_log_entry_overwrites_update.options.role_name == "@everyone"
        assert audit_log_entry_overwrites_update.options.type.name.lower() == "role"
        assert audit_log_entry_overwrites_update.options.id == 574921006817476608

    def test_AuditLogEntry_overwrites_delete(self, audit_log_entry_overwrites_delete):
        assert audit_log_entry_overwrites_delete.user_id == 159053372010266624
        assert audit_log_entry_overwrites_delete.target_id == 583953735722729485
        assert audit_log_entry_overwrites_delete.id == 592719735557455883
        assert audit_log_entry_overwrites_delete.action_type == 15 == audit_log.AuditLogEvent.CHANNEL_OVERWRITE_DELETE
        assert audit_log_entry_overwrites_delete.changes is not None

        assert (
            audit_log.AuditLogChange(new_value=None, old_value=0, key=audit_log.AuditLogChangeKey.DENY)
            in audit_log_entry_overwrites_delete.changes
        )

        assert (
            audit_log.AuditLogChange(new_value=None, old_value="role", key=audit_log.AuditLogChangeKey.TYPE)
            in audit_log_entry_overwrites_delete.changes
        )

        assert (
            audit_log.AuditLogChange(new_value=None, old_value=574921006817476608, key=audit_log.AuditLogChangeKey.ID)
            in audit_log_entry_overwrites_delete.changes
        )

        assert (
            audit_log.AuditLogChange(new_value=None, old_value=0, key=audit_log.AuditLogChangeKey.ALLOW)
            in audit_log_entry_overwrites_delete.changes
        )

        assert isinstance(audit_log_entry_overwrites_delete.options, audit_log.ChannelOverwriteAuditLogEntryInfo)
        assert audit_log_entry_overwrites_delete.options.role_name == "@everyone"
        assert audit_log_entry_overwrites_delete.options.type.name.lower() == "role"
        assert audit_log_entry_overwrites_delete.options.id == 574921006817476608

    def test_AuditLogEntry_role_add_to_member(self, audit_log_entry_role_add):
        assert audit_log_entry_role_add.target_id == 572144340277919754
        assert audit_log_entry_role_add.user_id == 537340989808050216
        assert audit_log_entry_role_add.id == 599637601951023104
        assert audit_log_entry_role_add.action_type == audit_log.AuditLogEvent.MEMBER_ROLE_UPDATE == 25
        assert len(audit_log_entry_role_add.changes) == 1
        change0 = audit_log_entry_role_add.changes[0]
        assert change0.key == audit_log.AuditLogChangeKey.ADD_ROLE_TO_MEMBER
        assert change0.old_value is None
        assert isinstance(change0.new_value, list)
        assert len(change0.new_value) == 1
        assert {"name": "S.T.A.F.F.", "id": "582689893965365248"} in change0.new_value

    def test_AuditLogEntry_role_remove_from_member(self, audit_log_entry_role_remove):
        assert audit_log_entry_role_remove.target_id == 572144340277919754
        assert audit_log_entry_role_remove.user_id == 537340989808050216
        assert audit_log_entry_role_remove.id == 599637601951023104
        assert audit_log_entry_role_remove.action_type == audit_log.AuditLogEvent.MEMBER_ROLE_UPDATE == 25
        assert len(audit_log_entry_role_remove.changes) == 1
        change0 = audit_log_entry_role_remove.changes[0]
        assert change0.key == audit_log.AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER
        assert change0.old_value is None
        assert isinstance(change0.new_value, list)
        assert len(change0.new_value) == 1
        assert {"name": "S.T.A.F.F.", "id": "582689893965365248"} in change0.new_value

    def test_AuditLogChangeKey_handles_undocumented_crap_input(self):
        assert audit_log.AuditLogChangeKey.from_discord_name("mfa_level") == audit_log.AuditLogChangeKey.MFA_LEVEL
        assert audit_log.AuditLogChangeKey.from_discord_name("$add") == audit_log.AuditLogChangeKey.ADD_ROLE_TO_MEMBER
        assert audit_log.AuditLogChangeKey.from_discord_name("some_undocumented_bs_here") == "SOME_UNDOCUMENTED_BS_HERE"
