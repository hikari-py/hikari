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
import os
import shutil

from ci import config
from ci import nox


def copy_from_in(src: str, dest: str) -> None:
    for parent, dirs, files in os.walk(src):
        sub_parent = os.path.relpath(parent, src)

        for file in files:
            sub_src = os.path.join(parent, file)
            sub_dest = os.path.normpath(os.path.join(dest, sub_parent, file))
            print(sub_src, "->", sub_dest)
            shutil.copy(sub_src, sub_dest)


@nox.session(reuse_venv=True)
def pages(session: nox.Session) -> None:
    """Generate static pages containing resources and tutorials."""
    for n, v in os.environ.items():
        if n.startswith(("GITLAB_", "CI")) or n == "CI":
            session.env[n] = v

    if not os.path.exists(config.ARTIFACT_DIRECTORY):
        os.mkdir(config.ARTIFACT_DIRECTORY)
    copy_from_in(config.PAGES_DIRECTORY, config.ARTIFACT_DIRECTORY)
