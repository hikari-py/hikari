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

import mock
import pytest

from hikari import voices
from hikari.events import voice_events


class TestVoiceStateUpdateEvent:
    @pytest.fixture
    def event(self):
        return voice_events.VoiceStateUpdateEvent(
            shard=object(), state=mock.Mock(voices.VoiceState), old_state=mock.Mock(voices.VoiceState)
        )

    def test_app_property(self, event):
        assert event.app is event.state.app

    def test_guild_id_property(self, event):
        event.state.guild_id = 123
        assert event.guild_id == 123

    def test_old_voice_state(self, event):
        event.old_state.guild_id = 123
        assert event.old_state.guild_id == 123


class TestVoiceServerUpdateEvent:
    @pytest.fixture
    def event(self):
        return voice_events.VoiceServerUpdateEvent(
            app=None, shard=object(), guild_id=123, token="token", raw_endpoint="voice.discord.com:123"
        )

    def test_endpoint_property(self, event):
        assert event.endpoint == "wss://voice.discord.com:123"

    def test_endpoint_property_when_raw_endpoint_is_None(self, event):
        event.raw_endpoint = None
        assert event.endpoint is None
