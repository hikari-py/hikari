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
Increments the next version
"""
import datetime
import os
import re
import sys

from distutils.version import LooseVersion

import requests


is_staging = len(sys.argv) > 1 and sys.argv[1].casefold() == "staging"
print("Will use", "staging" if is_staging else "prod", "configuration for this next version", file=sys.stderr)
pypi_server = "pypi.org"
api_name = os.environ["API_NAME"]
pypi_json_url = f"https://{pypi_server}/pypi/{api_name}/json"

print("Querying API at", pypi_json_url, file=sys.stderr)

with requests.get(pypi_json_url) as resp:
    print("Looking at versions on", pypi_server, file=sys.stderr)

    if resp.status_code == 404:
        print("Package not yet been deployed?", file=sys.stderr)
        data = []
    else:
        resp.raise_for_status()
        data = resp.json()["releases"]


# Inspect the version in pyproject.toml
with open("pyproject.toml") as fp:
    previous_version = re.findall(r"^version\s*=\s*\"(.*?)\"", fp.read(), re.M)[0]
    previous_version_parts = re.match(r"(\d+)\.(\d+)\.(\d+)", previous_version)
    previous_major = int(previous_version_parts.group(1)) if previous_version_parts else 0
    previous_minor = int(previous_version_parts.group(2)) if previous_version_parts else 0
    previous_micro = int(previous_version_parts.group(3)) if previous_version_parts else 0

if is_staging:
    # If development, we release a patch.
    # Increment staging version to next version, as that is sensible
    previous_micro += 1

    current_dev_releases = [
        LooseVersion(v) for v in data if v.startswith(f"{previous_major}.{previous_minor}.{previous_micro}")
    ]

    print("Releases under this major/minor/micro combination are:", *[v.version for v in current_dev_releases],
          file=sys.stderr)

    if current_dev_releases:
        latest = max(current_dev_releases)
        latest_patch = latest.version[-1] + 1
    else:
        latest_patch = 1

    current_version = f"{previous_major}.{previous_minor}.{previous_micro}.dev{latest_patch}"
    print("Will use patch version", current_version, file=sys.stderr)

else:
    # Prod uses semver, this has some special rules annoyingly.

    # If prod, we use semver
    if len(data) == 0:
        current_version = "0.0.1"
        print("There was no previous release", file=sys.stderr)
    else:
        releases = [LooseVersion(version) for version in data]
        non_dev_releases = [r for r in releases if all(isinstance(number, int) for number in r.version)]
        most_major_release = max(non_dev_releases)
        print("Most recent non-dev PyPi release was", most_major_release, file=sys.stderr)
        major, minor, micro = most_major_release.version[:3]

        if major == previous_major and minor == previous_minor:
            print("We are just incrementing the micro version, as major and minor is the same", file=sys.stderr)
            # If it is a micro version release (most of the time it will be), increment the minor version
            current_version = '.'.join(map(str, [major, minor, micro + 1]))
        else:
            print("We are using the version in pyproject.toml as a major or minor version isn't the same. "
                  "If this fails, please update the file manually.", file=sys.stderr)
            # Else we should use the version in pyproject.toml, as something is being changed.
            current_version = previous_version

print("This version should be set to", current_version, file=sys.stderr)
print(current_version)
