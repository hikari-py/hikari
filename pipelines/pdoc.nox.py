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
"""Pdoc documentation generation."""
import contextlib
import functools
import http.server
import logging
import os
import shutil
import socket
import threading
import webbrowser

from pipelines import config
from pipelines import nox


@nox.session(reuse_venv=True)
@nox.inherit_environment_vars
def pdoc(session: nox.Session) -> None:
    """Generate documentation with pdoc."""
    session.install("-r", "requirements.txt")
    session.install("pdoc3")
    session.install("sphobjinv")
    session.env["PDOC3_GENERATING"] = "1"

    session.run(
        "python",
        "docs/patched_pdoc.py",
        config.MAIN_PACKAGE,
        "--html",
        "--output-dir",
        config.ARTIFACT_DIRECTORY,
        "--template-dir",
        config.DOCUMENTATION_DIRECTORY,
        "--force",
    )
    shutil.copyfile(
        os.path.join(config.DOCUMENTATION_DIRECTORY, config.LOGO_SOURCE),
        os.path.join(config.ARTIFACT_DIRECTORY, config.LOGO_SOURCE),
    )


class HTTPServerThread(threading.Thread):
    def __init__(self) -> None:
        logging.basicConfig(level="INFO")

        super().__init__(name="HTTP Server", daemon=True)
        # Use a socket to obtain a random free port to host the HTTP server on.
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind(("", 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.host, self.port = sock.getsockname()

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=config.ARTIFACT_DIRECTORY)
        self.server = http.server.HTTPServer((self.host, self.port), handler)

    def run(self) -> None:
        self.server.serve_forever()

    def close(self) -> None:
        self.server.shutdown()


@nox.session(reuse_venv=True)
def test_pages(_: nox.Session) -> None:
    """Start an HTTP server for any generated pages in `/public`."""
    with contextlib.closing(HTTPServerThread()) as thread:
        thread.start()
        webbrowser.open(f"http://{thread.host}:{thread.port}")
        thread.join()
