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
"""Code-style jobs."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import time

from pipelines import config
from pipelines import nox

GIT = shutil.which("git")


@nox.session()
def reformat_code(session: nox.Session) -> None:
    """Remove trailing whitespace in source and then run ruff code formatter."""
    nox.sync(session, groups=["ruff"])

    remove_trailing_whitespaces(session)

    # At the time of writing, sorting imports is not done when running formatting
    # and needs to be done with ruff check
    # see: https://docs.astral.sh/ruff/formatter/#sorting-imports
    session.run("ruff", "format", *config.PYTHON_REFORMATTING_PATHS)
    session.run("ruff", "check", "--select", "I", "--fix", *config.PYTHON_REFORMATTING_PATHS)


@nox.session(venv_backend="none")
def check_trailing_whitespaces(session: nox.Session) -> None:
    """Check for trailing whitespaces in the project."""
    remove_trailing_whitespaces(session, check_only=True)


def remove_trailing_whitespaces(session: nox.Session, /, *, check_only: bool = False) -> None:
    """Remove trailing whitespaces and ensure LR ends are being used."""
    session.log(f"Searching for stray trailing whitespaces in files ending in {config.REFORMATTING_FILE_EXTS}")

    count = 0
    total = 0

    start = time.perf_counter()
    for raw_path in config.FULL_REFORMATTING_PATHS:
        path = pathlib.Path(raw_path)

        dir_total, dir_count = _remove_trailing_whitespaces_for_directory(
            pathlib.Path(path), session, check_only=check_only
        )

        total += dir_total
        count += dir_count

    end = time.perf_counter()

    remark = "Good job! " if not count else ""
    message = "Had to fix" if not check_only else "Found issues in"
    call = session.error if check_only and count else session.log

    call(
        f"{message} {count} file(s). "
        f"{remark}Took {1_000 * (end - start):.2f}ms to check {total} files in this project."
        + ("\nTry running 'nox -s reformat-code' to fix them" if check_only and count else "")
    )


def _remove_trailing_whitespaces_for_directory(
    root_path: pathlib.Path, session: nox.Session, /, *, check_only: bool
) -> tuple[int, int]:
    total = 0
    count = 0

    for path in root_path.glob("*"):
        if path.is_file():
            if path.name.casefold().endswith(config.REFORMATTING_FILE_EXTS):
                total += 1
                count += _remove_trailing_whitespaces_for_file(path, session, check_only=check_only)
            continue

        dir_total, dir_count = _remove_trailing_whitespaces_for_directory(path, session, check_only=check_only)

        total += dir_total
        count += dir_count

    return total, count


def _remove_trailing_whitespaces_for_file(file: pathlib.Path, session: nox.Session, /, *, check_only: bool) -> bool:
    try:
        lines = file.read_bytes().splitlines(keepends=True)
        new_lines = lines.copy()

        for i in range(len(new_lines)):
            line = lines[i].rstrip(b"\n\r \t")
            line += b"\n"
            new_lines[i] = line

        if lines == new_lines:
            return False

        if check_only:
            session.warn(f"Trailing whitespaces found in {file}")
            return True

        session.log(f"Removing trailing whitespaces present in {file}")

        file.write_bytes(b"".join(lines))

        if GIT is not None:
            result = subprocess.check_call(  # noqa: S603
                [GIT, "add", file, "-vf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None
            )
            assert result == 0, f"`git add {file} -v' exited with code {result}"

    except Exception as ex:  # noqa: BLE001
        session.warn("Failed to check", file, "because", type(ex).__name__, ex)

    return True
