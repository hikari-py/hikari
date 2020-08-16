#!/bin/sh
VERSION=${TRAVIS_TAG}
REF=${TRAVIS_COMMIT}

if [ -z ${GITHUB_TOKEN+x} ]; then echo '$GITHUB_TOKEN environment variable is missing' && exit 1; fi
if [ -z "${GITHUB_TOKEN}" ]; then echo '$GITHUB_TOKEN environment variable is empty' && exit 1; fi
if [ -z ${DEPLOY_WEBHOOK_URL+x} ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is missing' && exit 1; fi
if [ -z "${DEPLOY_WEBHOOK_URL}" ]; then echo '$DEPLOY_WEBHOOK_URL environment variable is empty' && exit 1; fi
if [ -z ${TWINE_USERNAME+x} ]; then echo '$TWINE_USERNAME environment variable is missing' && exit 1; fi
if [ -z "${TWINE_USERNAME}" ]; then echo '$TWINE_USERNAME environment variable is empty' && exit 1; fi
if [ -z ${TWINE_PASSWORD+x} ]; then echo '$TWINE_PASSWORD environment variable is missing' && exit 1; fi
if [ -z "${TWINE_PASSWORD}" ]; then echo '$TWINE_PASSWORD environment variable is empty' && exit 1; fi

echo "-- Bumping repository version to ${VERSION} (ref: ${REF}) --"
sed "s|^__version__.*|__version__ = \"${VERSION}\"|g" -i hikari/_about.py
sed "s|^__git_sha1__.*|__git_sha1__ = \"${REF}\"|g" -i hikari/_about.py
echo "=========================================================================="
cat hikari/_about.py
echo "=========================================================================="

echo "===== DEPLOYING TO PYPI ====="
python -m pip install -U twine setuptools wheel -r requirements.txt
python setup.py sdist bdist_wheel
echo "-- Contents of . --"
ls -ahl
echo
echo "-- Contents of ./dist --"
ls -ahl dist

echoo "-- Checking generated dists --"
python -m twine check dist/*
env | sort
python -m twine upload --disable-progress-bar --skip-existing dist/* --non-interactive --repository-url https://upload.pypi.org/legacy/

echo "===== SENDING WEBHOOK ====="
python -m pip install requests
python scripts/deploy_webhook.py

echo "===== DEPLOYING PAGES ====="
git config user.name "Nekokatt"
git config user.email "69713762+nekokatt@users.noreply.github.com"

python -m pip install nox
mkdir public || true
nox --sessions pdoc pages
cd public || exit 1
git init
git remote add origin https://nekokatt:${GITHUB_TOKEN}@github.com/${TRAVIS_REPO_SLUG}
git checkout -B gh-pages
git add -Av .
git commit -am "Deployed documentation [skip ci]"
git push origin gh-pages --force
