#!/usr/bin/env sh
set -e
set -x
version=$1
sed "s|^__version__.*|__version__ = \"${version}\"|g" -i "hikari/_about.py"
git add "hikari/_about.py"