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
from __future__ import annotations

import pathlib
import platform
import shutil

from pipelines import nox


@nox.session()
def init(session: nox.Session) -> None:
    """Initialize a development environment."""
    session.install("virtualenv")

    other_venvs = [pathlib.Path() / "venv"]

    for potential_venv in other_venvs:
        if potential_venv.exists() and potential_venv.is_dir():
            message = f"Found a venv at {potential_venv}, would you like to destroy it? [yn] "
            while (response := input(message).casefold()) not in "yn":
                pass

            if response == "y":
                print("rm", potential_venv)
                shutil.rmtree(potential_venv.absolute())

    platform_name = platform.uname().system

    print("Creating venv")
    session.run("virtualenv", ".venv", "--prompt=[hikari] ")

    print("Activating venv")
    posix_path = pathlib.Path() / ".venv" / "bin" / "pip"
    win32_path = pathlib.Path() / ".venv" / "Scripts" / "pip.exe"
    if platform_name == "Windows":
        base_install_args = str(win32_path.absolute()), "install"
    else:
        base_install_args = str(posix_path.absolute()), "install"

    print("Installing nox in venv")
    session.run(*base_install_args, "nox", external=True)

    print("Installing API dependencies")
    session.run(*base_install_args, "-Ur", "requirements.txt", external=True)

    print("Installing test dependencies")
    session.run(*base_install_args, "-Ur", "dev-requirements.txt", external=True)

    print("Installing MyPy dependencies")
    session.run(*base_install_args, "-Ur", "mypy-requirements.txt", external=True)

    print("Installing Flake8 dependencies")
    session.run(*base_install_args, "-Ur", "flake8-requirements.txt", external=True)

    print("\nFinished setting up venv, to activate it run ", end="")
    if platform_name == "Windows":
        print("an activate script in .venv/scripts/")
    else:
        print("'source .venv/bin/activate'")
