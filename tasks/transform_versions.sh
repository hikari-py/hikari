#!/usr/bin/env bash
set -e
set -x

version=$1

declare -A VERSION_TRANSFORMATIONS=(
    ["hikari/__init__.py"]="s|^__version__.*|__version__ = \"${version}\"|g"
    ["setup.py"]="s|^__version__.*|__version__ = \"${version}\"|g"
    ["docs/conf.py"]="0,/^version.*$/s||version = \"${version}\"|g"
)

for transformation in "${!VERSION_TRANSFORMATIONS[@]}"; do
    sed "${VERSION_TRANSFORMATIONS[${transformation}]}" -i "${transformation}"
done

git add ${!VERSION_TRANSFORMATIONS[@]}
