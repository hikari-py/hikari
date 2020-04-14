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
"""Sphinx documentation generation."""
import os
import re

from ci import config
from ci import nox


@nox.session(reuse_venv=False, default=True)
def sphinx(session: nox.Session) -> None:
    """Generate Sphinx documentation."""
    session.install(
        "-r", config.REQUIREMENTS,
        "sphinx==3.0.1",
        "https://github.com/ryan-roemer/sphinx-bootstrap-theme/zipball/v0.8.0"
    )

    session.env["SPHINXOPTS"] = "-WTvvn"

    print("Generating stubs")
    session.run("sphinx-apidoc", "-e", "-o", config.DOCUMENTATION_DIRECTORY, config.MAIN_PACKAGE)

    print("Producing HTML documentation from stubs")
    session.run(
        "python", "-m", "sphinx.cmd.build",
        "-a", "-b", "html", "-j", "auto", "-n",
        config.DOCUMENTATION_DIRECTORY, config.ARTIFACT_DIRECTORY
    )

    if "--no-rm" in session.posargs:
        print("Not removing stub files by request")
    else:
        print("Destroying stub files (skip by passing `-- --no-rm` flag)")
        blacklist = (f"{config.MAIN_PACKAGE}.rst", "modules.rst")
        for f in os.listdir(config.DOCUMENTATION_DIRECTORY):
            if f in blacklist or re.match(f"{config.MAIN_PACKAGE}\\.(\\w|\\.)+\\.rst", f):
                path = os.path.join(config.DOCUMENTATION_DIRECTORY, f)
                print("rm", path)
                os.unlink(path)
