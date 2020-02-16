#!/usr/bin/env bash

# Load configuration.
# source "$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"/config.sh

function deploy-to-pypi() {
    python setup.py sdist bdist_wheel
    set +x
    twine upload --username="${PYPI_USER}" --password="${PYPI_PASS}" --repository-url=https://upload.pypi.org/legacy/ dist/*
    set -x
}

function notify() {
    local version=${1}
    python tasks/notify.py "${version}" "${API_NAME}" "${PYPI_REPO}"
}

function deploy-to-svc() {
    local repo
    local old_version=${1}
    local current_version=${2}

    # Init SSH auth.
    set +x
    eval "$(ssh-agent -s)"
    mkdir ~/.ssh || true
    echo "${GIT_SSH_PRIVATE_KEY}" > ~/.ssh/id_rsa
    set -x
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -t rsa ${GIT_SVC_HOST} >> ~/.ssh/known_hosts
    ssh-add ~/.ssh/id_rsa
    # Verify the key works.
    ssh "${GIT_TEST_SSH_PATH}"
    git commit -am "(ci) Deployed ${current_version} to PyPI [skip deploy]" --allow-empty
    git push ${REMOTE_NAME} ${PROD_BRANCH}
    git tag "${current_version}" && git push ${REMOTE_NAME} "${current_version}"
    # git -c color.status=always log --all --decorate --oneline --graph -n 50
    git fetch --all
    git reset --hard origin/${PROD_BRANCH}
    git checkout ${PREPROD_BRANCH}
    git reset --hard origin/${PREPROD_BRANCH}
    # git -c color.status=always log --all --decorate --oneline --graph -n 50
    # Use [skip deploy] instead of [skip ci] so that our pages rebuild still...
    git merge origin/${PROD_BRANCH} --no-ff --strategy-option theirs --allow-unrelated-histories -m "(ci) Merged ${PROD_BRANCH} ${current_version} into ${PREPROD_BRANCH}"
    bash tasks/transform_versions.sh $(python tasks/make_version_string.py ${PREPROD_BRANCH})
    git commit -am "(ci) Updated version for next development release [skip deploy]"
    git push --atomic ${REMOTE_NAME} ${PREPROD_BRANCH} ${PROD_BRANCH} ${curr}
}

function do-deployment() {
    set -x
    
    local old_version
    local current_version
    git remote set-url ${REMOTE_NAME} "${REPOSITORY_URL}"
    git config user.name "${CI_ROBOT_NAME}"
    git config user.email "${CI_ROBOT_EMAIL}"

    git fetch --all
    git checkout -f "${COMMIT_REF}"

    old_version=$(grep -oP "${CURRENT_VERSION_PATTERN}" "${CURRENT_VERSION_FILE}")
    current_version=$(python tasks/make_version_string.py "${COMMIT_REF}")
    
    bash tasks/transform_versions.sh "${current_version}"
    pip install -e .

    case "${COMMIT_REF}" in
        ${PROD_BRANCH})
            # Ensure we have the staging ref as well as the master one
            git checkout "${PREPROD_BRANCH}" -f && git checkout "${PROD_BRANCH}" -f
            bash tasks/transform_versions.sh "${current_version}"
            # Push to GitLab and update both master and staging.
            time deploy-to-pypi
            time deploy-to-svc "${old_version}" "${current_version}"
            ;;
        ${PREPROD_BRANCH})
            time deploy-to-pypi
            ;;
        *)
            echo -e "\e[1;31m${COMMIT_REF} is not ${PROD_BRANCH} or ${PREPROD_BRANCH}, so will not be updated.\e[0m"
            exit 1
            ;;
    esac

    notify "${current_version}"
    set +x
}
