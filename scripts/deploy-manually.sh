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
posix_read() {
    prompt="${1}"
    var_name="${2}"
    printf "%s: " "${prompt}"
    read -r "${var_name?}"
    export "${var_name?}"
    return ${?}
}

posix_read "Twine username" TWINE_USERNAME
posix_read "Twine password" TWINE_PASSWORD
posix_read "GitHub deploy token" GITHUB_TOKEN
posix_read "Discord deployment webhook URL" DEPLOY_WEBHOOK_URL
posix_read "Tag" VERSION
posix_read "Repo slug (e.g. hikari-py/hikari)" GITHUB_REPO_SLUG

git checkout "${GITHUB_TAG}"
export REF=$(git rev-parse HEAD)
echo "Detected REF to be ${REF}"

set -x
rm public -Rf || true
bash scripts/deploy.sh
