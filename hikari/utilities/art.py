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
    "default_palette",
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


def _supports_color(colour_flag_set: bool, force_colour_flag_set: bool) -> bool:  # pragma: no cover
    # isatty is not always implemented, https://code.djangoproject.com/ticket/6223
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    if os.getenv("CLICOLOR_FORCE", "0") != "0" or force_colour_flag_set:
        return True
    elif (os.getenv("CLICOLOR", "0") != "0" or colour_flag_set) and is_a_tty:
        return True

    plat = sys.platform
    supports_color = False

    if plat != "Pocket PC":
        if plat == "win32":
            supports_color |= os.getenv("TERM_PROGRAM", None) in ("mintty", "Terminus")
            supports_color |= "ANSICON" in os.environ
            supports_color &= is_a_tty
        else:
            supports_color = is_a_tty

        supports_color |= bool(os.getenv("PYCHARM_HOSTED", ""))

    return supports_color


def default_palette(colour_flag_set: bool, force_colour_flag_set: bool) -> ConsolePalette:  # pragma: no cover
    """Generate the default pallete to use for the runtime.

    Contains a set of constant escape codes that are able to be printed.

    These codes will force the console to change colour or style, if supported.

    On unsupported platforms, these will be empty strings, thus making them safe
    to be used on non-coloured terminals or in logs specifically.

    This will also respect `CLICOLOR` and `CLICOLOR_FORCE` environment
    variables if `colour_flag_set` is `builtins.False` and
    `force_colour_flag_set` is also `builtins.False`.
    See https://bixense.com/clicolors/ for details.

    Parameters
    ----------
    colour_flag_set : builtins.bool
        If `builtins.True` then colour should be on if the output is a TTY.
    force_colour_flag_set : builtins.bool
        Same as `colour_flag_set` but forces colour for everything.


    Returns
    -------
    ConsolePalette
        A console palette to use.
    """
    # Modified from
    # https://github.com/django/django/blob/master/django/core/management/color.py

    supports_color = _supports_color(colour_flag_set, force_colour_flag_set)

    if supports_color:
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


def get_default_logging_format(palette: typing.Optional[ConsolePalette] = None) -> str:
    """Generate the default library logger format string.

    Parameters
    ----------
    palette : typing.Optional[ConsolePalette]
        The custom palette to use. Defaults to sane environment-dependent
        ANSI colour-codes if not specified and CLICOLOR/CLICOLOR_FORCE
        environment variables are not set.

    Returns
    -------
    builtins.str
        The string logging console format.
    """
    palette = palette or default_palette(False, False)

    return (
        f"{palette.red}%(levelname)-1.1s{palette.default} {palette.yellow}%(asctime)23.23s"
        f"{palette.default} {palette.bright}{palette.green}%(name)s: {palette.default}{palette.cyan}%(message)s"
        f"{palette.default}"
    )


def _default_banner_args() -> typing.Mapping[str, str]:
    system_bits = (
        platform.release(),
        platform.system(),
        platform.machine(),
    )
    filtered_system_bits = (s.strip() for s in system_bits if s.strip())

    return types.MappingProxyType(
        {
            # Hikari stuff.
            "hikari_version": _about.__version__,
            "hikari_git_sha1": _about.__git_sha1__,
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
            "system_description": " ".join(filtered_system_bits),
        }
    )


DEFAULT_BANNER_ARGS: typing.Final[typing.Mapping[str, str]] = _default_banner_args()


def get_banner(
    package: str = "hikari",
    palette: typing.Optional[ConsolePalette] = None,
    args: typing.Mapping[str, str] = DEFAULT_BANNER_ARGS,
) -> str:
    """Attempt to read a banner.txt from the given package.

    Parameters
    ----------
    package : builtins.str
        The package to read the banner.txt from. Defaults to `hikari`.
    palette : typing.Optional[ConsolePalette]
        The console palette to use (defaults to sane ANSI colour defaults or
        empty-strings if colours are not supported by your TTY and
        CLICOLOR/CLICOLOR_FORCE environment variables are not set.
    args : typing.Mapping[builtins.str, builtins.str]
        The mapping of arguments to interpolate into the banner, if desired.

    Returns
    -------
    builtins.str
        The raw banner that can be printed to the console.
    """
    palette = palette or default_palette(False, False)

    params = {**attr.asdict(palette), **args}

    with resources.open_text(package, "banner.txt") as banner_fp:
        return string.Template(banner_fp.read()).safe_substitute(params)
