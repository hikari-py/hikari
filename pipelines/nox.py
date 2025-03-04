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
"""Wrapper around nox to give default job kwargs."""

from __future__ import annotations

import typing as _typing

from nox import options as _options
from nox import session as _session
from nox.sessions import Session

# Default sessions should be defined here
_options.sessions = ["reformat-code", "codespell", "pytest", "flake8", "slotscheck", "mypy", "verify-types"]
_options.default_venv_backend = "uv|venv"

_NoxCallbackSig = _typing.Callable[[Session], None]


def session(**kwargs: _typing.Any) -> _typing.Callable[[_NoxCallbackSig], _NoxCallbackSig]:
    def decorator(func: _NoxCallbackSig) -> _NoxCallbackSig:
        name = func.__name__.replace("_", "-")
        reuse_venv = kwargs.pop("reuse_venv", True)
        return _session(name=name, reuse_venv=reuse_venv, **kwargs)(func)

    return decorator


def dev_groups(*groups: str) -> _typing.Sequence[str]:
    args = []

    for group in groups:
        args.extend(("--group", group))

    return args
