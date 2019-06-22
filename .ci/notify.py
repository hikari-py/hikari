#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import requests
import sys

WEBHOOK_URL = os.environ["RELEASE_WEBHOOK"]
ENVIRONMENT = os.environ["RELEASE_WEBHOOK_NAME"]
COLOUR = os.environ["RELEASE_WEBHOOK_COLOUR"]
VERSION = sys.argv[1]

requests.post(
    WEBHOOK_URL,
    json={
        "embeds": [
            {
                "title": f"[{VERSION}] New {ENVIRONMENT} deployment!",
                "description": f"Hikari v{VERSION} has just been put into {ENVIRONMENT}.",
                "color": int(COLOUR, 16),
                "author": {"name": "Nekoka.tt"}
            }
        ]
    }
)
