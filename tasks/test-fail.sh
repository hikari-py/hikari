#!/usr/bin/env bash
echo blah
sleep 0.5
echo blah
sleep 0.5
if [[ "$((1 + RANDOM % 4))" = "4" ]]; then
    echo "success"
    exit 2
else
    echo "connection reset by peer"
    exit 1
fi
