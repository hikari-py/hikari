#!/usr/bin/env bash
set -e
set -x

version=$1
file=hikari/_about.py

sed "s|^__version__.*|__version__ = \"${version}\"|g" -i ${file}

git add ${file}
