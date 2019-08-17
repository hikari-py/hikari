#!/usr/bin/env bash

function set-versions() {
  local version=$1
  set -x
  sed "s/^__version__.*/__version__ = \"${version}\"/g" -i hikari/__init__.py
  sed "0,/^version.*$/s//version = \"${version}\"/g" -i pyproject.toml
  sed "0,/^version.*$/s//version = \"${version}\"/g" -i docs/conf.py
  set +x
}

function deploy-to-pypi() {
  set -x
  poetry build
  poetry publish --username="$PYPI_USER" --password="$PYPI_PASS" --repository=hikarirepo
  set +x
}

function notify() {
  set -x
  local version=$1
  python tasks/notify.py "${version}" "hikari.core"
  set +x
}

function deploy-to-gitlab() {
  set -x
  set -e
  local repo
  local current_version=$1
  local next_version=$2

  # Init SSH auth.
  eval "$(ssh-agent -s)"
  mkdir ~/.ssh || true
  echo "$GIT_SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
  chmod 600 ~/.ssh/id_rsa
  ssh-keyscan -t rsa gitlab.com >> ~/.ssh/known_hosts
  ssh-add ~/.ssh/id_rsa
  ssh git@gitlab.com  # Ensure it works
  repo=$(echo "$CI_REPOSITORY_URL" | perl -pe 's#.*@(.+?(\:\d+)?)/#git@\1:#')
  git remote set-url origin "$repo"

  git config user.name "Hikari CI"
  git config user.email "nekoka.tt@outlook.com"
  git add pyproject.toml docs/conf.py hikari/core/__init__.py
  git commit -am "Deployed $current_version, will update to $next_version [skip ci]"
  git tag "$current_version"
  git push origin master
  git push origin "$current_version"
  git checkout staging
  git merge -X ours origin/master -m "Deployed $current_version, updating staging to match master on $next_version [skip ci]" || true
  git push origin staging || true
  set +e
  set +x
}

function do-deployment() {
  set -x
  local current_version
  local next_version

  git checkout -f "${CI_COMMIT_REF_NAME}"
  current_version=$(grep -oP "^version\s*=\s*\"\K[^\"]*" pyproject.toml)
  next_version=$(python tasks/make-version-string.py "$CI_COMMIT_REF_NAME")

  poetry config repositories.hikarirepo "$PYPI_REPO"

  set-versions "$current_version"

  case $CI_COMMIT_REF_NAME in
    master)
      # Ensure we have the staging ref as well as the master one
      git stash; git checkout staging -f; git checkout master -f; git stash pop

      # Push to GitLab and update both master and staging.
      deploy-to-gitlab "$current_version" "$next_version"
      deploy-to-pypi
      # Trigger Hikari deployment in main umbrella repo.
      echo "Triggering hikari package rebuild"
      curl --request POST --form token="$HIKARI_TRIGGER_TOKEN" --form ref=master https://gitlab.com/api/v4/projects/13535679/trigger/pipeline | python -m json.tool
      ;;
    staging)
      deploy-to-pypi
      ;;
    *)
      echo -e "\e[1;31m$CI_COMMIT_REF_NAME is not master or staging, so will not be updated.\e[0m"
      exit 1
      ;;
  esac

  notify "$current_version"
  set +x
}
