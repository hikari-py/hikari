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
"""Py.test integration."""
import contextlib
import os
import shutil

from pipelines import config
from pipelines import nox

FLAGS = [
    "-c",
    config.PYTEST_INI,
    "-r",
    "a",
    "--full-trace",
    "--cov",
    config.MAIN_PACKAGE,
    "--cov-config",
    config.COVERAGE_INI,
    "--cov-report",
    "term",
    "--cov-report",
    f"html:{config.COVERAGE_HTML_PATH}",
    "--cov-branch",
    "--junitxml",
    config.COVERAGE_JUNIT_PATH,
    "--force-testdox",
    "--showlocals",
]


@nox.session(reuse_venv=True)
def pytest(session: nox.Session) -> None:
    """Run unit tests and measure code coverage."""
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")
    shutil.rmtree(".coverage", ignore_errors=True)
    session.run("python", "-m", "pytest", *FLAGS, *session.posargs, config.TEST_PACKAGE)


@nox.session(reuse_venv=True)
def pytest_profile(session: nox.Session) -> None:
    """Run pytest with a profiler enabled to debug test times."""
    session.posargs.append("--profile")
    session.posargs.append("--durations=0")
    pytest(session)
    print("Generating profiling reports in `prof' directory.")

    import pstats

    with open("prof/results-by-tottime.txt", "w") as fp:
        stats = pstats.Stats("prof/combined.prof", stream=fp)
        stats.sort_stats("tottime")
        stats.print_stats()

    with open("prof/results-by-ncalls.txt", "w") as fp:
        stats = pstats.Stats("prof/combined.prof", stream=fp)
        stats.sort_stats("calls")
        stats.print_stats()


@nox.session(reuse_venv=True)
def mutation_test(session: nox.Session) -> None:
    """Run mutation tests on a given module and test suite.

    This randomly mutates the module undergoing testing to make it invalid
    by altering parts of the code. It will then attempt to run the tests to
    verify that they now fail.
    """
    session.install(
        "-r", "requirements.txt", "-r", "dev-requirements.txt", "git+https://github.com/sixty-north/cosmic-ray"
    )

    with contextlib.suppress(Exception):
        os.mkdir(config.ARTIFACT_DIRECTORY)

    toml = os.path.join(config.ARTIFACT_DIRECTORY, "mutation.toml")

    path = input("What module do you wish to mutate? (e.g hikari/utilities) ")
    package = input("What module do you wish to test? (e.g tests/hikari/utilities) ")

    print("Creating config file")

    with open(toml, "w") as fp:
        cfg = (
            "[cosmic-ray]\n"
            f"module-path = {path!r}\n"
            "python-version = ''\n"
            "timeout = 10\n"
            "exclude-modules = []\n"
            f"test-command = 'pytest -x {package}'"
            "\n"
            "[cosmic-ray.execution-engine]\n"
            "name = 'local'\n"
            "\n"
            "[cosmic-ray.cloning]\n"
            "method = 'copy'\n"
            "commands = []\n"
        )

        print(cfg)

        fp.write(cfg)

    sqlite = os.path.join(config.ARTIFACT_DIRECTORY, "mutation.db")

    print("Initializing session and generating test cases")
    session.run("cosmic-ray", "init", toml, sqlite)

    print("Performing mutation tests")
    session.run("cosmic-ray", "exec", sqlite)

    print("Generating reports")
    session.run("cr-report", sqlite)


@nox.session(reuse_venv=True)
def coalesce_coverage(session: nox.Session) -> None:
    """Combine coverage stats from several CI jobs."""
    session.install("coverage")

    coverage_files = []
    for file in os.listdir(config.ARTIFACT_DIRECTORY):
        if file.endswith(".coverage"):
            coverage_files.append(os.path.join(config.ARTIFACT_DIRECTORY, file))
    print("files for coverage:", coverage_files)

    session.run("coverage", "combine", f"--rcfile={config.COVERAGE_INI}", *coverage_files)
    session.run("coverage", "report", "-i", "-m", f"--rcfile={config.COVERAGE_INI}")
