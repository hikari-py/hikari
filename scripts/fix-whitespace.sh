#!/usr/bin/env bash
# Removes trailing whitespace in Python source files.

find hikari tests setup.py ci -type f -name '*.py' -exec sed -i "s/[ ]*$//g" {} \; -exec git add -v {} \;
