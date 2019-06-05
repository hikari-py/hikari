#!/usr/bin/env sh
# -*- coding: utf-8 -*-
set -x

MAX_LENGTH=300

mkdir public || true

echo "<link rel=\"stylesheet\" href=\"_static/bootstrap-sphinx.css\"/><ol>" > public/CHANGELOG.html
git log  --pretty=format:'<li> %s &bull; %an &bull; %ar &bull; <a href="http://gitlab.com/nekokatt/hikari/commit/%H">%h</a></li> ' | head -n ${MAX_LENGTH} >> public/CHANGELOG.html
echo "</ol>" >> public/CHANGELOG.html