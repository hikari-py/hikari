# -*- coding: utf-8 -*-
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
"""Pdoc documentation generation."""
import os
import shutil

from ci import config
from ci import nox


def copy_from_in(src: str, dest: str) -> None:
    for parent, dirs, files in os.walk(src):
        sub_parent = os.path.relpath(parent, src)

        for file in files:
            sub_src = os.path.join(parent, file)
            sub_dest = os.path.normpath(os.path.join(dest, sub_parent, file))
            print(sub_src, "->", sub_dest)
            shutil.copy(sub_src, sub_dest)


@nox.session(reuse_venv=True, default=True)
def pages(session: nox.Session) -> None:
    """Generate static pages containing resources and tutorials."""
    for n, v in os.environ.items():
        if n.startswith(("GITLAB_", "CI")) or n == "CI":
            session.env[n] = v

    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)
    copy_from_in(config.PAGES_DIRECTORY, config.ARTIFACT_DIRECTORY)
