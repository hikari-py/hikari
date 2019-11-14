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
Pushes a release to GitLab via the release API.
"""
import contextlib
import io
import os
import subprocess
import sys
import traceback

from distutils.version import LooseVersion

import gcg.entrypoint
import requests

api_name = sys.argv[1]
release = sys.argv[2]
project_id = os.getenv("CI_PROJECT_ID", 0)
# Personal access token with read/write API scope.
token = os.environ["GITLAB_RELEASE_TOKEN"]


def get_most_recent_tag_hash():
    subprocess.check_call("git", "fetch", "--tags", "--all")
    version = LooseVersion(release).version
    # We did a new release...
    version[-1] -= 1
    return '.'.join(map(str, version))
    


def try_to_get_changelog():
    sio = io.StringIO()
    try:
        with contextlib.redirect_stdout(sio):
            gcg.entrypoint.main([sys.argv[0], "-O", "rpm", "-s", get_most_recent_tag_hash()])
        return sio.getvalue()
    except Exception as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
        with contextlib.redirect_stdout(sio):
            gcg.entrypoint.main(["-O", "rpm"])
    finally:
        return sio.getvalue()


change_log = try_to_get_changelog()

headers = {
    "PRIVATE-TOKEN": token,
    "Content-Type": "application/json",
}

payload = {
    "name": release,
    "tag_name": release,
    "description": change_log,
    "assets": {
        "links": [
            {"name": "PyPI package", "url": f"https://pypi.org/project/{api_name}/{release}"}
        ]
    }
}

print("Sending payload", payload)

with requests.post(f"https://gitlab.com/api/v4/projects/{project_id}/releases", json=payload, headers=headers) as resp:
    resp.raise_for_status()
    print(resp.status_code, resp.reason)
    print(resp.json())
