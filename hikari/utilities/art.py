# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Stuff for handling banners and pretty logging."""
from __future__ import annotations

__all__: typing.List[str] = [
    "ConsolePalette",
    "DEFAULT_PALETTE",
    "DEFAULT_BANNER_ARGS",
    "get_default_logging_format",
    "get_banner",
]

import os
import platform
import string
import sys
import types
import typing
from importlib import resources

import attr

from hikari import _about
from hikari.utilities import attr_extensions


@typing.final
@attr_extensions.with_copy
@attr.s(frozen=True, kw_only=True)
class ConsolePalette:
    """Data class containing printable escape codes for colouring console output."""

    default: str = attr.ib(default="")
    bright: str = attr.ib(default="")
    underline: str = attr.ib(default="")
    invert: str = attr.ib(default="")
    red: str = attr.ib(default="")
    green: str = attr.ib(default="")
    yellow: str = attr.ib(default="")
    blue: str = attr.ib(default="")
    magenta: str = attr.ib(default="")
    cyan: str = attr.ib(default="")
    white: str = attr.ib(default="")
    bright_red: str = attr.ib(default="")
    bright_green: str = attr.ib(default="")
    bright_yellow: str = attr.ib(default="")
    bright_blue: str = attr.ib(default="")
    bright_magenta: str = attr.ib(default="")
    bright_cyan: str = attr.ib(default="")
    bright_white: str = attr.ib(default="")
    framed: str = attr.ib(default="")
    dim: str = attr.ib(default="")


def _default_palette() -> ConsolePalette:  # pragma: no cover
    # Modified from
    # https://github.com/django/django/blob/master/django/core/management/color.py
    _plat = sys.platform
    _supports_color = False

    # isatty is not always implemented, https://code.djangoproject.com/ticket/6223
    _is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    if _plat != "Pocket PC":
        if _plat == "win32":
            _supports_color |= os.getenv("TERM_PROGRAM", None) in ("mintty", "Terminus")
            _supports_color |= "ANSICON" in os.environ
            _supports_color &= _is_a_tty
        else:
            _supports_color = _is_a_tty

        _supports_color |= bool(os.getenv("PYCHARM_HOSTED", ""))

    if _supports_color:
        return ConsolePalette(
            default="\033[0m",
            bright="\033[1m",
            underline="\033[4m",
            invert="\033[7m",
            red="\033[31m",
            green="\033[32m",
            yellow="\033[33m",
            blue="\033[34m",
            magenta="\033[35m",
            cyan="\033[36m",
            white="\033[37m",
            bright_red="\033[91m",
            bright_green="\033[92m",
            bright_yellow="\033[93m",
            bright_blue="\033[94m",
            bright_magenta="\033[95m",
            bright_cyan="\033[96m",
            bright_white="\033[97m",
            framed="\033[51m",
            dim="\033[2m",
        )

    return ConsolePalette()


DEFAULT_PALETTE: typing.Final[ConsolePalette] = _default_palette()
"""Contains a set of constant escape codes that are able to be printed.

These codes will force the console to change colour or style, if supported.

On unsupported platforms, these will be empty strings, thus making them safe
to be used on non-coloured terminals or in logs specifically.
"""


def get_default_logging_format(palette: ConsolePalette = DEFAULT_PALETTE) -> str:
    """Generate the default library logger format string.

    Parameters
    ----------
    palette : ConsolePalette
        The custom palette to use. Defaults to sane environment-dependent
        ANSI colour-codes if not specified.

    Returns
    -------
    builtins.str
        The string logging console format.
    """
    return (
        f"{palette.red}%(levelname)-1.1s{palette.default} {palette.yellow}%(asctime)23.23s"
        f"{palette.default} {palette.bright}{palette.green}%(name)s: {palette.default}{palette.cyan}%(message)s"
        f"{palette.default}"
    )


DEFAULT_BANNER_ARGS: typing.Final[typing.Mapping[str, str]] = types.MappingProxyType(
    {
        # Hikari stuff.
        "hikari_version": _about.__version__,
        "hikari_git_branch": _about.__git_branch__,
        "hikari_git_sha1": _about.__git_sha1__,
        "hikari_git_when": _about.__git_when__,
        "hikari_copyright": _about.__copyright__,
        "hikari_license": _about.__license__,
        "hikari_install_location": os.path.abspath(os.path.dirname(_about.__file__)),
        "hikari_documentation_url": _about.__docs__,
        "hikari_discord_invite": _about.__discord_invite__,
        "hikari_source_url": _about.__url__,
        # Python stuff.
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_build": " ".join(platform.python_build()),
        "python_branch": platform.python_branch(),
        "python_compiler": platform.python_compiler(),
        # Platform specific stuff I might remove later.
        "libc_version": " ".join(platform.libc_ver()),
        # System stuff.
        "platform_system": platform.system(),
        "platform_architecture": " ".join(platform.architecture()),
    }
)


def get_banner(
    package: str = "hikari",
    palette: ConsolePalette = DEFAULT_PALETTE,
    args: typing.Mapping[str, str] = DEFAULT_BANNER_ARGS,
) -> str:
    """Attempt to read a banner.txt from the given package.

    Parameters
    ----------
    package : builtins.str
        The package to read the banner.txt from. Defaults to `hikari`.
    palette : ConsolePalette
        The console palette to use (defaults to sane ANSI colour defaults or
        empty-strings if colours are not supported by your TTY.
    args : typing.Mapping[builtins.str, builtins.str]
        The mapping of arguments to interpolate into the banner, if desired.

    Returns
    -------
    builtins.str
        The raw banner that can be printed to the console.
    """
    params = {**attr.asdict(palette), **args}

    with resources.open_text(package, "banner.txt") as banner_fp:
        return string.Template(banner_fp.read()).safe_substitute(params)
