#!/usr/bin/env bash

# This script attempts to detect when PyPI resets our connection and aborts the operation by repeating the operation
# up to 10 times if it occurs. It works by reading the stdout and stderr of the passed command and dumping the exit
# code to a temporary file each time. If the output contains 'connection reset by peer', an internal flag gets set
# that will make the script sleep for a couple of seconds and retry again. Otherwise, the exit code that was saved
# is used as the script exit code.
retries=10
for i in $(seq 1 ${retries}); do
    echo -e "\e[1;31mAttempt #$i/$retries of \e[0;33m$*\e[0m"
    continue=1
    # shellcheck disable=SC2068
    exec 3< <($@ 2>&1; echo $? > /tmp/exit_code)
    while read -ru 3 line; do
        echo "${line}"
        if echo "${line}" | grep -iq "Connection reset by peer"; then
            echo -e "\e[1;31mConnection reset by peer, retrying.\e[0m" >&1
            continue=0
        fi
    done
    exit_code=$(xargs < /tmp/exit_code)
    if [[ ! ${continue} -eq 0 ]]; then
        exit "${exit_code}"
    else
        sleep 2
    fi
done
code=$(xargs < /tmp/exit_code)
rm /tmp/exit_code
exit "${code}"
