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

from ci import config
from ci import nox


@nox.session(reuse_venv=True, default=True)
def flake8(session: nox.Session) -> None:
    session.install("-r", "requirements.txt", "-r", "flake-requirements.txt")

    if "GITLAB_CI" in os.environ or "--gitlab" in session.posargs:
        print("Detected GitLab, will output CodeClimate report instead!")
        format_args = ["--format=gl-codeclimate", f"--output-file={config.FLAKE8_CODECLIMATE}"]
    else:
        format_args = [f"--output-file={config.FLAKE8_TXT}", "--statistics", "--show-source"]

    session.run(
        "flake8", "--exit-zero", "--format=html", f"--htmldir={config.FLAKE8_HTML}", *format_args, config.MAIN_PACKAGE,
    )
