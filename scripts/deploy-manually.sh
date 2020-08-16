#!/bin/sh
posix_read() {
    prompt="${1}"
    var_name="${2}"
    printf "%s: " "${prompt}"
    read -r "${var_name?}"
    return ${?}
}

posix_read "Twine username" TWINE_USERNAME
posix_read "Twine password" TWINE_PASSWORD
posix_read "GitHub deploy token" GITHUB_TOKEN
posix_read "Discord deployment webhook URL" DEPLOY_WEBHOOK_URL
posix_read "Tag" TRAVIS_TAG
posix_read "Repo slug (e.g. nekokatt/hikari)" TRAVIS_REPO_SLUG

set -e
git checkout "${TRAVIS_TAG}"
TRAVIS_COMMIT=$(git show-ref -s HEAD)
echo "Detected TRAVIS_COMMIT to be ${TRAVIS_COMMIT}"
. scripts/deploy.sh
