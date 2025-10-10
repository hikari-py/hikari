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

import datetime

import mock
import pytest

from hikari import scheduled_events
from hikari import snowflakes
from hikari import traits
from hikari import urls
from hikari.internal import routes


class TestScheduledEvent:
    @pytest.fixture
    def scheduled_event(self, hikari_app: traits.RESTAware) -> scheduled_events.ScheduledEvent:
        return scheduled_events.ScheduledEvent(
            app=hikari_app,
            id=snowflakes.Snowflake(123456),
            guild_id=snowflakes.Snowflake(654321),
            name="scheduled_event",
            description="scheduled_event_description",
            start_time=datetime.datetime.fromtimestamp(1000),
            end_time=datetime.datetime.fromtimestamp(2000),
            privacy_level=scheduled_events.EventPrivacyLevel.GUILD_ONLY,
            status=scheduled_events.ScheduledEventStatus.SCHEDULED,
            entity_type=scheduled_events.ScheduledEventType.VOICE,
            creator=mock.Mock(),
            user_count=3,
            image_hash="image_hash",
        )

    def test_make_image_url_format_set_to_deprecated_ext_argument_if_provided(
        self, scheduled_event: scheduled_events.ScheduledEvent
    ):
        scheduled_event.id = snowflakes.Snowflake(543123)
        scheduled_event.image_hash = "ododododo"

        with mock.patch.object(
            routes, "SCHEDULED_EVENT_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert scheduled_event.make_image_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, scheduled_event_id=543123, hash="ododododo", size=4096, file_format="JPEG", lossless=True
        )

    def test_image_url_property(self, scheduled_event: scheduled_events.ScheduledEvent):
        with mock.patch.object(scheduled_events.ScheduledEvent, "make_image_url") as patched_make_image_url:
            assert scheduled_event.image_url == patched_make_image_url.return_value

    def test_image_url(self, scheduled_event: scheduled_events.ScheduledEvent):
        scheduled_event.id = snowflakes.Snowflake(543123)
        scheduled_event.image_hash = "ododododo"
        with mock.patch.object(routes, "SCHEDULED_EVENT_COVER") as route:
            assert scheduled_event.make_image_url(file_format="JPEG", size=1) is route.compile_to_file.return_value

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, scheduled_event_id=543123, hash="ododododo", size=1, file_format="JPEG", lossless=True
        )

    def test_make_image_url_when_image_hash_is_none(self, scheduled_event: scheduled_events.ScheduledEvent):
        scheduled_event.image_hash = None

        with mock.patch.object(routes, "SCHEDULED_EVENT_COVER") as patched_scheduled_event_cover:
            assert scheduled_event.make_image_url(ext="JPEG", size=1) is None

        patched_scheduled_event_cover.assert_not_called()
