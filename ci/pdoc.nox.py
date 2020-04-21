#!/usr/bin/env python3
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


@nox.session(reuse_venv=True, default=True)
def pdoc(session: nox.Session) -> None:
    """Generate documentation with pdoc."""

    # Inherit environment GitLab CI vars, where appropriate.
    for n, v in os.environ.items():
        if n.startswith(("GITLAB_", "CI")) or n == "CI":
            session.env[n] = v

    #: Copy over the root index html file if it's set.
    if config.ROOT_INDEX_SOURCE:
        if not os.path.exists(config.ARTIFACT_DIRECTORY):
            os.mkdir(config.ARTIFACT_DIRECTORY)
        shutil.copy(
            os.path.join(config.DOCUMENTATION_DIRECTORY, config.ROOT_INDEX_SOURCE),
            os.path.join(config.ARTIFACT_DIRECTORY, "index.html")
        )

    session.install("-r", config.REQUIREMENTS, "pdoc3==0.8.1")

    session.run(
        "python",
        "-m",
        "pdoc",
        config.MAIN_PACKAGE,
        "--html",
        "--output-dir",
        config.ARTIFACT_DIRECTORY,
        "--template-dir",
        config.DOCUMENTATION_DIRECTORY,
        "--force",
    )
