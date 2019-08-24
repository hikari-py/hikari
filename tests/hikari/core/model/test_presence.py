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
import pytest


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
def game_presence():
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
            },
            {
                "type": 0,
                "state": "Working on hikari.core",
                "name": "JetBrains IDE",
                "id": "197cdcbec495eb3f",
                "details": "Editing [Scratch] scratch_2.py",
                "created_at": 1566136493755,
                "assets": {
                    "small_text": "Using PyCharm",
                    "small_image": "387095349199896578",
                    "large_text": "Editing a Scratch file",
                },
                "application_id": "384215522050572288",
            },
        ],
    }
