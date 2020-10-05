#!/bin/sh
set -e

VERSION=${TRAVIS_TAG}
REF=${TRAVIS_COMMIT}

echo "===== INSTALLING DEPENDENCIES ====="
python -m pip install \
    setuptools \
    wheel \
    nox \
    twine \
    requests \
    -r requirements.txt

echo "Defined environment variables"
env | grep -oP "^[^=]+" | sort

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

echo "===== GENERATING STUB FILES ====="
nox -s generate-stubs

echo "===== DEPLOYING TO PYPI ====="
python setup.py sdist bdist_wheel
echo "-- Contents of . --"
ls -ahl
echo
echo "-- Contents of ./dist --"
ls -ahl dist

echo "-- Checking generated dists --"
python -m twine check dist/*
echo
echo "-- Uploading to PyPI --"
python -m twine upload --disable-progress-bar --skip-existing dist/* --non-interactive --repository-url https://upload.pypi.org/legacy/

echo "===== SENDING WEBHOOK ====="
python scripts/deploy_webhook.py

echo "===== DEPLOYING PAGES ====="
source scripts/deploy-pages.sh
