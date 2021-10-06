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

if [ -z ${VERSION+x} ]; then echo '$VERSION environment variable is missing' && exit 1; fi
if [ -z "${VERSION}" ]; then echo '$VERSION environment variable is empty' && exit 1; fi
if [ -z ${GITHUB_TOKEN+x} ]; then echo '$GITHUB_TOKEN environment variable is missing' && exit 1; fi
if [ -z "${GITHUB_TOKEN}" ]; then echo '$GITHUB_TOKEN environment variable is empty' && exit 1; fi

echo "===== INSTALLING DEPENDENCIES ====="
pip install towncrier
pip install -e .

echo "===== UPDATING INFORMATION ====="
echo "-- Checkout branch --"
git checkout -b "task/prepare-release-${VERSION}"

echo "-- Bumping repository version to ${VERSION} --"
sed "s|^__version__.*|__version__ = \"${VERSION}\"|g" -i hikari/_about.py

echo "-- Running towncrier --"
towncrier --yes

echo "-- Committing changes --"
git commit -am "Prepare for release of version ${VERSION} [skip-ci]"

if [ "${CI}" ]; then
    git push origin "task/prepare-release-${VERSION}"
else
    echo "Changes committed to 'task/prepare-release-${VERSION}'. You can now push the changes and create a pull request"
fi
