#!/usr/bin/env python3
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

import asyncio
import time
import sys

sys.path.append(".")

import aiohttp
import hikari


skipped_emojis = []
valid_emojis = []
invalid_emojis = []


async def run():
    start = time.perf_counter()

    async with aiohttp.request("get", "https://static.emzi0767.com/misc/discordEmojiMap.json") as resp:
        resp.raise_for_status()
        mapping = (await resp.json(encoding="utf-8-sig"))["emojiDefinitions"]

    semaphore = asyncio.Semaphore(value=100)

    tasks = []

    for i, emoji in enumerate(mapping):
        await semaphore.acquire()
        task = asyncio.create_task(try_fetch(i, len(mapping), emoji["surrogates"], emoji["primaryName"]))
        task.add_done_callback(lambda _: semaphore.release())
        tasks.append(task)

        if i and i % 750 == 0:
            print("Backing off so GitHub doesn't IP ban us")
            await asyncio.gather(*tasks)
            await asyncio.sleep(10)
            tasks.clear()

    await asyncio.gather(*tasks)

    print("Results")
    print("Valid emojis:", len(valid_emojis))
    print("Invalid emojis:", len(invalid_emojis))

    if skipped_emojis:
        print("Emojis may be skipped if persistent 5xx responses come from GitHub.")
        print("Skipped emojis:", len(skipped_emojis))

    for surrogates, name in invalid_emojis:
        print(*map(hex, map(ord, surrogates)), name)

    print("Time taken", time.perf_counter() - start, "seconds")


async def try_fetch(i, n, emoji_surrogates, name):
    emoji = hikari.UnicodeEmoji(name=emoji_surrogates)
    ex = None
    for _ in range(5):
        try:
            await emoji.__aiter__().__anext__()
        except Exception as _ex:
            ex = _ex
        else:
            ex = None
            break

    if isinstance(ex, hikari.errors.ServerHTTPErrorResponse):
        skipped_emojis.append((emoji_surrogates, name))
        print("[ SKIP ]", f"{i}/{n}", name, *map(hex, map(ord, emoji_surrogates)), emoji.url, str(ex))

    if ex is None:
        valid_emojis.append((emoji_surrogates, name))
        print("[  OK  ]", f"{i}/{n}", name, *map(hex, map(ord, emoji_surrogates)), emoji.url)
    else:
        invalid_emojis.append((emoji_surrogates, name))
        print("[ FAIL ]", f"{i}/{n}", name, *map(hex, map(ord, emoji_surrogates)), type(ex), ex, emoji.url)


asyncio.run(run())

if invalid_emojis or not valid_emojis:
    exit(1)
