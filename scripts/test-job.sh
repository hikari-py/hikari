#!/bin/bash
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
set -e

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
