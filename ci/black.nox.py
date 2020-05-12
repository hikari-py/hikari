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
"""Black code-style jobs."""
from ci import nox


PATHS = [
    "hikari",
    "tests",
    "setup.py",
    "noxfile.py",
]


@nox.session(default=True, reuse_venv=True)
def reformat_code(session: nox.Session) -> None:
    """Run black code formatter."""
    session.install("black")
    session.run("black", *PATHS)


@nox.session(reuse_venv=True)
def check_formatting(session: nox.Session) -> None:
    """Check that the code matches the black code style."""
    session.install("black")
    session.run("black", *PATHS, "--check")
