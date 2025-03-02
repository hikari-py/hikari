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

from hikari import snowflakes
from hikari import stage_instances


@pytest.fixture
def mock_app():
    return mock.Mock()


class TestStageInstance:
    @pytest.fixture
    def stage_instance(self, mock_app):
        return stage_instances.StageInstance(
            app=mock_app,
            id=snowflakes.Snowflake(123),
            channel_id=snowflakes.Snowflake(6969),
            guild_id=snowflakes.Snowflake(420),
            topic="beanos",
            privacy_level=stage_instances.StageInstancePrivacyLevel.GUILD_ONLY,
            discoverable_disabled=True,
            scheduled_event_id=snowflakes.Snowflake(1337),
        )

    def test_id_property(self, stage_instance):
        assert stage_instance.id == 123

    def test_app_property(self, stage_instance, mock_app):
        assert stage_instance.app is mock_app

    def test_channel_id_property(self, stage_instance):
        assert stage_instance.channel_id == 6969

    def test_guild_id_property(self, stage_instance):
        assert stage_instance.guild_id == 420

    def test_topic_property(self, stage_instance):
        assert stage_instance.topic == "beanos"

    def test_privacy_level_property(self, stage_instance):
        assert stage_instance.privacy_level == stage_instances.StageInstancePrivacyLevel.GUILD_ONLY

    def test_discoverable_disabled_property(self, stage_instance):
        assert stage_instance.discoverable_disabled is True

    def test_guild_scheduled_event_id_property(self, stage_instance):
        assert stage_instance.scheduled_event_id == 1337
