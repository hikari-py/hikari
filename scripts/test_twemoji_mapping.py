# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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


from hikari import emojis

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
        print("[  OK  ]", f"{i}/{n}", name, *map(hex, map(ord, emoji_surrogates)), emoji.url)
    else:
        invalid_emojis.append((emoji_surrogates, name))
        print("[ FAIL ]", f"{i}/{n}", name, *map(hex, map(ord, emoji_surrogates)), emoji.url)


with tempfile.TemporaryDirectory() as tempdir:
    run()

if invalid_emojis or not valid_emojis:
    exit(1)
