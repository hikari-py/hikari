#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import datetime
import math

import pytest

from hikari.state.models import presences


@pytest.fixture()
def no_presence():
    return {
        "user": {"id": "339767912841871360"},
        "status": "online",
        "game": None,
        "client_status": {"desktop": "online"},
        "activities": [],
    }


@pytest.fixture()
def presence_delta_empty():
    return {"user": {"id": "339767912841871360"}}


@pytest.fixture()
def presence_update():
    return {
        "user": {"id": "339767912841871360"},
        "status": "online",
        "game": None,
        "client_status": {"desktop": "online"},
        "activities": [],
        "roles": ["123", "456", "789"],
        "guild_id": "10987",
    }


@pytest.fixture()
def legacy_presence():
    return {
        "user": {"id": "506109712710762498"},
        "status": "online",
        "game": {
            "type": 0,
            "name": " Prefix [;] | Role Hex Code: #26f43a",
            "id": "ec0b28a579ecb4bd",
            "created_at": 1566116552964,
        },
        "client_status": {"web": "online"},
        "activities": [
            {
                "type": 0,
                "name": " Prefix [;] | Role Hex Code: #26f43a",
                "id": "ec0b28a579ecb4bd",
                "created_at": 1566116552964,
            }
        ],
    }


@pytest.fixture()
def rich_presence():
    return {
        "user": {"id": "537340989808050216"},
        "status": "online",
        "game": {
            "type": 0,
            "timestamps": {"start": 1566135892633},
            "state": "Workspace: No workspace.",
            "name": "Visual Studio Code",
            "id": "f6f10aa607d5cabb",
            "details": "Editing Untitled-2",
            "created_at": 1566135893878,
            "assets": {
                "small_text": "Code - OSS",
                "small_image": "565945770067623946",
                "large_text": "Editing a TXT file",
                "large_image": "565945769958572037",
            },
            "application_id": "383226320970055681",
        },
        "client_status": {"desktop": "online"},
        "activities": [
            {
                "type": 0,
                "timestamps": {"start": 1566135892633},
                "state": "Workspace: No workspace.",
                "name": "Visual Studio Code",
                "id": "f6f10aa607d5cabb",
                "details": "Editing Untitled-2",
                "created_at": 1566135893878,
                "assets": {
                    "small_text": "Code - OSS",
                    "small_image": "565945770067623946",
                    "large_text": "Editing a TXT file",
                    "large_image": "565945769958572037",
                },
                "application_id": "383226320970055681",
            }
        ],
    }


@pytest.fixture()
def assets():
    return {
        "small_text": "Using PyCharm",
        "small_image": "387095349199896578",
        "large_text": "Editing a Scratch file",
        "large_image": "565945769958572037",
    }


@pytest.fixture()
def party():
    return {"id": "1a2b3c", "current_size": 4, "max_size": 5}


@pytest.fixture()
def timestamps():
    return {"start": 1566116552964, "end": 1566135892633}


@pytest.fixture()
def rich_presence_activity(assets, party, timestamps):
    return {
        "type": 2,
        "state": "Working on hikari.core",
        "timestamps": timestamps,
        "name": "JetBrains IDE",
        "id": "197cdcbec495eb3f",
        "details": "Editing [Scratch] scratch_2.py",
        "created_at": 1566136493755,
        "assets": assets,
        "application_id": "384215522050572288",
        "flags": 3,
        "party": party,
    }


@pytest.fixture()
def legacy_presence_activity():
    return {
        "type": 0,
        "name": "with yo mama",
        "url": None,
    }


