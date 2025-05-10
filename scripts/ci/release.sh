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

if [ "$(find changes/*.*.md 2>/dev/null | wc -l)" != "0" ]; then
  echo "Cannot create release if CHANGELOG fragment files exist under 'changes/'!" && exit 1
fi

echo "Defined environment variables"
env | grep -oP "^[^=]+" | sort

if [ -z ${VERSION+x} ]; then echo '$VERSION environment variable is missing' && exit 1; fi
if [ -z "${VERSION}" ]; then echo '$VERSION environment variable is empty' && exit 1; fi
if [ -z ${DEPLOY_WEBHOOK_URL+x} ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is missing' && exit 1; fi
if [ -z "${DEPLOY_WEBHOOK_URL}" ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is empty' && exit 1; fi
if [ -z ${UV_PUBLISH_USERNAME+x} ]; then echo '$UV_PUBLISH_USERNAME environment variable is missing' && exit 1; fi
if [ -z "${UV_PUBLISH_USERNAME}" ]; then echo '$UV_PUBLISH_USERNAME environment variable is empty' && exit 1; fi
if [ -z ${UV_PUBLISH_PASSWORD+x} ]; then echo '$UV_PUBLISH_PASSWORD environment variable is missing' && exit 1; fi
if [ -z "${UV_PUBLISH_PASSWORD}" ]; then echo '$UV_PUBLISH_PASSWORD environment variable is empty' && exit 1; fi

about_version=$(sed -nr 's/^__version__: typing\.Final\[str\] = "([^"]*)"/\1/p' hikari/_about.py)
if [ -z "${about_version}" ]; then
  echo "Variable '__version__' not found in about!" && exit 1
fi

if [ "${about_version}" != "${VERSION}" ]; then
  echo "Variable '__version__' does not match the version this release is for! [__version__='${about_version}'; VERSION='${VERSION}']" && exit 1
fi

ref="$(git rev-parse HEAD)"

echo "===== DEPLOYING TO PYPI ====="
echo "-- Setting __git_sha1__ (ref: ${ref}) --"
sed "/^__git_sha1__.*/, \${s||__git_sha1__: typing.Final[str] = \"${ref}\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__git_sha1__' not found in about!" && exit 1)
echo "=========================================================================="
cat hikari/_about.py
echo "=========================================================================="
uv sync
python -m hikari
echo "=========================================================================="

echo "-- Building package --"
uv build
echo "-- Contents of . --"
ls -ahl
echo
echo "-- Contents of ./dist --"
ls -ahl dist

echo "-- Uploading to PyPI --"
uv publish

echo "===== SENDING WEBHOOK ====="
curl \
  -X POST \
  -H "Content-Type: application/json" \
  "${DEPLOY_WEBHOOK_URL}" \
  -d '{
        "username": "Github Actions",
        "embeds": [
          {
            "title": "'"${VERSION} has been deployed to PyPI"'",
            "color": 6697881,
            "description": "'"Install it now by executing: \`\`\`pip install hikari==${VERSION}\`\`\`\\nDocumentation can be found at https://docs.hikari-py.dev/en/${VERSION}"'",
            "footer": {
              "text": "'"SHA: ${ref}"'"
            }
          }
        ]
    }'


echo "===== UPDATING VERSION IN REPOSITORY ====="
new_version="$(python scripts/ci/increase_version_number.py "${VERSION}")"

echo "-- Setting up git --"
git fetch origin
git checkout -f master

echo "-- Bumping to development version (${new_version}) --"
sed "/^__version__.*/, \${s||__version__: typing.Final[str] = \"${new_version}\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__version__' not found in about!" && exit 1)
sed "/^__docs__.*/, \${s||__docs__: typing.Final[str] = \"https://docs.hikari-py.dev/en/master\"|g; b}; \$q1" -i hikari/_about.py || (echo "Variable '__docs__' not found in about!" && exit 1)

echo "-- Pushing to repository --"
git commit -am "Bump to development version (${new_version})"
git push
