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
import os
import shutil

from ci import config
from ci import nox


@nox.session(reuse_venv=True)
@nox.inherit_environment_vars
def build_ext(session: nox.Session) -> None:
    """Compile C++ extensions in-place."""
    session.run("python", "setup.py", "build_ext", "--inplace")


@nox.session(reuse_venv=True)
@nox.inherit_environment_vars
def clean_ext(session: nox.Session) -> None:
    """Clean any compiled C++ extensions."""
    print("rm", "build", "-r")
    shutil.rmtree("build", ignore_errors=True)
    print("rm", "dist", "-r")
    shutil.rmtree("dist", ignore_errors=True)
    for parent, _, files in os.walk(config.MAIN_PACKAGE):
        for file in files:
            if file.endswith((".so", ".pyd", ".lib", ".dll", ".PYD", ".DLL")):
                path = os.path.join(parent, file)
                print("rm", path)
                os.remove(path)
