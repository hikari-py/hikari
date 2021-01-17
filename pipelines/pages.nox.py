# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
import shutil
import socket
import threading
import webbrowser

from pipelines import config
from pipelines import nox


def copy_from_in(src: str, dest: str) -> None:
    for parent, _, files in os.walk(src):
        sub_parent = os.path.relpath(parent, src)

        for file in files:
            sub_src = os.path.join(parent, file)
            sub_dest = os.path.normpath(os.path.join(dest, sub_parent, file))
            print(sub_src, "->", sub_dest)
            shutil.copy(sub_src, sub_dest)


@nox.session(reuse_venv=True)
@nox.inherit_environment_vars
def pages(session: nox.Session) -> None:
    """Generate website pages."""
    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)

    # Static
    print("Copying static objects...")
    copy_from_in(config.PAGES_DIRECTORY, config.ARTIFACT_DIRECTORY)

    # Documentation
    session.install("-r", "requirements.txt", "-r", "dev-requirements.txt")
    session.env["PDOC3_GENERATING"] = "1"

    print("Building documentation...")
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

    # Rename `hikari` into `documentation`
    # print("Renaming output dir...")
    # print(f"{config.ARTIFACT_DIRECTORY}/{config.MAIN_PACKAGE} -> {config.ARTIFACT_DIRECTORY}/documentation")
    # shutil.rmtree(f"{config.ARTIFACT_DIRECTORY}/documentation", ignore_errors=True)
    # shutil.move(f"{config.ARTIFACT_DIRECTORY}/{config.MAIN_PACKAGE}", f"{config.ARTIFACT_DIRECTORY}/documentation")

    # Pre-generated indexes
    if shutil.which("npm") is None:
        message = "'npm' not installed, can't prebuild index"
        if "CI" in os.environ:
            session.error(message)

        session.skip(message)

    print("Prebuilding index...")
    session.run("npm", "install", "lunr@2.3.7", external=True)
    session.run(
        "node",
        "scripts/prebuild_index.js",
        f"{config.ARTIFACT_DIRECTORY}/hikari/index.json",
        f"{config.ARTIFACT_DIRECTORY}/hikari/prebuilt_index.json",
        external=True,
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
