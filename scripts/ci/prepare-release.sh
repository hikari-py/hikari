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

echo "Defined environment variables"
env | grep -oP "^[^=]+" | sort

if [ -z ${IS_PRERELEASE+x} ]; then echo 'IS_PRERELEASE environment variable is missing' && exit 1; fi
if [ -z "${IS_PRERELEASE}" ]; then echo 'IS_PRERELEASE environment variable is empty' && exit 1; fi

echo "===== INSTALLING DEPENDENCIES ====="
pip install -r dev-requirements/towncrier.txt

echo "===== GENERATING RELEASE VERSION ====="
version=$(python scripts/ci/generate_release_version.py "${IS_PRERELEASE}")

echo "===== UPDATING INFORMATION ====="
echo "-- Checkout branch --"
git checkout -b "task/prepare-release-${version}"

echo "-- Bumping repository version to ${version} --"
sed "/^__version__.*/, \${s||__version__: typing.Final[str] = \"${version}\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__version__' not found in about!" && exit 1)
sed "/^__docs__.*/, \${s||__docs__: typing.Final[str] = \"https://docs.hikari-py.dev/en/${version}\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__docs__' not found in about!" && exit 1)

echo "-- Running towncrier --"
# Towncrier requires the package to be installed to get the appropriate release version
pip install -e .
towncrier --yes

echo "-- Committing changes --"
git commit -am "Prepare for release of version ${version}"

if [ "${CI}" ]; then
    git push origin "task/prepare-release-${version}"
else
    echo "Changes committed to 'task/prepare-release-${version}'. You can now push the changes and create a pull request"
fi
