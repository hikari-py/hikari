#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notify on Discord via a webhook that a new version has been released to PyPi.
"""
import os
import sys

import requests

WEBHOOK_URL = os.environ["RELEASE_WEBHOOK"]
ENVIRONMENT = os.environ["RELEASE_WEBHOOK_NAME"]
COLOUR = os.environ["RELEASE_WEBHOOK_COLOUR"]
DESCRIPTION = os.environ["RELEASE_WEBHOOK_DESCRIPTION"]
VERSION = sys.argv[1]

requests.post(
    WEBHOOK_URL,
    json={
        "embeds": [
            {
                "title": f"[{VERSION}] New {ENVIRONMENT} deployment!",
                "description": f"Hikari v{VERSION} has just been put into {ENVIRONMENT}.",
                "color": int(COLOUR, 16),
                "author": {"name": "Nekoka.tt"},
                "footer": {"text": DESCRIPTION}
            }
        ]
    }
)
