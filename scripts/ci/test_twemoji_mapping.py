# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

sys.path.append("..")


from hikari import emojis

TWEMOJI_REPO_BASE_URL = "https://github.com/discord/twemoji.git"
DISCORD_EMOJI_MAPPING_URL = "https://emzi0767.gl-pages.emzi0767.dev/discord-emoji/discordEmojiMap-canary.min.json"

try:
    tempdir = pathlib.Path(sys.argv[1])
except IndexError:
    print("Argument 1 must be the path to the temporary directory")
    exit(2)


start = time.perf_counter()

has_items = next(tempdir.iterdir(), False)
if has_items:
    print("Updating twemoji collection")
    subprocess.check_call("git pull", shell=True, cwd=tempdir)
else:
    print("Cloning twemoji collection")
    subprocess.check_call(f"git clone {TWEMOJI_REPO_BASE_URL} {tempdir} --depth=1", shell=True)

print("Fetching emoji mapping")
with urllib.request.urlopen(DISCORD_EMOJI_MAPPING_URL) as request:
    mapping = json.loads(request.read())["emojiDefinitions"]

assets_path = tempdir / "assets" / "72x72"

invalid_emojis = []
total = len(mapping)
for i, emoji in enumerate(mapping, start=1):
    name = emoji["primaryName"]
    emoji_surrogates = emoji["surrogates"]
    emoji = emojis.UnicodeEmoji.parse(emoji_surrogates)
    line_repr = f"{i}/{total} {name} {' '.join(map(hex, map(ord, emoji_surrogates)))} {emoji.url}"

    if (assets_path / emoji.filename).exists():
        print(f"[  OK  ] {line_repr}")
    else:
        invalid_emojis.append(line_repr)
        print(f"[ FAIL ] {line_repr}")

print("")
print("Results")
print("-------")
print(f"Valid emojis: {total - len(invalid_emojis)}")
print(f"Invalid emojis: {len(invalid_emojis)}")

for line_repr in invalid_emojis:
    print(f"  {line_repr}")

print(f"Took {time.perf_counter() - start} seconds")

if invalid_emojis or total == 0:
    exit(1)
