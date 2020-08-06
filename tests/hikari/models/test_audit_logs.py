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

from hikari.models import audit_logs
from hikari.utilities import snowflake


def test_AuditLogChangeKey_str_operator():
    change_key = audit_logs.AuditLogChangeKey("owner_id")
    assert str(change_key) == "OWNER_ID"


def test_AuditLogEventType_str_operator():
    event_type = audit_logs.AuditLogEventType(80)
    assert str(event_type) == "INTEGRATION_CREATE"


class TestAuditLog:
    def test_iter(self):
        entry_1 = object()
        entry_2 = object()
        entry_3 = object()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflake.Snowflake(432123): entry_1,
                snowflake.Snowflake(432654): entry_2,
                snowflake.Snowflake(432888): entry_3,
            },
            integrations={},
            users={},
            webhooks={},
        )
        assert list(audit_log) == [entry_1, entry_2, entry_3]

    def test_get_item_with_index(self):
        entry = object()
        entry_2 = object()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflake.Snowflake(432123): object(),
                snowflake.Snowflake(432654): entry,
                snowflake.Snowflake(432888): object(),
                snowflake.Snowflake(677777): object(),
                snowflake.Snowflake(999999): entry_2,
            },
            integrations={},
            users={},
            webhooks={},
        )
        assert audit_log[1] is entry
        assert audit_log[4] is entry_2

    def test_get_item_with_index(self):
        entry_1 = object()
        entry_2 = object()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflake.Snowflake(432123): object(),
                snowflake.Snowflake(432654): entry_1,
                snowflake.Snowflake(432888): object(),
                snowflake.Snowflake(666666): entry_2,
                snowflake.Snowflake(783452): object(),
            },
            integrations={},
            users={},
            webhooks={},
        )
        assert audit_log[1:5:2] == (entry_1, entry_2)

    def test_get_item_with_ivalid_type(self):
        try:
            audit_logs.AuditLog(entries=[object(), object()], integrations={}, users={}, webhooks={},)["OK"]
        except TypeError:
            pass
        else:
            assert False, "Expect TypeError but got no exception"

    def test_len(self):
        audit_log = audit_logs.AuditLog(
            entries={
                snowflake.Snowflake(432123): object(),
                snowflake.Snowflake(432654): object(),
                snowflake.Snowflake(432888): object(),
                snowflake.Snowflake(783452): object(),
            },
            integrations={},
            users={},
            webhooks={},
        )
        assert len(audit_log) == 4
