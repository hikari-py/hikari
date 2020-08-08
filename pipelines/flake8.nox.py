# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import shutil

from pipelines import config
from pipelines import nox


@nox.session(reuse_venv=True)
def flake8(session: nox.Session) -> None:
    """Run code linting, SAST, and analysis."""
    session.install("-r", "requirements.txt", "-r", "flake-requirements.txt")

    if "GITLAB_CI" in os.environ or "--gitlab" in session.posargs:
        print("Generating HTML report")

        shutil.rmtree(config.FLAKE8_TXT, ignore_errors=True)

        session.run(
            "flake8", "--exit-zero", "--format=html", f"--htmldir={config.FLAKE8_HTML}", config.MAIN_PACKAGE,
        )

        shutil.rmtree(config.FLAKE8_TXT, ignore_errors=True)

        print("Detected GitLab, will output CodeClimate report next!")
        # If we add the args for --statistics or --show-source, the thing breaks
        # silently, and I cant find another decent package that actually works
        # in any of the gitlab-supported formats :(
        session.run(
            "flake8", "--exit-zero", "--format=junit-xml", f"--output-file={config.FLAKE8_JUNIT}", config.MAIN_PACKAGE,
        )

    print("Generating console output")

    shutil.rmtree(config.FLAKE8_TXT, ignore_errors=True)

    session.run(
        "flake8", f"--output-file={config.FLAKE8_TXT}", "--statistics", "--show-source", "--tee", config.MAIN_PACKAGE,
    )
