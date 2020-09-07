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
import ast
import atexit
import functools
import inspect
import os
import subprocess
import tempfile
import textwrap

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
tempdir = tempfile.TemporaryDirectory()
atexit.register(tempdir.cleanup)


def mypy_test(func):
    """This makes me feel so dirty but I love it.

    Extracts the source code from a decorated function using inspect, wraps
    it in a coroutine definition and fires it off to a mypy daemon.
    """

    @functools.wraps(func)
    def test(*_, **__):

        # We use the AST to find out where the function definition ends and the
        # function body starts. We then take the body and stick it in a fully
        # typed coroutine function where we know we can await anything.
        source_code = inspect.getsource(func)
        lines = source_code.split("\n")
        tree = ast.parse(source_code)
        first_line = tree.body[0].body[0].lineno
        body = "async def test() -> None:\n" + "\n".join(lines[first_line - 1 :])

        test_file = os.path.join(tempdir.name, func.__name__ + ".py")
        with open(test_file, "w") as fp:
            fp.write(body)

        proc = subprocess.Popen(["dmypy", "run", test_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(None)
        if proc.returncode != 0:
            raise AssertionError(
                "\n".join(
                    (
                        f"MyPy exited with status code {proc.returncode}",
                        "",
                        "STDOUT:",
                        textwrap.indent(stdout.decode("utf-8"), "    "),
                        "",
                        "STDERR:",
                        textwrap.indent(stderr.decode("utf-8"), "    "),
                        "",
                    )
                )
            )

    return test
