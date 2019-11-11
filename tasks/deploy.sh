#!/usr/bin/env bash

# Load configuration.
# source "$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"/config.sh

function set-versions() {
    set -x
    bash tasks/transform-versions.sh $1
    set +x
}

function deploy-to-pypi() {
    poetry build
    poetry publish --username="${PYPI_USER}" --password="${PYPI_PASS}" --repository=${POETRY_REPOSITORY_PROPERTY_NAME}
}

function deploy-to-release-api() {
    set -x
    pip install gcg # Git Changelog Generator
    python tasks/release.py "${API_NAME}" "${1}"
    set +x
}

function notify() {
    set -x
    local version=${1}
    python tasks/notify.py "${version}" "${API_NAME}" "${PYPI_REPO}"
    set +x
}

function deploy-to-svc() {
    set -x
    local repo
    local old_version=${1}
    local current_version=${2}

    # Init SSH auth.
    eval "$(ssh-agent -s)"
    mkdir ~/.ssh || true
    set +x
    echo "${GIT_SSH_PRIVATE_KEY}" > ~/.ssh/id_rsa
    set -x
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -t rsa ${GIT_SVC_HOST} >> ~/.ssh/known_hosts
    ssh-add ~/.ssh/id_rsa
    # Verify the key works.
    ssh ${GIT_TEST_SSH_PATH}
    git remote set-url ${REMOTE_NAME} "${REPOSITORY_URL}"
    git config user.name "${CI_ROBOT_NAME}"
    git config user.email "${CI_ROBOT_EMAIL}"
    git status
    git diff
    git commit -am "Deployed ${current_version} ${SKIP_CI_COMMIT_PHRASE}" --allow-empty
    git push ${REMOTE_NAME} ${PROD_BRANCH} || true
    (git tag "${current_version}" && git push ${REMOTE_NAME} "${current_version}") || true
    git checkout ${PREPROD_BRANCH}
    (git merge ${PROD_BRANCH} --no-ff --strategy-option theirs -m "Merged ${PROD_BRANCH} ${current_version} into ${PREPROD_BRANCH} ${SKIP_CI COMMIT_PHRASE}" && git push ${REMOTE_NAME} ${PREPROD_BRANCH}) || true
    set +x
}

function do-deployment() {
    set -x
    local old_version
    local current_version

    git fetch -ap
    git checkout -f "${COMMIT_REF}"

    old_version=$(grep -oP "${CURRENT_VERSION_PATTERN}" "${CURRENT_VERSION_FILE}")
    current_version=$(python tasks/make-version-string.py "${COMMIT_REF}")

    poetry config repositories.${POETRY_REPOSITORY_PROPERTY_NAME} "${PYPI_REPO}"

    case "${COMMIT_REF}" in
        ${PROD_BRANCH})
            # Ensure we have the staging ref as well as the master one
            git checkout "${PREPROD_BRANCH}" -f && git checkout "${PROD_BRANCH}" -f
            set-versions "${current_version}"
            # Push to GitLab and update both master and staging.
            deploy-to-pypi
            deploy-to-svc "${old_version}" "${current_version}"
            deploy-to-release-api "${current_version}" || true
            ;;
        ${PREPROD_BRANCH})
            set-versions "${current_version}"
            deploy-to-pypi
            ;;
        *)
            echo -e "\e[1;31m${COMMIT_REF} is not ${PROD_BRANCH} or ${PREPROD_BRANCH}, so will not be updated.\e[0m"
            exit 1
            ;;
    esac

    notify "${current_version}"
    set +x
}
