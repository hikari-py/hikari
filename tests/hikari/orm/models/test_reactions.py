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
from hikari.orm.http import base_http_adapter
from hikari.orm.models import channels
from hikari.orm.models import emojis
from hikari.orm.models import messages
from hikari.orm.models import reactions
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture
def fabric_impl():
    mock_state_registry = _helpers.create_autospec(base_registry.BaseRegistry)
    mock_http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
    mock_fabric = fabric.Fabric(state_registry=mock_state_registry, http_adapter=mock_http_adapter)
    return mock_fabric


@pytest.mark.model
class TestReaction:
    @pytest.fixture
    def mock_reaction(self, fabric_impl):
        return _helpers.create_autospec(
            reactions.Reaction, channel_id=2424242, message_id=55555555, _fabric=fabric_impl
        )

    def test_parse(self, fabric_impl):
        e = _helpers.mock_model(emojis.UnicodeEmoji)
        r = reactions.Reaction(fabric_impl, 9, e, 333, 66)
        assert r._fabric is fabric_impl
        assert r.emoji is e
        assert r.count == 9
        assert r.message_id == 333
        assert r.channel_id == 66

    @pytest.mark.asyncio
    async def test_fetch_channel(self, fabric_impl, mock_reaction):
        mock_channel = _helpers.mock_model(channels.Channel, is_resolved=True)
        fabric_impl.http_adapter.fetch_channel.return_value = mock_channel
        assert await reactions.Reaction.fetch_channel(mock_reaction) is mock_channel
        fabric_impl.http_adapter.fetch_channel.assert_called_once_with(channel=2424242)

    def test_get_channel(self, fabric_impl, mock_reaction):
        mock_channel = _helpers.mock_model(channels.Channel, is_resolved=True)
        fabric_impl.state_registry.get_channel_by_id.return_value = mock_channel
        assert reactions.Reaction.get_channel(mock_reaction) is mock_channel
        fabric_impl.state_registry.get_channel_by_id.assert_called_once_with(channel_id=2424242)

    @pytest.mark.asyncio
    async def test_fetch_message_rest_response(self, fabric_impl, mock_reaction):
        mock_message = mock.MagicMock(messages.Message, is_resolved=False)
        fabric_impl.http_adapter.fetch_message.return_value = mock_message
        assert await reactions.Reaction.fetch_message(mock_reaction) is mock_message
        fabric_impl.http_adapter.fetch_message.assert_called_once_with(channel=2424242, message=55555555)

    def test_get_message(self, fabric_impl, mock_reaction):
        mock_message = _helpers.mock_model(messages.Message, is_resolved=True)
        fabric_impl.state_registry.get_message_by_id.return_value = mock_message
        assert reactions.Reaction.get_message(mock_reaction) is mock_message
        fabric_impl.state_registry.get_message_by_id.assert_called_once_with(message_id=55555555)

    def test__repr__(self):
        assert repr(
            _helpers.mock_model(
                reactions.Reaction,
                count=42,
                emoji=_helpers.mock_model(emojis.UnicodeEmoji),
                message_id=21,
                channel_id=64,
                __repr__=reactions.Reaction.__repr__,
            )
        )
