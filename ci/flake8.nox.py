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


@nox.session(reuse_venv=True, default=True)
def flake8(session: nox.Session) -> None:
    """Run code linting, SAST, and analysis."""
    session.install("-r", "requirements.txt", "-r", "flake-requirements.txt")

    session.run(
        "flake8", "--exit-zero", "--format=html", f"--htmldir={config.FLAKE8_HTML}", config.MAIN_PACKAGE,
    )

    if "GITLAB_CI" in os.environ or "--gitlab" in session.posargs:
        print("Detected GitLab, will output CodeClimate report instead!")
        # If we add the args for --statistics or --show-source, the thing breaks
        # silently, and I cant find another decent package that actually works
        # in any of the gitlab-supported formats :(
        format_args = ["--format=junit-xml", f"--output-file={config.FLAKE8_JUNIT}"]
    else:
        format_args = [f"--output-file={config.FLAKE8_TXT}", "--statistics", "--show-source", "--tee"]
        # This is because flake8 just appends to the file, so you can end up with
        # a huge file with the same errors if you run it a couple of times.
        shutil.rmtree(config.FLAKE8_TXT, ignore_errors=True)

    session.run(
        "flake8", *format_args, config.MAIN_PACKAGE,
    )
