#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Attempts to aggregate any existing coverage reports into a single coverage report, as well as producing several other
# useful report formats for the PAGES pipeline output artifacts
#
set -x

DIR=public
PATTERN='coverage-*'
TARGET_DIR=$DIR
python -m coverage combine $(find $DIR -type f -iname $PATTERN)
python -m coverage xml -o public/coverage.xml
python -m coverage html -d public/coverage
rm .coverage public/*.dat || true
diff-cover --compare-branch origin/master $DIR/coverage.xml --html-report=$TARGET_DIR/.diff-cover.html
echo "<link rel=\"stylesheet\" href=\"_static/bootstrap-sphinx.css\"/><ol>" > public/diff-cover.html
cat public/.diff-cover.html >> public/diff-cover.html
rm public/.diff-cover.html
rm $TARGET_DIR/html -Rf