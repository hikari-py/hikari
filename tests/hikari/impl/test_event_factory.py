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
import mock
import pytest

from hikari import traits
from hikari.events import interaction_events
from hikari.impl import event_factory as event_factory_


class TestEventFactoryImpl:
    @pytest.fixture()
    def mock_app(self):
        return mock.Mock(traits.RESTAware)

    @pytest.fixture()
    def mock_shard(self):
        return mock.Mock(traits.ShardAware)

    @pytest.fixture()
    def event_factory(self, mock_app):
        return event_factory_.EventFactoryImpl(mock_app)

    ######################
    # INTERACTION EVENTS #
    ######################

    def test_deserialize_command_create_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "123"}

        result = event_factory.deserialize_command_create_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_command.assert_called_once_with(payload)
        assert result.app is mock_app
        assert result.shard is mock_shard
        assert result.command is mock_app.entity_factory.deserialize_command.return_value
        assert isinstance(result, interaction_events.CommandCreateEvent)

    def test_deserialize_command_update_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "12344"}

        result = event_factory.deserialize_command_update_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_command.assert_called_once_with(payload)
        assert result.app is mock_app
        assert result.shard is mock_shard
        assert result.command is mock_app.entity_factory.deserialize_command.return_value
        assert isinstance(result, interaction_events.CommandUpdateEvent)

    def test_deserialize_command_delete_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "1561232344"}

        result = event_factory.deserialize_command_delete_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_command.assert_called_once_with(payload)
        assert result.app is mock_app
        assert result.shard is mock_shard
        assert result.command is mock_app.entity_factory.deserialize_command.return_value
        assert isinstance(result, interaction_events.CommandDeleteEvent)

    def test_deserialize_interaction_create_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "1561232344"}

        result = event_factory.deserialize_interaction_create_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_interaction.assert_called_once_with(payload)
        assert result.app is mock_app
        assert result.shard is mock_shard
        assert result.interaction is mock_app.entity_factory.deserialize_interaction.return_value
        assert isinstance(result, interaction_events.InteractionCreateEvent)
