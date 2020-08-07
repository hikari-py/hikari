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
"""Black code-style jobs."""
import os
import shutil
import subprocess
import time

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
    ".ini",
    ".cfg",
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
    ".gitlab",
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
