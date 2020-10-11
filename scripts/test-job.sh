#!/bin/bash
set -x

if [ -z "${PYTHON_COMMAND:+x}" ]; then
    export PYTHON_COMMAND=python
fi

mkdir public > /dev/null 2>&1 || true
${PYTHON_COMMAND} -V
${PYTHON_COMMAND} -m pip install nox
${PYTHON_COMMAND} -m nox --sessions pytest
${PYTHON_COMMAND} -m nox --sessions pytest-speedups -- --cov-append

if [ "$(uname -s | perl -ne 'print lc')-$(uname -m)" = "linux-x86_64" ]; then
    echo "Detected Linux AMD64, will upload coverage data"
    curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter
    chmod +x ./cc-test-reporter
    ./cc-test-reporter after-build \
        --exit-code 0 \
        --id       "d40e64ea0ff74713f79365fea4378ab51a2141ad4fcf0fb118496bbf560d4192"
fi
