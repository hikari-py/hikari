#!/bin/sh
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.

set -e

TRUE=0
FALSE=1

dockerfiles=(
    cpy374
    cpy380
    cpy39rc
)

run_cmd() {
    printf "\e[0;34m> \e[0;35m%s\e[0m\n" "$*"
    exec $@
}

prefix() {
    while read l ; do printf "$2%20s\e[0m %s\n" "$1" "$l" ; done
}

destroy() {
    (echo "Destroying $1 if it exists." && 2>&1 docker image rm -f $1 || true) \
        | prefix "$1 (rm)" "\e[1;31m"
}

build() {
    docker image build --no-cache --force-rm -t $1 -f $1.dockerfile .. 2>&1 \
        | tee -a $1-build.container.log \
        | prefix "$1 (build)" "\e[1;33m" &
}

run() {
    echo "                    =============================================================="
    echo "                    $1 run"
    echo "                    ······························································"
    df=$1
    shift 1
    docker run --rm $df $@ 2>&1 \
        | tee -a $df-run.container.log \
        | prefix "$df" "\e[1;33m"
}

trap "kill $(jobs -p) 2>/dev/null" SIGINT SIGTERM SIGKILL
do_clean=$FALSE
do_rebuild=$FALSE
do_help=$FALSE

while [ $# != 0 ]; do
    if [ "--help" = $1 ]; then
        shift 1
        do_help=$TRUE
    elif [ "--clean" = $1 ]; then
        shift 1
        do_clean=$TRUE
    elif [ "--rebuild" = $1 ]; then
        shift 1
        do_rebuild=$TRUE
    else
        break
    fi
done

if [ ${do_help} -eq $TRUE ]; then
    echo "USAGE: $0 [--help] [--clean] [--rebuild] <arg1> <arg2> .. <argN>"
    echo
    echo "Run Hikari's pipelines within Docker containers for specific versions of Python."
    echo "Logs also get written out to *.container.log to be used for debugging purposes later."
    echo
    echo "Options:"
    echo "    --clean     remove any log files from previous runs."
    echo "    --help      display this message."
    echo "    --rebuild   rebuild all images automatically."
    echo "    <argX>      an argument to pass to 'nox' in each environment."
    exit 0
fi

if [ ${do_clean} -eq $TRUE ]; then
    rm *.container.log -vf
fi

echo "                    Docker is located at: $(which docker)"

if [ ${do_rebuild} -eq $TRUE ]; then
    for dockerfile in ${dockerfiles[@]}; do
        destroy ${dockerfile}
    done
fi

for dockerfile in ${dockerfiles[@]}; do
    if ! docker image ls | grep -q ${dockerfile}; then
        build ${dockerfile}
    fi
done

wait $(jobs -p)

for dockerfile in ${dockerfiles[@]}; do
    run ${dockerfile} ${@}
done
