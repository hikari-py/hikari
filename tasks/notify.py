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
    VERSION = sys.argv[1]
    NAME = sys.argv[2]
    DEPLOYMENT_HOST = sys.argv[3]
    WEBHOOK_URL = os.environ["RELEASE_WEBHOOK"]
    ENVIRONMENT = os.environ["RELEASE_WEBHOOK_NAME"]
    COLOUR = os.environ["RELEASE_WEBHOOK_COLOUR"]
    DESCRIPTION = os.environ["RELEASE_WEBHOOK_DESCRIPTION"]
    BRIEF = f"**[{VERSION}] New {ENVIRONMENT} deployment!**"
    AUTHOR = os.environ["REPO_AUTHOR"]

    requests.post(
        WEBHOOK_URL,
        json = {
            "embeds": [
                {
                    "title": NAME,
                    "footer": {
                        "text": BRIEF + "\n\n" + DESCRIPTION,
                    },
                    "color": int(COLOUR, 16),
                    "author": {"name": AUTHOR},
                    "description": f"[{NAME} v{VERSION}]({DEPLOYMENT_HOST}/project/{NAME}/{VERSION}) has "
                                   f"just been put into {ENVIRONMENT}."
                }
            ]
        },
    )
except BaseException as ex:
    traceback.print_exception(type(ex), ex, ex.__traceback__)
