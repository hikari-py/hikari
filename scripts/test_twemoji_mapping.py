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

import discord_emojis

sys.path.append(".")


from hikari import emojis

TWEMOJI_REPO_BASE_URL = "https://github.com/twitter/twemoji.git"


with tempfile.TemporaryDirectory() as tempdir:
    start = time.perf_counter()
    valid_emojis = []
    invalid_emojis = []

    subprocess.check_call(f"git clone {TWEMOJI_REPO_BASE_URL} {tempdir} --depth=1", shell=True)
    known_files = [f.name for f in (pathlib.Path(tempdir) / "assets" / "72x72").iterdir()]

    emoji_list = discord_emojis.EMOJIS
    n = len(emoji_list)
    for i, emoji_surrogates in enumerate(emoji_list, start=1):
        emoji = emojis.UnicodeEmoji.parse(emoji_surrogates)

        if emoji.filename in known_files:
            valid_emojis.append(emoji_surrogates)
            print("[  OK  ]", f"{i}/{n}", *map(hex, map(ord, emoji_surrogates)), emoji.url)
        else:
            invalid_emojis.append(emoji_surrogates)
            print("[ FAIL ]", f"{i}/{n}", *map(hex, map(ord, emoji_surrogates)), emoji.url)

    print("Results")
    print("Valid emojis:", len(valid_emojis))
    print("Invalid emojis:", len(invalid_emojis))

    for surrogates in invalid_emojis:
        print(*map(hex, map(ord, surrogates)))

    print("Time taken", time.perf_counter() - start, "seconds")

    if invalid_emojis or not valid_emojis:
        exit(1)
