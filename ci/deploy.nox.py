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
"""Deployment scripts for CI only."""
import json
import os
import re
import shlex

from distutils.version import LooseVersion

from ci import config
from ci import nox


def update_version_string(version):
    print("Updating version in version file to", version)
    nox.shell("sed", shlex.quote(f's|^__version__.*|__version__ = "{version}"|g'), "-i", config.VERSION_FILE)


def increment_prod_to_next_dev(version):
    version_obj = LooseVersion(version)
    last_index = len(version_obj.version) - 1
    bits = [*map(str, version_obj.version[:last_index]), f"{version_obj.version[last_index] + 1}.dev"]
    next_dev = ".".join(bits)
    print(version, "prod version will be incremented to", next_dev)
    return next_dev


def get_current_version():
    with open(config.VERSION_FILE) as fp:
        fp_content = fp.read()

    aboutpy_v = LooseVersion(re.findall(r"^__version__\s*=\s*\"(.*?)\"", fp_content, re.M)[0])
    if not hasattr(aboutpy_v, "vstring"):
        print("Corrupt _about.py, using default version 0.0.0")
        current = "0.0.0"
    else:
        current = aboutpy_v.vstring
    print("Current version", current)
    return current


def get_next_prod_version_from_dev(version):
    bits = LooseVersion(version).version[:3]
    prod = ".".join(map(str, bits))
    print(version, "maps to prod release", prod)
    return prod


def get_next_dev_version(version):
    import requests

    version = LooseVersion(version)

    with requests.get(config.PYPI_API) as resp:
        print("Looking at existing versions on", config.PYPI_API)

        if resp.status_code == 404:
            print("Package does not seem to yet be deployed, using dummy values.")
            return "0.0.1.dev1"
        else:
            resp.raise_for_status()
            root = resp.json()
            print("Found existing versions online, so adjusting versions to follow from that where appropriate...")
            dev_releases = [LooseVersion(r) for r in root["releases"] if "dev" in r]
            same_micro_dev_releases = [r for r in dev_releases if r.version[:3] == version.version[:3]]
            latest_matching_staging_v = max(same_micro_dev_releases) if same_micro_dev_releases else version
            try:
                next_patch = latest_matching_staging_v.version[4] + 1
            except IndexError:
                # someone messed the version string up or something, meh, just assume it is fine.
                print(latest_matching_staging_v, "doesn't match a patch staging version, so just ignoring it")
                next_patch = 1
            print("Using next patch of", next_patch)
            bits = [*map(str, latest_matching_staging_v.version[:3]), f"dev{next_patch}"]
            return ".".join(bits)


def deploy_to_pypi() -> None:
    print("Performing PyPI deployment of current code")
    nox.shell("pip install -r requirements.txt twine")
    nox.shell("python", "setup.py", *config.DISTS)
    os.putenv("TWINE_USERNAME", os.environ["PYPI_USER"])
    os.putenv("TWINE_PASSWORD", os.environ["PYPI_PASS"])
    os.putenv("TWINE_REPOSITORY_URL", config.PYPI_REPO)
    dists = [os.path.join("dist", n) for n in os.listdir("dist")]
    nox.shell("twine", "upload", "--disable-progress-bar", "--skip-existing", *dists)


def deploy_to_git(next_version: str) -> None:
    print("Setting up the git repository ready to make automated changes")
    nox.shell("git config user.name", shlex.quote(config.CI_ROBOT_NAME))
    nox.shell("git config user.email", shlex.quote(config.CI_ROBOT_EMAIL))
    nox.shell(
        "git remote set-url",
        config.REMOTE_NAME,
        "$(echo \"$CI_REPOSITORY_URL\" | perl -pe 's#.*@(.+?(\\:\\d+)?)/#git@\\1:#')",
    )

    print("Making deployment commit")
    nox.shell(
        "git commit -am", shlex.quote(f"(ci) Deployed {next_version} to PyPI {config.SKIP_CI_PHRASE}"), "--allow-empty",
    )

    print("Tagging release")
    nox.shell("git tag", next_version)

    print("Merging prod back into preprod")
    nox.shell("git checkout", config.PREPROD_BRANCH)
    nox.shell(f"git reset --hard {config.REMOTE_NAME}/{config.PREPROD_BRANCH}")

    nox.shell(
        f"git merge {config.PROD_BRANCH}",
        "--no-ff --strategy-option theirs --allow-unrelated-histories -m",
        shlex.quote(f"(ci) Merged {config.PROD_BRANCH} {next_version} into {config.PREPROD_BRANCH}"),
    )
    update_version_string(increment_prod_to_next_dev(next_version))

    print("Making next dev commit on preprod")
    nox.shell(
        "git commit -am", shlex.quote(f"(ci) Updated version for next development release {config.SKIP_DEPLOY_PHRASE}")
    )
    nox.shell("git push --atomic", config.REMOTE_NAME, config.PREPROD_BRANCH, config.PROD_BRANCH, next_version)


def send_notification(version: str, title: str, description: str, color: str) -> None:
    print("Sending webhook to Discord")
    nox.shell(
        "curl",
        "-X POST",
        "-H",
        shlex.quote("Content-Type: application/json"),
        "-d",
        shlex.quote(
            json.dumps(
                {
                    "embeds": [
                        {
                            "title": title,
                            "description": description,
                            "author": {"name": config.AUTHOR},
                            "footer": {"text": f"v{version}"},
                            "url": f"{config.PYPI}project/{config.API_NAME}/{version}",
                            "color": int(color, 16),
                        }
                    ]
                }
            )
        ),
        os.environ["RELEASE_WEBHOOK"],
    )


@nox.session()
def deploy(session: nox.Session) -> None:
    """Perform a deployment. This will only work on the CI."""
    nox.shell("pip install requests")
    commit_ref = os.getenv("CI_COMMIT_REF_NAME", *session.posargs[0:1])
    print("Commit ref is", commit_ref)
    current_version = get_current_version()

    if commit_ref == config.PREPROD_BRANCH:
        print("preprod release!")
        next_version = get_next_dev_version(current_version)
        update_version_string(next_version)
        deploy_to_pypi()
        send_notification(
            next_version,
            f"{config.API_NAME} v{next_version} has been released",
            "Pick up the latest development release from pypi by running:\n"
            "```bash\n"
            f"pip install -U {config.API_NAME}=={next_version}\n"
            "```",
            "2C2F33",
        )
    elif commit_ref == config.PROD_BRANCH:
        print("prod release!")
        next_version = get_next_prod_version_from_dev(current_version)
        update_version_string(next_version)
        deploy_to_pypi()
        deploy_to_git(next_version)
        send_notification(
            next_version,
            f"{config.API_NAME} v{next_version} has been released",
            "Pick up the latest stable release from pypi by running:\n"
            "```bash\n"
            f"pip install -U {config.API_NAME}=={next_version}\n"
            "```",
            "7289DA",
        )
    else:
        print("not preprod or prod branch, nothing will be performed.")
