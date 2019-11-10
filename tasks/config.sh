#!/usr/bin/env bash

echo "===============CONFIGURATION==============="

function do_export() {
    echo "exported $*"
    export "$*"
}

do_export CURRENT_VERSION_FILE="pyproject.toml"
do_export CURRENT_VERSION_PATTERN="^version\s*=\s*\"\K[^\"]*"

do_export API_NAME="hikari"
do_export GIT_SVC_HOST="gitlab.com"
do_export REPO_AUTHOR="nekokatt"
do_export ORIGINAL_REPO_URL="https://${GIT_SVC_HOST}/${REPO_AUTHOR}/${API_NAME}"
do_export REPOSITORY_URL=$(echo "$CI_REPOSITORY_URL" | perl -pe 's#.*@(.+?(\:\d+)?)/#git@\1:#')

do_export SSH_PRIVATE_KEY_PATH="~/.ssh/id_rsa"
do_export GIT_TEST_SSH_PATH="git@${GIT_SVC_HOST}"

do_export CI_ROBOT_NAME="${API_NAME} CI"
do_export CI_ROBOT_EMAIL="$(echo ${API_NAME} | sed 's/ /-/g')-ci@${GIT_SVC_HOST}"

do_export SKIP_CI_COMMIT_PHRASE='[skip ci]'

do_export PROD_BRANCH="master"
do_export PREPROD_BRANCH="staging"
do_export REMOTE_NAME="origin"

do_export COMMIT_REF="${CI_COMMIT_REF_NAME}"

do_export POETRY_REPOSITORY_PROPERTY_NAME="chosen_repo"

cat > /dev/null << EOF
  SECURE VARIABLES TO DEFINE IN CI
  ================================

  PyPi credentials:
    PYPI_USER
    PYPI_PASS

  SSH:
    GIT_SSH_PRIVATE_KEY

  Webhooks:
    RELEASE_WEBHOOK (url of webhook to fire requests at to make a deployment message on Discord)
    RELEASE_WEBHOOK_NAME (title of embed)
    RELEASE_WEBHOOK_DESCRIPTION (description of embed)
    RELEASE_WEBHOOK_COLOUR (integer colour code)

  GitLab API:
    GITLAB_RELEASE_TOKEN (user API token used to create a new release with over https)
    CI_PROJECT_ID (the project ID on GitLab, this is predefined by the CI environment)

  VARIABLES TO DEFINE IN CI PER ENVIRONMENT
  =========================================

  Any:
    ENVIRONMENT - the name of the environment being used (GitLab sets this for us)

  Production environment:
    PYPI_REPO

  Preproduction environment:
    PYPI_REPO
EOF

echo "=============END CONFIGURATION============="
