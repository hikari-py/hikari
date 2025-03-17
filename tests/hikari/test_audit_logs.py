# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
from __future__ import annotations

import mock
import pytest

from hikari import audit_logs
from hikari import channels
from hikari import snowflakes
from hikari import traits


@pytest.fixture
def mock_app() -> traits.RESTAware:
    return mock.Mock(traits.RESTAware)


@pytest.mark.asyncio
class TestMessagePinEntryInfo:
    @pytest.fixture
    def message_pin_entry_info(mock_app: traits.RESTAware) -> audit_logs.MessagePinEntryInfo:
        return audit_logs.MessagePinEntryInfo(
            app=mock_app, channel_id=snowflakes.Snowflake(123), message_id=snowflakes.Snowflake(456)
        )

    async def test_fetch_channel(self, message_pin_entry_info: audit_logs.MessagePinEntryInfo):
        with (
            mock.patch.object(message_pin_entry_info, "app") as patched_app,
            mock.patch.object(
                patched_app.rest,
                "fetch_channel",
                mock.AsyncMock(return_value=mock.Mock(spec_set=channels.GuildTextChannel)),
            ) as patched_fetch_channel,
        ):
            assert await message_pin_entry_info.fetch_channel() is patched_fetch_channel.return_value
            patched_fetch_channel.assert_awaited_once_with(123)

    async def test_fetch_message(self, message_pin_entry_info: audit_logs.MessagePinEntryInfo):
        with (
            mock.patch.object(message_pin_entry_info, "app") as patched_app,
            mock.patch.object(patched_app.rest, "fetch_message", new_callable=mock.AsyncMock) as patched_fetch_message,
        ):
            assert await message_pin_entry_info.fetch_message() is patched_fetch_message.return_value
            patched_fetch_message.assert_awaited_once_with(123, 456)


@pytest.mark.asyncio
class TestMessageDeleteEntryInfo:
    async def test_fetch_channel(self):
        app = mock.AsyncMock()
        model = audit_logs.MessageDeleteEntryInfo(app=app, count=1, channel_id=snowflakes.Snowflake(123))

        with mock.patch.object(
            app.rest, "fetch_channel", new=mock.AsyncMock(return_value=mock.Mock(spec_set=channels.GuildTextChannel))
        ) as patched_fetch_channel:
            assert await model.fetch_channel() is patched_fetch_channel.return_value

            patched_fetch_channel.assert_awaited_once_with(123)


@pytest.mark.asyncio
class TestMemberMoveEntryInfo:
    async def test_fetch_channel(self):
        app = mock.AsyncMock()
        model = audit_logs.MemberMoveEntryInfo(app=app, count=1, channel_id=snowflakes.Snowflake(123))

        with mock.patch.object(
            app.rest, "fetch_channel", new=mock.AsyncMock(return_value=mock.Mock(spec_set=channels.GuildVoiceChannel))
        ) as patched_fetch_channel:
            assert await model.fetch_channel() is patched_fetch_channel.return_value

            patched_fetch_channel.assert_awaited_once_with(123)


class TestAuditLogEntry:
    @pytest.fixture
    def audit_log_entry(mock_app: traits.RESTAware) -> audit_logs.AuditLogEntry:
        return audit_logs.AuditLogEntry(
            app=mock_app,
            id=snowflakes.Snowflake(123),
            target_id=None,
            changes=[],
            user_id=snowflakes.Snowflake(456),
            action_type=0,
            options=None,
            reason=None,
            guild_id=snowflakes.Snowflake(34123123),
        )

    @pytest.mark.asyncio
    async def test_fetch_user_when_no_user(self, audit_log_entry: audit_logs.AuditLogEntry):
        with (
            mock.patch.object(audit_log_entry, "user_id", None),
            mock.patch.object(audit_log_entry, "app") as patched_app,
            mock.patch.object(patched_app.rest, "fetch_user") as patched_fetch_user,
        ):
            assert await audit_log_entry.fetch_user() is None

            patched_fetch_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_user_when_user(self, audit_log_entry: audit_logs.AuditLogEntry):
        with (
            mock.patch.object(audit_log_entry, "app") as patched_app,
            mock.patch.object(patched_app.rest, "fetch_user", new_callable=mock.AsyncMock) as patched_fetch_user,
        ):
            assert await audit_log_entry.fetch_user() is patched_fetch_user.return_value
            patched_fetch_user.assert_awaited_once_with(456)


class TestAuditLog:
    def test_iter(self):
        entry_1 = mock.Mock()
        entry_2 = mock.Mock()
        entry_3 = mock.Mock()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflakes.Snowflake(432123): entry_1,
                snowflakes.Snowflake(432654): entry_2,
                snowflakes.Snowflake(432888): entry_3,
            },
            integrations={},
            users={},
            threads={},
            webhooks={},
        )
        assert list(audit_log) == [entry_1, entry_2, entry_3]

    def test_get_item_with_index(self):
        entry = mock.Mock()
        entry_2 = mock.Mock()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflakes.Snowflake(432123): mock.Mock(),
                snowflakes.Snowflake(432654): entry,
                snowflakes.Snowflake(432888): mock.Mock(),
                snowflakes.Snowflake(677777): mock.Mock(),
                snowflakes.Snowflake(999999): entry_2,
            },
            integrations={},
            threads={},
            users={},
            webhooks={},
        )
        assert audit_log[1] is entry
        assert audit_log[4] is entry_2

    def test_get_item_with_slice(self):
        entry_1 = mock.Mock()
        entry_2 = mock.Mock()
        audit_log = audit_logs.AuditLog(
            entries={
                snowflakes.Snowflake(432123): mock.Mock(),
                snowflakes.Snowflake(432654): entry_1,
                snowflakes.Snowflake(432888): mock.Mock(),
                snowflakes.Snowflake(666666): entry_2,
                snowflakes.Snowflake(783452): mock.Mock(),
            },
            integrations={},
            threads={},
            users={},
            webhooks={},
        )
        assert audit_log[1:5:2] == (entry_1, entry_2)

    def test_len(self):
        audit_log = audit_logs.AuditLog(
            entries={
                snowflakes.Snowflake(432123): mock.Mock(),
                snowflakes.Snowflake(432654): mock.Mock(),
                snowflakes.Snowflake(432888): mock.Mock(),
                snowflakes.Snowflake(783452): mock.Mock(),
            },
            integrations={},
            threads={},
            users={},
            webhooks={},
        )
        assert len(audit_log) == 4
