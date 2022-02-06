#!/bin/sh
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
set -e

if [ $(ls -1 changes/*.*.md 2>/dev/null | wc -l) != 0 ]; then
    echo "Cannot create release if CHANGELOG fragment files exist under 'changes/'!" && exit 1
fi

echo "Defined environment variables"
env | grep -oP "^[^=]+" | sort

if [ -z ${VERSION+x} ]; then echo '$VERSION environment variable is missing' && exit 1; fi
if [ -z "${VERSION}" ]; then echo '$VERSION environment variable is empty' && exit 1; fi
if [ -z ${REF+x} ]; then echo '$REF environment variable is missing' && exit 1; fi
if [ -z "${REF}" ]; then echo '$REF environment variable is empty' && exit 1; fi
if [ -z ${GITHUB_TOKEN+x} ]; then echo '$GITHUB_TOKEN environment variable is missing' && exit 1; fi
if [ -z "${GITHUB_TOKEN}" ]; then echo '$GITHUB_TOKEN environment variable is empty' && exit 1; fi
if [ -z ${REPO_SLUG+x} ]; then echo '$REPO_SLUG environment variable is missing' && exit 1; fi
if [ -z "${REPO_SLUG}" ]; then echo '$REPO_SLUG environment variable is empty' && exit 1; fi
if [ -z ${DOCUMENTATION_REPO_SLUG+x} ]; then echo '$DOCUMENTATION_REPO_SLUG environment variable is missing' && exit 1; fi
if [ -z "${DOCUMENTATION_REPO_SLUG}" ]; then echo '$DOCUMENTATION_REPO_SLUG environment variable is empty' && exit 1; fi
if [ -z ${DEPLOY_WEBHOOK_URL+x} ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is missing' && exit 1; fi
if [ -z "${DEPLOY_WEBHOOK_URL}" ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is empty' && exit 1; fi
if [ -z ${TWINE_USERNAME+x} ]; then echo '$TWINE_USERNAME environment variable is missing' && exit 1; fi
if [ -z "${TWINE_USERNAME}" ]; then echo '$TWINE_USERNAME environment variable is empty' && exit 1; fi
if [ -z ${TWINE_PASSWORD+x} ]; then echo '$TWINE_PASSWORD environment variable is missing' && exit 1; fi
if [ -z "${TWINE_PASSWORD}" ]; then echo '$TWINE_PASSWORD environment variable is empty' && exit 1; fi

regex='__version__: typing\.Final\[str\] = "([^"]*)"'
if [[ $(cat hikari/_about.py) =~ $regex ]]; then
  if [ "${BASH_REMATCH[1]}" != "${VERSION}" ]; then
    echo "Variable '__version__' does not match the version this deploy is for! [__version__='${BASH_REMATCH[1]}'; VERSION='${VERSION}']" && exit 1
  fi
else
  echo "Variable '__version__' not found in about!" && exit 1
fi

echo "===== INSTALLING DEPENDENCIES ====="
# Note: We install each of these separately due to issues with the new PIP resolver
# https://github.com/pypa/pip/issues/9187
pip install setuptools
pip install wheel
pip install twine
pip install nox
pip install -r requirements.txt

echo "===== DEPLOYING TO PYPI ====="
echo "-- Setting __git_sha1__ (ref: ${REF}) --"
sed "/^__git_sha1__.*/, \${s||__git_sha1__: typing.Final[str] = \"${REF}\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__git_sha1__' not found in about!" && exit 1)
echo "=========================================================================="
cat hikari/_about.py
echo "=========================================================================="
python -m hikari
echo "=========================================================================="

python setup.py sdist bdist_wheel
echo "-- Contents of . --"
ls -ahl
echo
echo "-- Contents of ./dist --"
ls -ahl dist

echo "-- Checking generated dists --"
python -m twine check dist/*
echo
echo "-- Uploading to PyPI --"
python -m twine upload --disable-progress-bar --skip-existing dist/* --non-interactive --repository-url https://upload.pypi.org/legacy/

echo "===== DEPLOYING PAGES ====="
bash scripts/deploy-pages.sh

echo "===== SENDING WEBHOOK ====="
bash scripts/deploy-webhook.sh

echo "===== UPDATING VERSION IN REPOSITORY ====="
NEW_VERSION=$(python scripts/increase_version_number.py "${VERSION}")

echo "-- Setting up git --"
git fetch origin
git checkout -f master

echo "-- Bumping to development version (${NEW_VERSION}) --"
sed "/^__version__.*/, \${s||__version__: typing.Final[str] = \"${NEW_VERSION}\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__version__' not found in about!" && exit 1)
sed "/^__docs__.*/, \${s||__docs__: typing.Final[str] = \"https://docs.hikari-py.dev/master\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__docs__' not found in about!" && exit 1)

echo "-- Pushing to repository --"
git commit -am "Bump to development version (${NEW_VERSION})"
git push
