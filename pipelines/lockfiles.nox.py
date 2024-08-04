# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Lock file pipelines."""
import pathlib

from pipelines import config
from pipelines import nox


def _generate_lock(session: nox.Session, requirements_path: pathlib.Path) -> str:
    return session.run(
        "uv",
        "pip",
        "compile",
        requirements_path,
        "-q",
        "--universal",
        "--generate-hashes",
        "--python-version",
        "3.8.1",  # This will be the minimum version allowed for development dependencies
        silent=True,
    )


@nox.session(venv_backend="none")
def lock_dependencies(session: nox.Session) -> None:
    """Generate development dependencies locks."""

    for req_in in pathlib.Path(config.DEV_REQUIREMENTS_DIRECTORY).glob("*.in"):
        lock = _generate_lock(session, req_in)

        output_path = req_in.with_suffix(".txt")
        output_path.write_text(lock)


@nox.session(venv_backend="none")
def check_dependency_locks(session: nox.Session) -> None:
    """Check dependencies locks."""
    failure = False

    for req_in in pathlib.Path(config.DEV_REQUIREMENTS_DIRECTORY).glob("*.in"):
        expected = _generate_lock(session, req_in)

        output_path = req_in.with_suffix(".txt")
        current = output_path.read_text()

        if expected != current:
            failure = True
            session.warn(f"{output_path} is not up to date!")

    if failure:
        session.error("Found outdated locks, try running `nox -s lock-dependencies` to fix them")
