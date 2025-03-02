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

from hikari import stage_instances
from hikari.events import stage_events


class TestStageInstanceCreateEvent:
    @pytest.fixture
    def event(self):
        return stage_events.StageInstanceCreateEvent(shard=object(), stage_instance=mock.Mock())

    def test_app_property(self, event):
        assert event.app is event.stage_instance.app


class TestStageInstanceUpdateEvent:
    @pytest.fixture
    def event(self):
        return stage_events.StageInstanceUpdateEvent(
            shard=object(), stage_instance=mock.Mock(stage_instances.StageInstance)
        )

    def test_app_property(self, event):
        assert event.app is event.stage_instance.app


class TestStageInstanceDeleteEvent:
    @pytest.fixture
    def event(self):
        return stage_events.StageInstanceDeleteEvent(
            shard=object(), stage_instance=mock.Mock(stage_instances.StageInstance)
        )

    def test_app_property(self, event):
        assert event.app is event.stage_instance.app
