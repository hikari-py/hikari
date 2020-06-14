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
import os as _os

IS_CI = "CI" in _os.environ

# Packaging
MAIN_PACKAGE = "hikari"
TEST_PACKAGE = "tests"

# Generating documentation and artifacts.
ARTIFACT_DIRECTORY = "public"
PAGES_DIRECTORY = "pages"
DOCUMENTATION_DIRECTORY = "docs"
ROOT_INDEX_SOURCE = "index.html"

# Linting and test configs.
FLAKE8_CODECLIMATE = "public/flake8.json"
FLAKE8_HTML = "public/flake8"
FLAKE8_TXT = "public/flake8.txt"
MYPY_INI = "mypy.ini"
MYPY_JUNIT_OUTPUT_PATH = _os.path.join(ARTIFACT_DIRECTORY, "mypy.xml")
PYDOCSTYLE_INI = "pydocstyle.ini"
PYTEST_INI = "pytest.ini"
PYTEST_HTML_OUTPUT_PATH = _os.path.join(ARTIFACT_DIRECTORY, "pytest.html")
COVERAGE_HTML_PATH = _os.path.join(ARTIFACT_DIRECTORY, "coverage", "html")
COVERAGE_JUNIT_PATH = _os.path.join(ARTIFACT_DIRECTORY, "tests.xml")
COVERAGE_INI = "coverage.ini"

# Deployment variables; these only apply to CI stuff specifically.
VERSION_FILE = _os.path.join(MAIN_PACKAGE, "_about.py")
API_NAME = "hikari"
GIT_SVC_HOST = "gitlab.com"
GIT_TEST_SSH_PATH = "git@gitlab.com"
AUTHOR = "Nekokatt"
ORIGINAL_REPO_URL = f"https://{GIT_SVC_HOST}/${AUTHOR}/{API_NAME}"
SSH_DIR = "~/.ssh"
SSH_PRIVATE_KEY_PATH = _os.path.join(SSH_DIR, "id_rsa")
SSH_KNOWN_HOSTS = _os.path.join(SSH_DIR, "known_hosts")
CI_ROBOT_NAME = AUTHOR
CI_ROBOT_EMAIL = "3903853-nekokatt@users.noreply.gitlab.com"
SKIP_CI_PHRASE = "[skip ci]"
SKIP_DEPLOY_PHRASE = "[skip deploy]"
SKIP_PAGES_PHRASE = "[skip pages]"
PROD_BRANCH = "master"
PREPROD_BRANCH = "staging"
REMOTE_NAME = "origin"
DISTS = ["sdist", "bdist_wheel"]
PYPI_REPO = "https://upload.pypi.org/legacy/"
PYPI = "https://pypi.org/"
PYPI_API = f"{PYPI}/pypi/{API_NAME}/json"

# Docker stuff
DOCKER_ENVS = [
    "python:3.8.0",
    "python:3.8.1",
    "python:3.8.2",
    "python:3.8.3",
    "python:3.9-rc",
]
