#!/usr/bin/env bash

# This script attempts to detect when PyPI resets our connection and aborts the operation by repeating the operation
# up to 10 times if it occurs. It works by reading the stdout and stderr of the passed command and dumping the exit
# code to a temporary file each time. If the output contains 'connection reset by peer', an internal flag gets set
# that will make the script sleep for a couple of seconds and retry again. Otherwise, the exit code that was saved
# is used as the script exit code.
for i in $(seq 1 10); do
    echo -en "\e[1;31m#$i \e[0m"
    continue=1
    exec 3< <($* 2>&1; echo $? > /tmp/exit_code)
    while read -u 3 line; do
        echo ${line}
        if echo ${line} | grep -iq "Connection reset by peer"; then
            echo "Connection reset by peer, retrying." >&1
            continue=0
        fi
    done
    exit_code=$(cat /tmp/exit_code | xargs)
    if [[ ! ${continue} -eq 0 ]]; then
        exit ${exit_code}
    else
        sleep 2
    fi
done
code=$(cat /tmp/exit_code | xargs)
rm /tmp/exit_code
exit ${code}
