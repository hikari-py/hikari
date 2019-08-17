#!/usr/bin/env bash

function set-versions() {
  local version=$1
  sed "s/^__version__.*/__version__ = \"${version}\"/g" -i hikari/__init__.py
  sed "0,/^version.*$/s//version = \"${version}\"/g" -i pyproject.toml
  sed "0,/^version.*$/s//version = \"${version}\"/g" -i docs/conf.py
}

function deploy-to-pypi() {
  poetry build
  poetry publish --username="$PYPI_USER" --password="$PYPI_PASS" --repository=hikarirepo
}

function notify() {
  local version=$1
  python tasks/notify.py "${version}" "hikari.core"
}

function deploy-to-gitlab() {
  local repo
  local old_version=$1
  local current_version=$2

  # Init SSH auth.
  eval "$(ssh-agent -s)"
  mkdir ~/.ssh || true
  set +x
  echo "$GIT_SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
  set -x
  chmod 600 ~/.ssh/id_rsa
  ssh-keyscan -t rsa gitlab.com >> ~/.ssh/known_hosts
  ssh-add ~/.ssh/id_rsa
  ssh git@gitlab.com  # Ensure it works
  repo=$(echo "$CI_REPOSITORY_URL" | perl -pe 's#.*@(.+?(\:\d+)?)/#git@\1:#')
  git remote set-url origin "$repo"

  git config user.name "Hikari CI"
  git config user.email "nekoka.tt@outlook.com"
  git add pyproject.toml docs/conf.py hikari/core/__init__.py
  git status
  git diff
  git commit -am "Deployed $current_version [skip ci]" --allow-empty
  git push origin master || true
  git tag "$current_version" && git push origin "$current_version" || true
  git checkout staging
  git merge master --no-ff -m "Merge deployed master $current_version into staging [skip ci]" && git push origin staging || true
}

function do-deployment() {
  set -x
  local old_version
  local current_version

  git fetch -ap
  git checkout -f "${CI_COMMIT_REF_NAME}"

  old_version=$(grep -oP "^version\s*=\s*\"\K[^\"]*" pyproject.toml)
  current_version=$(python tasks/make-version-string.py "$CI_COMMIT_REF_NAME")

  poetry config repositories.hikarirepo "$PYPI_REPO"

  case $CI_COMMIT_REF_NAME in
    master)
      # Ensure we have the staging ref as well as the master one
      git checkout staging -f && git checkout master -f
      set-versions "$current_version"
      # Push to GitLab and update both master and staging.
      deploy-to-pypi
      deploy-to-gitlab "$old_version" "$current_version"
      # Trigger Hikari deployment in main umbrella repo.
      echo "Triggering hikari package rebuild"
      curl --request POST --form token="$HIKARI_TRIGGER_TOKEN" --form ref=master https://gitlab.com/api/v4/projects/13535679/trigger/pipeline | python -m json.tool
      ;;
    staging)
      set-versions "$current_version"
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
