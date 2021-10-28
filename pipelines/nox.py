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
"""Wrapper around nox to give default job kwargs."""
import functools
import os
import subprocess
import typing

from nox import options as _options
from nox import session as _session
from nox.sessions import Session

from pipelines import config

# Default sessions should be defined here
_options.sessions = ["reformat-code", "pytest", "flake8", "mypy", "verify-types", "safety", "pdoc"]

_NoxCallbackSig = typing.Callable[[Session], None]


def session(
    *, only_if: typing.Callable[[], bool] = lambda: True, reuse_venv: bool = False, **kwargs: typing.Any
) -> typing.Callable[[_NoxCallbackSig], typing.Union[_NoxCallbackSig, Session]]:
    def decorator(func: _NoxCallbackSig) -> typing.Union[_NoxCallbackSig, Session]:
        func.__name__ = func.__name__.replace("_", "-")

        return _session(reuse_venv=reuse_venv, **kwargs)(func) if only_if() else func

    return decorator


def inherit_environment_vars(func: _NoxCallbackSig) -> _NoxCallbackSig:
    @functools.wraps(func)
    def logic(session: Session) -> None:
        for n, v in os.environ.items():
            session.env[n] = v
        return func(session)

    return logic


def shell(arg: str, *args: str) -> int:
    command = " ".join((arg, *args))
    print("nox > shell >", command)
    return subprocess.check_call(command, shell=True)


if not os.path.isdir(config.ARTIFACT_DIRECTORY):
    os.mkdir(config.ARTIFACT_DIRECTORY)
