# -*- coding: utf-8 -*-
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
import pytest
import mock

from hikari import templates
from hikari import undefined
from hikari import users


class TestTemplate:
    @pytest.fixture()        
    def mock_user(self):
        return mock.Mock(return_value=users.User)
    
    @pytest.fixture()
    def obj(self, mock_user):
        return templates.Template(
            code="abc123",
            name="Test Template",
            description="Template used for testing",
            usage_count=101,
            creator=mock_user,
            created_at=object(),
            updated_at=object(),
            source_guild=object(),
            is_unsynced=True,
        )
    
    @pytest.mark.asyncio()            
    async def test_fetch_self(self, obj):
        obj.creator.app.rest.fetch_template = mock.AsyncMock()
        fetch_self = await obj.fetch_self()
        obj.creator.app.rest.fetch_template.assert_awaited_once()
        
        assert fetch_self == obj.creator.app.rest.fetch_template.return_value

    @pytest.mark.asyncio()
    async def test_edit(self, obj):
        obj.creator.app.rest.edit_template = mock.AsyncMock()
        edit = await obj.edit(name="Test Template 2", description="Electric Boogaloo")
        obj.creator.app.rest.edit_template.assert_awaited_once_with(obj.source_guild, obj, name="Test Template 2", description="Electric Boogaloo")
        
        assert edit == obj.creator.app.rest.edit_template.return_value
    
    @pytest.mark.asyncio()
    async def test_delete(self, obj):
        mock_template = mock.Mock(templates.Template)
        obj.creator.app.rest.delete_template = mock.AsyncMock(return_value=mock_template)
        deleted_template = await obj.delete()
        obj.creator.app.rest.delete_template.assert_awaited_once_with(obj.source_guild, obj)
    
    @pytest.mark.asyncio()
    async def test_sync(self, obj):
        obj.creator.app.rest.sync_guild_template = mock.AsyncMock()
        sync = await obj.sync()
        obj.creator.app.rest.sync_guild_template.assert_awaited_once()
        
        assert sync == obj.creator.app.rest.sync_guild_template.return_value
    
    @pytest.mark.asyncio()
    async def test_create_guild(self, obj):
        obj.creator.app.rest.create_guild_from_template = mock.AsyncMock()
        create_guild = await obj.create_guild(name="Test guild", icon="https://avatars.githubusercontent.com/u/72694042")
        obj.creator.app.rest.create_guild_from_template.assert_awaited_once_with(obj, "Test guild", icon="https://avatars.githubusercontent.com/u/72694042")
        
        assert create_guild == obj.creator.app.rest.create_guild_from_template.return_value

    def test_str(self, obj):
        assert str(obj) == "https://discord.new/abc123"
