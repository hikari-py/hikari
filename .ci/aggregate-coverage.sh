#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Attempts to aggregate any existing coverage reports into a single coverage report, as well as producing several other
# useful report formats for the PAGES pipeline output artifacts
#
set -x

DIR=public
TARGET_DIR=$DIR
DEBUG=no

python -m coverage combine $(find $DIR -type f -iname "coverage-py36" -o -iname "coverage-py37")
python -m coverage report
python -m coverage xml -o public/coverage.xml
python -m coverage html -d public/coverage

if [ "$DEBUG" = "no" ]; then
    rm .coverage public/*.dat || true
fi

CURRENT_BRANCH="$(git symbolic-ref --short HEAD || git symbolic-ref --short master)"
if [ "$CURRENT_BRANCH" = "master" ]; then
    PREVIOUS_BRANCH=$(git rev-list origin | head -n 2 | tail -n 1)
else
    PREVIOUS_BRANCH="master"
fi

diff-cover --compare-branch origin/$PREVIOUS_BRANCH $DIR/coverage.xml --html-report=$TARGET_DIR/.diff-cover.html || true

echo "<link rel=\"stylesheet\" href=\"_static/bootstrap-sphinx.css\"/><ol>" > public/diff-cover.html
cat public/.diff-cover.html >> public/diff-cover.html
rm public/.diff-cover.html
rm $TARGET_DIR/html -Rf