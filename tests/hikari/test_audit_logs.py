# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
import pytest

from hikari import audit_logs
from hikari import snowflakes


class TestUnrecognisedAuditLogEntryInfo:
    def test_eq_when_not_same_class(self):
        audit_log = audit_logs.UnrecognisedAuditLogEntryInfo(app=None, payload={})
        # Unfortunately there is no other way to do this
        returned = audit_logs.UnrecognisedAuditLogEntryInfo.__eq__(audit_log, object())
        assert returned is NotImplemented

    @pytest.mark.parametrize(
        ("payload1", "payload2", "expected"),
        [
            ({"test": "test2"}, {"test": "test3"}, False),
            ({}, {"test": "test2"}, False),
            ({"test": "test2"}, {"test": "test2"}, True),
        ],
    )
    def test_eq(self, payload1, payload2, expected):
        audit_log = audit_logs.UnrecognisedAuditLogEntryInfo(app=None, payload=payload1)
        other = audit_logs.UnrecognisedAuditLogEntryInfo(app=None, payload=payload2)

        assert (audit_log == other) is expected

    def test_str(self):
        audit_log = audit_logs.UnrecognisedAuditLogEntryInfo(app=None, payload={"test": "test2", "test3": 98})

        assert str(audit_log) == "UnrecognisedAuditLogEntryInfo(test='test2', test3=98)"

    def test_repr(self):
        audit_log = audit_logs.UnrecognisedAuditLogEntryInfo(app=None, payload={"test": "test2", "test3": 98})

        assert repr(audit_log) == "UnrecognisedAuditLogEntryInfo(test='test2', test3=98)"


class TestAuditLog:
    def test_iter(self):
        entry_1 = object()
        entry_2 = object()
        entry_3 = object()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflakes.Snowflake(432123): entry_1,
                snowflakes.Snowflake(432654): entry_2,
                snowflakes.Snowflake(432888): entry_3,
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
                snowflakes.Snowflake(432123): object(),
                snowflakes.Snowflake(432654): entry,
                snowflakes.Snowflake(432888): object(),
                snowflakes.Snowflake(677777): object(),
                snowflakes.Snowflake(999999): entry_2,
            },
            integrations={},
            users={},
            webhooks={},
        )
        assert audit_log[1] is entry
        assert audit_log[4] is entry_2

    def test_get_item_with_slice(self):
        entry_1 = object()
        entry_2 = object()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflakes.Snowflake(432123): object(),
                snowflakes.Snowflake(432654): entry_1,
                snowflakes.Snowflake(432888): object(),
                snowflakes.Snowflake(666666): entry_2,
                snowflakes.Snowflake(783452): object(),
            },
            integrations={},
            users={},
            webhooks={},
        )
        assert audit_log[1:5:2] == (entry_1, entry_2)

    def test_get_item_with_ivalid_type(self):
        with pytest.raises(TypeError):
            audit_logs.AuditLog(
                entries=[object(), object()],
                integrations={},
                users={},
                webhooks={},
            )["OK"]

    def test_len(self):
        audit_log = audit_logs.AuditLog(
            entries={
                snowflakes.Snowflake(432123): object(),
                snowflakes.Snowflake(432654): object(),
                snowflakes.Snowflake(432888): object(),
                snowflakes.Snowflake(783452): object(),
            },
            integrations={},
            users={},
            webhooks={},
        )
        assert len(audit_log) == 4
