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
"""Allows running CI scripts within a Docker container."""
import os
import random
import shlex
import shutil

from nox import options

from ci import config
from ci import nox

if shutil.which("docker"):

    @nox.session(reuse_venv=True)
    def docker(session: nox.Session) -> None:
        """Run a nox session in a container that targets a specific Python version.

        This will invoke nox with the given additional arguments.
        """

        try:
            args = ["--help"] if not session.posargs else session.posargs
            python, *args = args
            args = shlex.join(args)

            if python not in config.DOCKER_ENVS:
                print(f"\033[31m\033[1mNo environment called {python} found.\033[0m")
                raise IndexError
        except IndexError:
            env_example = random.choice(config.DOCKER_ENVS)
            command_example = random.choice(options.sessions)
            print(
                "USAGE: nox -s docker -- {env} [{arg}, ...]",
                "",
                docker.__doc__,
                f"For example: 'nox -s docker -- {env_example} -s {command_example}'",
                "",
                "Parameters:",
                "  {env}     The environment to build. Supported environments are:",
                *(f"              - {e}" for e in config.DOCKER_ENVS),
                "  {arg}     Argument to pass to nox within the container.",
                "",
                "Supported sessions include:",
                *(f"  - {s}" for s in options.sessions if s != "docker"),
                sep="\n",
            )
            return

        print("\033[33m<<<<<<<<<<<<<<<<<<<  ENTERING CONTAINER  >>>>>>>>>>>>>>>>>>>\033[0m")
        print(f"> will run 'nox {args}' in container using '{python}' image.")
        nox.shell(
            "docker",
            "run",
            "--mount",
            f"type=bind,source={os.path.abspath(os.getcwd())!r},target=/hikari",
            "--rm",
            "-it",
            python,
            f"/bin/sh -c 'cd hikari && pip install nox && nox {args}'",
        )
        print("\033[33m<<<<<<<<<<<<<<<<<<<  EXITING  CONTAINER  >>>>>>>>>>>>>>>>>>>\033[0m")
