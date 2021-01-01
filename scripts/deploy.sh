#!/bin/sh
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
set -e

echo "Defined environment variables"
env | grep -oP "^[^=]+" | sort

if [ -z ${GITHUB_TAG+x} ]; then echo '$GITHUB_TAG environment variable is missing' && exit 1; fi
if [ -z "${GITHUB_TAG}" ]; then echo '$GITHUB_TAG environment variable is empty' && exit 1; fi
if [ -z ${GITHUB_SHA+x} ]; then echo '$GITHUB_SHA environment variable is missing' && exit 1; fi
if [ -z "${GITHUB_SHA}" ]; then echo '$GITHUB_SHA environment variable is empty' && exit 1; fi
if [ -z ${GITHUB_TOKEN+x} ]; then echo '$GITHUB_TOKEN environment variable is missing' && exit 1; fi
if [ -z "${GITHUB_TOKEN}" ]; then echo '$GITHUB_TOKEN environment variable is empty' && exit 1; fi
if [ -z ${DEPLOY_WEBHOOK_URL+x} ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is missing' && exit 1; fi
if [ -z "${DEPLOY_WEBHOOK_URL}" ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is empty' && exit 1; fi
if [ -z ${TWINE_USERNAME+x} ]; then echo '$TWINE_USERNAME environment variable is missing' && exit 1; fi
if [ -z "${TWINE_USERNAME}" ]; then echo '$TWINE_USERNAME environment variable is empty' && exit 1; fi
if [ -z ${TWINE_PASSWORD+x} ]; then echo '$TWINE_PASSWORD environment variable is missing' && exit 1; fi
if [ -z "${TWINE_PASSWORD}" ]; then echo '$TWINE_PASSWORD environment variable is empty' && exit 1; fi

VERSION=${GITHUB_TAG}
REF=${GITHUB_SHA}

echo "===== INSTALLING DEPENDENCIES ====="
python -m pip install \
    setuptools \
    wheel \
    nox \
    twine \
    requests \
    -r requirements.txt

echo "-- Bumping repository version to ${VERSION} (ref: ${REF}) --"
sed "s|^__version__.*|__version__ = \"${VERSION}\"|g" -i hikari/_about.py
sed "s|^__git_sha1__.*|__git_sha1__ = \"${REF}\"|g" -i hikari/_about.py
echo "=========================================================================="
cat hikari/_about.py
echo "=========================================================================="

echo "===== GENERATING STUB FILES ====="
nox -s generate-stubs

echo "===== DEPLOYING TO PYPI ====="
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

echo "===== SENDING WEBHOOK ====="
python scripts/deploy_webhook.py

echo "===== DEPLOYING PAGES ====="
source scripts/deploy-pages.sh