@pytest.mark.model
class TestPresence:
    def test_parse_no_Presence(self, no_presence):
        p = presences.Presence(no_presence)

        assert p.status == presences.Status.ONLINE
        assert p.desktop_status == presences.Status.ONLINE
        assert p.web_status == presences.Status.OFFLINE
        assert p.mobile_status == presences.Status.OFFLINE

        assert len(p.activities) == 0

    def test_parse_legacy_Presence(self, legacy_presence):
        p = presences.Presence(legacy_presence)

        assert p.status == presences.Status.ONLINE
        assert p.desktop_status == presences.Status.OFFLINE
        assert p.web_status == presences.Status.ONLINE
        assert p.mobile_status == presences.Status.OFFLINE

        assert len(p.activities) == 1
        a = p.activities[0]
        assert a is not None

    def test_rich_Presence(self, rich_presence):
        p = presences.Presence(rich_presence)

        assert p.status == presences.Status.ONLINE
        assert p.desktop_status == presences.Status.ONLINE
        assert p.web_status == presences.Status.OFFLINE
        assert p.mobile_status == presences.Status.OFFLINE

        assert len(p.activities) == 1
        a = p.activities[0]
        assert a is not None

    def test_Presence_update(self, presence_update):
        p = presences.Presence(presence_update)
        assert p.status == presences.Status.ONLINE
        assert p.desktop_status == presences.Status.ONLINE
        assert p.web_status == presences.Status.OFFLINE
        assert p.mobile_status == presences.Status.OFFLINE
        assert len(p.activities) == 0

    def test_Presence_delta_when_empty(self, presence_delta_empty):
        p = presences.Presence(presence_delta_empty)
        assert p.status == presences.Status.OFFLINE
        assert p.desktop_status == presences.Status.OFFLINE
        assert p.web_status == presences.Status.OFFLINE
        assert p.mobile_status == presences.Status.OFFLINE
        assert len(p.activities) == 0


@pytest.mark.model
def test_parse_PresenceActivity(legacy_presence_activity):
    a = presences.PresenceActivity(legacy_presence_activity)
    assert a.name == "with yo mama"
    assert a.type == presences.ActivityType.PLAYING


@pytest.mark.model
def test_parse_RichPresenceActivity(rich_presence_activity):
    a = presences.RichPresenceActivity(rich_presence_activity)
    assert a.type == presences.ActivityType.LISTENING
    assert a.timestamps is not None
    assert a.state == "Working on hikari.core"
    assert a.name == "JetBrains IDE"
    assert a.id == "197cdcbec495eb3f"
    assert a.details == "Editing [Scratch] scratch_2.py"
    assert a.assets is not None
    assert a.application_id == 384215522050572288
    assert a.flags & presences.ActivityFlag.INSTANCE
    assert a.flags & presences.ActivityFlag.JOIN
    assert a.party is not None


@pytest.mark.model
def test_parse_presence_activity_for_PresenceActivity(legacy_presence_activity):
    a = presences.parse_presence_activity(legacy_presence_activity)
    # It must be the class exactly, not a derivative.
    assert type(a) is presences.PresenceActivity


@pytest.mark.model
def test_parse_presence_activity_for_RichPresenceActivity(rich_presence_activity):
    a = presences.parse_presence_activity(rich_presence_activity)
    # It must be the class exactly, not a derivative.
    assert type(a) is presences.RichPresenceActivity


@pytest.mark.model
def test_parse_assets(assets):
    a = presences.ActivityAssets(assets)
    assert a.small_text == "Using PyCharm"
    assert a.small_image == "387095349199896578"
    assert a.large_text == "Editing a Scratch file"
    assert a.large_image == "565945769958572037"


@pytest.mark.model
def test_parse_party(party):
    p = presences.ActivityParty(party)
    assert p.id == "1a2b3c"
    assert p.current_size == 4
    assert p.max_size == 5


@pytest.mark.model
class TestActivityTimestamps:
    def test_parse_timestamps(self, timestamps):
        t = presences.ActivityTimestamps(timestamps)
        assert t.start == datetime.datetime(2019, 8, 18, 8, 22, 32, 964000, datetime.timezone.utc)
        assert t.end == datetime.datetime(2019, 8, 18, 13, 44, 52, 633000, datetime.timezone.utc)

    def test_duration(self, timestamps):
        t = presences.ActivityTimestamps(timestamps)
        assert math.isclose(t.duration.total_seconds(), 1566135892.633 - 1566116552.964)
