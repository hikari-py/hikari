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
"""Black code-style jobs."""
import os
import shutil
import subprocess
import time

from ci import config
from ci import nox

REFORMATING_PATHS = [
    "hikari",
    "tests",
    "scripts",
    "ci",
    "setup.py",
    "noxfile.py",
]

GIT = shutil.which("git")
FILE_EXTS = (
    ".py",
    ".pyx",
    ".pyi",
    ".c",
    ".cpp",
    ".cxx",
    ".hpp",
    ".hxx",
    ".h",
    ".yml",
    ".yaml",
    ".html",
    ".htm",
    ".js",
    ".json",
    ".toml",
    ".css",
    ".md",
    ".dockerfile",
    "Dockerfile",
    ".editorconfig",
    ".gitattributes",
    ".json",
    ".gitignore",
    ".dockerignore",
    ".flake8",
    ".txt",
    ".sh",
    ".bat",
    ".ps1",
    ".rb",
    ".pl",
)

LINE_ENDING_PATHS = {
    *REFORMATING_PATHS,
    *(f for f in os.listdir(".") if os.path.isfile(f) and f.endswith(FILE_EXTS)),
    "pages",
    "docs",
    "insomnia",
}


@nox.session(reuse_venv=True)
def reformat_code(session: nox.Session) -> None:
    """Remove trailing whitespace in source, run isort and then run black code formatter."""
    remove_trailing_whitespaces()

    # Isort
    session.install("isort")
    session.run("isort", *REFORMATING_PATHS)

    # Black
    session.install("black")
    session.run("black", "--target-version", "py38", *REFORMATING_PATHS)


def remove_trailing_whitespaces() -> None:
    print("\033[36mnox > Searching for stray trailing whitespaces in files ending in", FILE_EXTS, "\033[0m")

    count = 0
    total = 0

    start = time.perf_counter()
    for path in LINE_ENDING_PATHS:
        if os.path.isfile(path):
            total += 1
            count += remove_trailing_whitespaces_for_file(path)

        for root, dirs, files in os.walk(path, topdown=True, followlinks=False):
            for file in files:
                if file.casefold().endswith(FILE_EXTS):
                    total += 1
                    count += remove_trailing_whitespaces_for_file(os.path.join(root, file))

                i = len(dirs) - 1
                while i >= 0:
                    if dirs[i] == "__pycache__":
                        del dirs[i]
                    i -= 1

    end = time.perf_counter()

    remark = "Good job!" if not count else "Will now continue to run black."
    print(
        "\033[36mnox > I had to fix",
        count,
        "file(s).",
        remark,
        f"Took {1_000 * (end - start):.2f}ms to check {total} files in this project.\033[0m",
    )


def remove_trailing_whitespaces_for_file(file) -> bool:
    try:
        with open(file) as fp:
            lines = fp.readlines()
            new_lines = lines[:]

        for i in range(len(new_lines)):
            line = lines[i].rstrip("\n\r \t")
            line += "\n"
            new_lines[i] = line

        if lines == new_lines:
            return False

        print("Removing trailing whitespaces present in", file)

        with open(file, "w") as fp:
            fp.writelines(new_lines)

        if GIT is not None:
            result = subprocess.check_call(
                [GIT, "add", file, "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None
            )
            assert result == 0, f"`git add {file} -v' exited with code {result}"
            return True
        return False
    except Exception as ex:
        print("Failed to check", file, "because", type(ex).__name__, ex)
        return False
