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
import os

import requests

if os.getenv("CI"):
    webhook_url = os.environ["DEPLOY_WEBHOOK_URL"]
    tag = os.environ["GITHUB_TAG"]
    build_no = os.environ["GITHUB_BUILD_NUMBER"]
    commit_sha = os.environ["GITHUB_SHA"]

    payload = dict(
        username="Github Actions",
        embeds=[
            dict(
                title=f"{tag} has been deployed to PyPI",
                color=0x663399,
                description="Install it now!",
                footer=dict(text=f"#{build_no} | {commit_sha}"),
            )
        ],
    )

    with requests.post(webhook_url, json=payload) as resp:
        print("POST", payload)
        print(resp.status_code, resp.reason)
        try:
            print(resp.json())
        except:
            print(resp.content)
else:
    print("Skipping webhook, not on CI.")
