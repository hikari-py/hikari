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
import os
import shutil

from pipelines import config
from pipelines import nox

FILES_TO_CYTHONIZE = [
    "hikari/impl/buckets.py",
    "hikari/impl/cache.py",
    "hikari/impl/entity_factory.py",
    "hikari/impl/event_manager.py",
    "hikari/impl/event_manager_base.py",
    "hikari/impl/rate_limits.py",
]


@nox.session(reuse_venv=True)
def cythonize(session: nox.Session) -> None:
    """Cythonize the library."""
    session.install(
        "-r",
        "requirements.txt",
        # "Cython==3.0.0a9"
        "git+https://github.com/cython/cython@b68b21d97dadc3061cab433b491719973fa56f31#egg=Cython==3.0.0a10",
    )

    if os.path.exists(config.CYTHON_OUTPUT_DIRECTORY):
        shutil.rmtree(config.CYTHON_OUTPUT_DIRECTORY)
    os.mkdir(config.CYTHON_OUTPUT_DIRECTORY)

    for file in FILES_TO_CYTHONIZE:
        output_file = file[:-2].replace("/", ".") + "c"
        output_path = os.path.join(config.CYTHON_OUTPUT_DIRECTORY, output_file)
        session.run("cython", file, "-o", output_path)
