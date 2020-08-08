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
"""Deployment scripts for CI only."""
import json
import os
import re
import shlex
import subprocess
from distutils.version import LooseVersion

from pipelines import config
from pipelines import nox


def update_version_string(version):
    git_sha1 = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], universal_newlines=True, stderr=subprocess.DEVNULL,
    )[:8]

    git_branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], universal_newlines=True, stderr=subprocess.DEVNULL,
    )[:-1]

    git_when = subprocess.check_output(
        ["git", "log", "-1", '--date=format:"%Y/%m/%d"', '--format="%ad"'],
        universal_newlines=True,
        stderr=subprocess.DEVNULL,
    )[:-1]

    print("Updating version in version file to", version)
    nox.shell("sed", shlex.quote(f's|^__version__.*|__version__ = "{version}"|g'), "-i", config.VERSION_FILE)
    print("Updating branch in version file to", git_branch)
    nox.shell("sed", shlex.quote(f's|^__git_branch__.*|__git_branch__ = "{git_branch}"|g'), "-i", config.VERSION_FILE)
    print("Updating sha1 in version file to", git_sha1)
    nox.shell("sed", shlex.quote(f's|^__git_sha1__.*|__git_sha1__ = "{git_sha1}"|g'), "-i", config.VERSION_FILE)
    print("Updating timestamp in version file to", git_when)
    nox.shell("sed", shlex.quote(f's|^__git_when__.*|__git_when__ = "{git_when}"|g'), "-i", config.VERSION_FILE)


def set_official_release_flag(value: bool):
    print("Marking as", "official" if value else "unofficial", "release")
    nox.shell(
        "sed",
        shlex.quote(f's|^__is_official_distributed_release__.*|__is_official_distributed_release__ = "{value}"|g'),
        "-i",
        config.VERSION_FILE,
    )


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


def init_git() -> None:
    print("Setting up the git repository ready to make automated changes")
    nox.shell("git config user.name", shlex.quote(config.CI_ROBOT_NAME))
    nox.shell("git config user.email", shlex.quote(config.CI_ROBOT_EMAIL))
    nox.shell(
        "git remote set-url",
        config.REMOTE_NAME,
        "$(echo \"$CI_REPOSITORY_URL\" | perl -pe 's#.*@(.+?(\\:\\d+)?)/#git@\\1:#')",
    )


def deploy_to_git(next_version: str) -> None:
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


def rebase_development() -> None:
    print("Merging preprod back into dev")
    nox.shell("git checkout", config.DEV_BRANCH)
    nox.shell(f"git reset --hard {config.REMOTE_NAME}/{config.DEV_BRANCH}")

    nox.shell(f"git rebase {config.PREPROD_BRANCH}")
    nox.shell("git push", config.REMOTE_NAME, config.DEV_BRANCH, "-f", "-o", "ci.skip")


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
def stubgen_hack(session: nox.Session) -> None:
    session.install("-r", "mypy-requirements.txt", "-r", "requirements.txt")

    # MyPy seems to struggle to understand what is exported from `hikari/__init__.py`
    # due to disabling implicit exports in strict mode.
    # This works around the issue by injecting a helpful stub. Saves risk of error
    # and verbosity later by having to hard code 200 classes into an `__all__`
    # list manually.
    print("Generating stub workaround for __init__.py to allow --strict usage.")

    # Sniff license header from __init__.py
    header = []
    with open(os.path.join(config.MAIN_PACKAGE, "__init__.py")) as fp:
        while (line := fp.readline()).startswith("#") or not line.strip():
            header.append(line.rstrip())

    header = "\n".join(
        (
            *header,
            "\n",
            "# This stubfile is generated by Hikari's deploy script as a workaround\n"
            "# for our design not working correctly with MyPy's --strict flag. By\n"
            "# explicitly generating this stub, MyPy no longer gets confused by what\n"
            "# members are re-exported by package level init scripts. This lets you\n"
            "# type check as strictly as possible and still get correct results.\n"
            "#\n"
            "# For all other purposes, you can completely ignore this file!\n",
            "\n",
        )
    )

    for root, dirs, files in os.walk(config.MAIN_PACKAGE, topdown=True, followlinks=False):
        for f in files:
            if f == "__init__.py":
                module = ".".join(root.split(os.sep))
                file = os.path.join(root, f) + "i"
                nox.run("stubgen", "-m", module, "-o", ".")

                print("Adding license header to stub", file, "for module", module)
                with open(file) as fp:
                    stub = fp.read()

                with open(file, "w") as fp:
                    fp.write(header)
                    fp.write(stub)


@nox.session()
def deploy(session: nox.Session) -> None:
    """Perform a deployment. This will only work on the CI."""
    print("Injecting stubgen hack to allow for --strict in MyPy for users")
    nox.registry["stubgen-hack"](session)

    print("Re-running code formatting fixes")
    nox.registry["reformat-code"](session)

    nox.shell("pip install requests")

    commit_ref = os.getenv("CI_COMMIT_REF_NAME", *session.posargs[0:1])
    print("Commit ref is", commit_ref)
    current_version = get_current_version()

    init_git()
    if commit_ref == config.PREPROD_BRANCH:
        print("preprod release!")
        next_version = get_next_dev_version(current_version)
        update_version_string(next_version)
        set_official_release_flag(True)
        deploy_to_pypi()
        set_official_release_flag(False)
        send_notification(
            next_version,
            f"{config.API_NAME} v{next_version} has been released",
            "Pick up the latest development release from pypi by running:\n"
            "```bash\n"
            f"pip install -U {config.API_NAME}=={next_version}\n"
            "```",
            "2C2F33",
        )
        rebase_development()
    elif commit_ref == config.PROD_BRANCH:
        print("prod release!")
        next_version = get_next_prod_version_from_dev(current_version)
        update_version_string(next_version)
        set_official_release_flag(True)
        deploy_to_pypi()
        set_official_release_flag(False)
        send_notification(
            next_version,
            f"{config.API_NAME} v{next_version} has been released",
            "Pick up the latest stable release from pypi by running:\n"
            "```bash\n"
            f"pip install -U {config.API_NAME}=={next_version}\n"
            "```",
            "7289DA",
        )
        deploy_to_git(next_version)
        rebase_development()
    else:
        print("not preprod or prod branch, nothing will be performed.")
