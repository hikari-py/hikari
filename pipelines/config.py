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
LOGO_SOURCE = "logo.png"

# Linting and test configs.
FLAKE8_JUNIT = "public/flake8-junit.xml"
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
DEV_BRANCH = "development"
REMOTE_NAME = "origin"
DISTS = ["sdist", "bdist_wheel"]
PYPI_REPO = "https://upload.pypi.org/legacy/"
PYPI = "https://pypi.org/"
PYPI_API = f"{PYPI}/pypi/{API_NAME}/json"
