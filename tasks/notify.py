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
"""
Notify on Discord via a webhook that a new version has been released to PyPi.
"""
import os
import sys
import traceback

import requests

try:
    WEBHOOK_URL = os.environ["RELEASE_WEBHOOK"]
    ENVIRONMENT = os.environ["RELEASE_WEBHOOK_NAME"]
    COLOUR = os.environ["RELEASE_WEBHOOK_COLOUR"]
    DESCRIPTION = os.environ["RELEASE_WEBHOOK_DESCRIPTION"]
    VERSION = sys.argv[1]
    NAME = sys.argv[2]

    requests.post(
        WEBHOOK_URL,
        json={
            "embeds": [
                {
                    "title": f"[{VERSION}] New {ENVIRONMENT} deployment!",
                    "footer": {"text": f"{NAME} v{VERSION} has just been put into {ENVIRONMENT}."},
                    "color": int(COLOUR, 16),
                    "author": {"name": "Nekoka.tt"},
                    "description": DESCRIPTION,
                }
            ]
        },
    )
except BaseException:
    traceback.print_exc()
