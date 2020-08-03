# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""A CI-used script that tests all the Twemoji URLs generated
by Discord emojis are actually legitimate URLs, since Discord
does not map these on a 1-to-1 basis.
"""

import pathlib
import subprocess
import sys
import tempfile
import time

import requests

sys.path.append(".")


from hikari.models import emojis

TWEMOJI_REPO_BASE_URL = "https://github.com/twitter/twemoji.git"

valid_emojis = []
invalid_emojis = []


def run():
    start = time.perf_counter()

    resp = requests.get("https://static.emzi0767.com/misc/discordEmojiMap.json")
    resp.encoding = "utf-8-sig"
    mapping = resp.json()["emojiDefinitions"]

    subprocess.check_call(f"git clone {TWEMOJI_REPO_BASE_URL} {tempdir}", shell=True)

    for i, emoji in enumerate(mapping):
        try_fetch(i, len(mapping), emoji["surrogates"], emoji["primaryName"])

    print("Results")
    print("Valid emojis:", len(valid_emojis))
    print("Invalid emojis:", len(invalid_emojis))

    for surrogates, name in invalid_emojis:
        print(*map(hex, map(ord, surrogates)), name)

    print("Time taken", time.perf_counter() - start, "seconds")


def try_fetch(i, n, emoji_surrogates, name):
    emoji = emojis.UnicodeEmoji.from_emoji(emoji_surrogates)
    path = pathlib.Path(tempdir) / "assets" / "72x72" / emoji.filename

    if path.is_file():
        valid_emojis.append((emoji_surrogates, name))
        print("\033[1;32m[  OK  ]\033[0m", f"{i}/{n}", name, *map(hex, map(ord, emoji_surrogates)), emoji.url)
    else:
        invalid_emojis.append((emoji_surrogates, name))
        print("\033[1;31m[ FAIL ]\033[0m", f"{i}/{n}", name, *map(hex, map(ord, emoji_surrogates)), emoji.url)


with tempfile.TemporaryDirectory() as tempdir:
    run()

if invalid_emojis or not valid_emojis:
    exit(1)
