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
"""Documentation pages generation."""
from pipelines import config
from pipelines import nox


@nox.session()
def mkdocs(session: nox.Session):
    """Generate docs using mkdocs."""
    if "--no-refs" in session.posargs:
        session.env["ENABLE_MKDOCSTRINGS"] = "false"

    session.install("-e", ".", *nox.dev_requirements("mkdocs"))

    session.run("mkdocs", "build", "-d", config.DOCUMENTATION_OUTPUT_PATH)


@nox.session()
def mkdocs_serve(session: nox.Session):
    """Start an HTTP server that serves the generated docs in real time."""
    if "--no-refs" in session.posargs:
        session.env["ENABLE_MKDOCSTRINGS"] = "false"

    session.install("-e", ".", *nox.dev_requirements("mkdocs"))

    if "--no-reload" in session.posargs:
        session.run("mkdocs", "serve", "--no-livereload")
    else:
        session.run("mkdocs", "serve")
