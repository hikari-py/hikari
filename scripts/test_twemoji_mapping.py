# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
DISCORD_EMOJI_MAPPING_URL = "https://static.emzi0767.com/misc/discordEmojiMap.min.json"


with tempfile.TemporaryDirectory() as tempdir:
    start = time.perf_counter()
    valid_emojis = []
    invalid_emojis = []

    resp = requests.get(DISCORD_EMOJI_MAPPING_URL)
    resp.encoding = "utf-8-sig"
    mapping = resp.json()["emojiDefinitions"]

    subprocess.check_call(f"git clone {TWEMOJI_REPO_BASE_URL} {tempdir} --depth=1", shell=True)
    known_files = [f.name for f in (pathlib.Path(tempdir) / "assets" / "72x72").iterdir()]

    n = len(mapping)
    for i, emoji in enumerate(mapping, start=1):
        emoji_surrogates = emoji["surrogates"]
        name = emoji["primaryName"]
        emoji = emojis.UnicodeEmoji.parse(emoji_surrogates)
        line_repr = f"{i}/{n} {name} " + " ".join(map(hex, map(ord, emoji_surrogates))) + " " + emoji.url

        if emoji.filename in known_files:
            valid_emojis.append((emoji_surrogates, name))
            print("[  OK  ]", line_repr)
        else:
            invalid_emojis.append(line_repr)
            print("[ FAIL ]", line_repr)

    print()
    print("Results")
    print("-------")
    print("Valid emojis:", len(valid_emojis))
    print("Invalid emojis:", len(invalid_emojis))

    for line_repr in invalid_emojis:
        print(" ", line_repr)

    print("Time taken", time.perf_counter() - start, "seconds")

    if invalid_emojis or not valid_emojis:
        exit(1)
