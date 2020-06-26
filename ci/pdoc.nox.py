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
from ci import config
from ci import nox


@nox.session(reuse_venv=True, default=True)
@nox.inherit_environment_vars
def pdoc(session: nox.Session) -> None:
    """Generate documentation with pdoc."""
    session.install("-r", "requirements.txt")
    session.install("git+https://github.com/pdoc3/pdoc@83a8c400bcf9109d4753c46ad2f71a4e57114871")
    session.install("sphobjinv")

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
