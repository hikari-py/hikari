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
"""Clang-tidy."""
import subprocess

from ci import config
from ci import nox


def _clang_tidy(*args):
    invocation = f"clang-tidy $(find {config.MAIN_PACKAGE} -name '*.c' -o -name '*.h') "
    invocation += " ".join(args)
    print(subprocess.check_output(invocation, shell=True))


@nox.session(reuse_venv=True)
def clang_tidy_check(session: nox.Session) -> None:
    _clang_tidy()


@nox.session(reuse_venv=True)
def clang_tidy_fix(session: nox.Session) -> None:
    _clang_tidy("--fix")
