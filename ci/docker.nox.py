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
