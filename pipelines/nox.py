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

from __future__ import annotations

import typing

import nox

NoxCallbackSigT = typing.Callable[[nox.Session], None]

# Default sessions should be defined here
nox.options.sessions = ["reformat-code", "codespell", "pytest", "ruff", "slotscheck", "mypy", "verify-types"]
nox.options.default_venv_backend = "uv"


def session(**kwargs: typing.Any) -> typing.Callable[[NoxCallbackSigT], NoxCallbackSigT]:  # noqa: ANN401
    """Session wrapper to give default job kwargs."""

    def decorator(func: NoxCallbackSigT) -> NoxCallbackSigT:
        name = func.__name__.replace("_", "-")
        reuse_venv = kwargs.pop("reuse_venv", True)
        return nox.session(name=name, reuse_venv=reuse_venv, **kwargs)(func)

    return decorator


def sync(
    session: nox.Session, /, *, self: bool = False, extras: typing.Sequence[str] = (), groups: typing.Sequence[str] = ()
) -> None:
    """Install session packages using `uv sync`."""
    if extras and not self:
        msg = "When specifying extras, set `self=True`."
        raise RuntimeError(msg)

    args: list[str] = []
    for extra in extras:
        args.extend(("--extra", extra))

    group_flag = "--group" if self else "--only-group"
    for group in groups:
        args.extend((group_flag, group))

    session.run_install(
        "uv", "sync", "--locked", *args, silent=True, env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    )
