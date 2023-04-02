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
"""Website pages generation."""
import contextlib
import functools
import http.server
import logging
import os
import socket
import threading
import webbrowser

from pipelines import config
from pipelines import nox


@nox.session()
def sphinx(session: nox.Session):
    """Generate docs using sphinx."""
    if "--no-refs" in session.posargs:
        session.env["SKIP_REFERENCE_DOCS"] = "1"

    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)

    session.install("-e", ".", *nox.dev_requirements("sphinx"))

    session.run(
        "sphinx-build", "-M", "dirhtml", config.DOCUMENTATION_DIRECTORY, os.path.join(config.ARTIFACT_DIRECTORY, "docs")
    )


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        directory = os.path.join(config.ARTIFACT_DIRECTORY, "docs", "dirhtml")
        super().__init__(directory=directory, *args, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


class HTTPServerThread(threading.Thread):
    def __init__(self) -> None:
        logging.basicConfig(level="INFO")

        super().__init__(name="HTTP Server", daemon=True)
        # Use a socket to obtain a random free port to host the HTTP server on.
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind(("", 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.host, self.port = sock.getsockname()

        self.server = http.server.HTTPServer((self.host, self.port), RequestHandler)

    def run(self) -> None:
        self.server.serve_forever()

    def close(self) -> None:
        self.server.shutdown()


@nox.session(venv_backend="none")
def view_docs(_: nox.Session) -> None:
    """Start an HTTP server for any generated pages in `/public/docs/dirhtml`."""
    with contextlib.closing(HTTPServerThread()) as thread:
        thread.start()
        webbrowser.open(f"http://{thread.host}:{thread.port}")
        thread.join()
