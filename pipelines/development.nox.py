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

    print("Creating venv")
    session.run("virtualenv", ".venv", "--prompt=[hikari] ")

    print("Activating venv")
    posix_path = pathlib.Path() / ".venv" / "bin" / "activate_this.py"
    win32_path = pathlib.Path() / ".venv" / "Scripts" / "activate_this.py"
    if posix_path.is_file():
        session.run("python", str(posix_path.absolute()))
    else:
        session.run("python", str(win32_path.absolute()))

    print("Installing nox in venv")
    session.install("nox")

    print("Installing API dependencies")
    session.install("-Ur", "requirements.txt")

    print("Installing test dependencies")
    session.install("-Ur", "dev-requirements.txt")

    print("Installing MyPy dependencies")
    session.install("-Ur", "mypy-requirements.txt")

    print("Installing Flake8 dependencies")
    session.install("-Ur", "flake8-requirements.txt")
