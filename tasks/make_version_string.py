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
"""
Increments the next version
"""
import os
import re
import sys
import textwrap
from distutils.version import LooseVersion

import requests

log_message = lambda *a, **k: print(*a, **k, file=sys.stderr)

is_staging = len(sys.argv) > 1 and "staging" in sys.argv[1:]
is_pages = len(sys.argv) > 1 and "pages" in sys.argv[1:]

log_message("will use", "staging" if is_staging else "prod", "configuration for this next version")
if is_pages:
    log_message("will not bump versions up, this is just for gitlab pages.")

pypi_server = "pypi.org"
api_name = os.getenv("API_NAME", "hikari")
pypi_json_url = f"https://{pypi_server}/pypi/{api_name}/json"

# Inspect the version in pyproject.toml
if os.getenv("TEST_VERSION_STRING_VERSION_LINE"):
    fp_content = os.environ["TEST_VERSION_STRING_VERSION_LINE"]
else:
    with open(os.path.join(api_name, "_about.py")) as fp:
        fp_content = fp.read()


aboutpy_v = LooseVersion(re.findall(r"^__version__\s*=\s*\"(.*?)\"", fp_content, re.M)[0])
if not hasattr(aboutpy_v, "vstring"):
    log_message("corrupt _about.py, using default version 0.0.0")
    aboutpy_v = LooseVersion("0.0.0")

log_message("version in _about.py is", aboutpy_v)

with requests.get(pypi_json_url) as resp:
    log_message("looking at existing versions on", pypi_server)

    if resp.status_code == 404:
        log_message("package does not seem to yet be deployed, using dummy values.")
        releases = []
        dev_releases = []
        staging_releases_before_published_prod = 0
        latest_pypi_prod_v = LooseVersion("0.0.0")
        latest_pypi_staging_v = LooseVersion("0.0.1.dev0")
        latest_matching_staging_v = LooseVersion("0.0.1.dev0")
    else:
        resp.raise_for_status()
        root = resp.json()
        log_message("found existing versions online, so adjusting versions to follow from that where appropriate...")
        releases = [LooseVersion(r) for r in root["releases"]]
        dev_releases = [LooseVersion(r) for r in root["releases"] if "dev" in r]
        same_micro_dev_releases = [r for r in dev_releases if r.version[:3] == aboutpy_v.version[:3]]
        latest_pypi_prod_v = LooseVersion(root["info"]["version"])
        staging_releases_before_published_prod = len(
            [r for r in releases if r.version[:3] == latest_pypi_prod_v.version[:3]]
        )
        latest_pypi_staging_v = max(dev_releases)
        latest_matching_staging_v = max(same_micro_dev_releases) if same_micro_dev_releases else aboutpy_v

    log_message("there have been", len(releases), "total PyPI releases")
    log_message("...", len(dev_releases), "of these were to staging and", len(releases) - len(dev_releases),
                "were to prod")
    log_message("... the latest prod release on PyPI is", latest_pypi_prod_v)
    log_message(
        "... there were",
        staging_releases_before_published_prod,
        "staging releases before the most recent already-published prod version was released"
    )
    log_message("... the latest staging release on PyPI is", latest_pypi_staging_v)
    log_message("... the latest same-micro staging release on PyPI as in _about.py is", latest_matching_staging_v)

# Version that the about.py has ignoring the patches.
aboutpy_prod_v = LooseVersion(".".join(map(str, aboutpy_v.version[:3])))
log_message("_about.py represents a version that would result in", aboutpy_prod_v, "being released to prod")

if is_staging:
    if is_pages:
        # Just keep the main version bits and the `dev` but not the specific patch, as it is easier to work with.
        result_v = aboutpy_prod_v.vstring + ".dev"
    else:
        # staging release.
        # if we already have a pypi dev release with the same major.minor.micro as the one in _about.py, then
        # find the biggest number and add 1 to the patch.
        try:
            next_patch = latest_matching_staging_v.version[4] + 1
        except IndexError:
            # someone messed the version string up or something, meh, just assume it is fine.
            log_message(latest_matching_staging_v, "doesn't match a patch staging version, so just ignoring it")
            next_patch = 1
        log_message("using next patch of", next_patch)
        bits = [*map(str, latest_matching_staging_v.version[:3]), f"dev{next_patch}"]
        result_v = LooseVersion(".".join(bits))
else:
    if not is_pages:
        # ignore what is on PyPI and just use the aboutpy_prod_version, unless it is on the releases list, then
        # panic and ask Nekokatt or someone to fix their version number.
        if aboutpy_prod_v in releases:
            log_message(textwrap.dedent(f"""
                HEY!!
            
                The _about.py contains a version of {aboutpy_v}. This implies the next prod upload should be for
                {aboutpy_prod_v}.

                Unfortunately, you have already published this version, so I can't republish it!

                Please rectify this issue manually and try again...
            """))
            sys.exit(1)

    # use the resultant prod version
    result_v = aboutpy_prod_v

log_message("resultant version", result_v)
print(result_v)
