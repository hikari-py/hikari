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
"""Code-style jobs."""
import pathlib
import shutil
import subprocess
import time
import typing

from pipelines import config
from pipelines import nox

GIT = shutil.which("git")


@nox.session()
def reformat_code(session: nox.Session) -> None:
    """Remove trailing whitespace in source, run isort, codespell and then run black code formatter."""
    session.install(*nox.dev_requirements("formatting"))

    remove_trailing_whitespaces(session)

    session.run("isort", *config.PYTHON_REFORMATTING_PATHS)
    session.run("black", *config.PYTHON_REFORMATTING_PATHS)


@nox.session(venv_backend="none")
def check_trailing_whitespaces(session: nox.Session) -> None:
    """Check for trailing whitespaces in the project."""
    remove_trailing_whitespaces(session, check_only=True)


def remove_trailing_whitespaces(session: nox.Session, check_only: bool = False) -> None:
    session.log(f"Searching for stray trailing whitespaces in files ending in {config.REFORMATTING_FILE_EXTS}")

    count = 0
    total = 0

    start = time.perf_counter()
    for raw_path in config.FULL_REFORMATTING_PATHS:
        path = pathlib.Path(raw_path)

        dir_total, dir_count = remove_trailing_whitespaces_for_directory(pathlib.Path(path), session, check_only)

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


def remove_trailing_whitespaces_for_directory(
    root_path: pathlib.Path, session: nox.Session, check_only: bool
) -> typing.Tuple[int, int]:
    total = 0
    count = 0

    for path in root_path.glob("*"):
        if path.is_file():
            if path.name.casefold().endswith(config.REFORMATTING_FILE_EXTS):
                total += 1
                count += remove_trailing_whitespaces_for_file(str(path), session, check_only)
            continue

        dir_total, dir_count = remove_trailing_whitespaces_for_directory(path, session, check_only)

        total += dir_total
        count += dir_count

    return total, count


def remove_trailing_whitespaces_for_file(file: str, session: nox.Session, check_only: bool) -> bool:
    try:
        with open(file, "rb") as fp:
            lines = fp.readlines()
            new_lines = lines[:]

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

        with open(file, "wb") as fp:
            fp.writelines(new_lines)

        if GIT is not None:
            result = subprocess.check_call(
                [GIT, "add", file, "-vf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None
            )
            assert result == 0, f"`git add {file} -v' exited with code {result}"

        return True
    except Exception as ex:
        print("Failed to check", file, "because", type(ex).__name__, ex)
        return True
