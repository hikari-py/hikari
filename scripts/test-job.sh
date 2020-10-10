#!/bin/bash
set -x

if [ -z "${PYTHON_COMMAND:+x}" ]; then
    export PYTHON_COMMAND=python
fi

mkdir public > /dev/null 2>&1 || true
${PYTHON_COMMAND} -V
${PYTHON_COMMAND} -m pip install nox
${PYTHON_COMMAND} -m nox --sessions pytest
RESULT_UNOPTIMISED=$?
${PYTHON_COMMAND} -m nox --sessions pytest-speedups -- --cov-append
RESULT_OPTIMISED=$?
RESULT=$((~$((RESULT_UNOPTIMISED & RESULT_OPTIMISED))))

if [ "$(uname -s | perl -ne 'print lc')-$(uname -m)" = "linux-x86_64" ]; then
    echo "Detected Linux AMD64, will upload coverage data"
    curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter
    chmod +x ./cc-test-reporter
    ./cc-test-reporter after-build \
        --exit-code ${RESULT} \
        --id       "bf39911ceca45a536d408ea6456ed67460c73754f1411fb45f5e957398d98348"
fi
