#!/bin/sh -e
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

# Script to set the PYTHONPATH variable up to point to the root of this repository.

if [ -z "${1}" ]; then
    echo "Please pass a bot token as the first parameter to this script!"
    exit 1
fi

SCRIPT=$(readlink -f "${0}")
SCRIPT_PATH=$(dirname "${SCRIPT}")

# PYTHONPATH might not be set
if [ $PYTHONPATH ]; then
    PYTHONPATH="${PYTHONPATH}:${SCRIPT_PATH}/../.."
else
    PYTHONPATH="${SCRIPT_PATH}/../.."
fi

export PYTHONPATH
export BOT_TOKEN="${1}"

python3 "${SCRIPT_PATH}/$(basename "${SCRIPT_PATH}").py"
