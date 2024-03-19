# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""User-experience extensions and utilities."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "init_logging",
    "print_banner",
    "warn_if_not_optimized",
    "supports_color",
    "HikariVersion",
    "check_for_updates",
)

import importlib.resources
import logging
import logging.config
import os
import pathlib
import platform
import re
import string
import sys
import typing
import warnings

import colorlog.escape_codes

from hikari import _about as about
from hikari.internal import data_binding
from hikari.internal import net

if typing.TYPE_CHECKING:
    from hikari.impl import config

    CmpTuple = typing.Tuple[int, int, int, typing.Union[int, float]]

# While this is discouraged for most purposes in libraries, this enables us to
# filter out the vast majority of clutter that most network logger calls
# create. This also has a very minute performance improvement for trace logging
# calls, as we have to use `logger.log` directly to utilise this properly.
# We append `_HIKARI` to the name to keep it unique from any other logging
# levels that may be in use.

TRACE: typing.Final[int] = logging.DEBUG - 5
logging.addLevelName(TRACE, "TRACE_HIKARI")

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.ux")


def init_logging(
    flavor: typing.Union[None, str, int, typing.Dict[str, typing.Any], os.PathLike[str]],
    allow_color: bool,
    force_color: bool,
) -> None:
    """Initialize logging for the user.

    !!! note
        If any handlers already exist, some opinionated defaults will be configured
        (mostly do to with logging efficiency and warning logging), but existing
        handlers will not be overwritten. You can disable this by passing
        [`None`][] as the `flavor` parameter.

    !!! warning
        This function is blocking!

    Parameters
    ----------
    flavor : typing.Optional[None, str, int, typing.Dict[str, typing.Any], os.PathLike[str]]
        The hint for configuring logging.

        This can be [`None`][] to not enable logging automatically.

        If you pass a [`str`][] or a [`int`][], it is interpreted as
        the global logging level to use, and should match one of `"DEBUG"`,
        `"INFO"`, `"WARNING"`, `"ERROR"` or `"CRITICAL"`.
        The configuration will be set up to use a `colorlog` coloured logger,
        and to use a sane logging format strategy. The output will be written
        to [`sys.stdout`][] using this configuration.

        If you pass a [`dict`][], it is treated as the mapping to pass to
        [`logging.config.dictConfig`][]. If the dict defines any handlers, default
        handlers will not be setup if `incremental` is not specified.

        If you pass a [`str`][] to an existing file or a [`os.PathLike`][], it is
        interpreted as the file to load config from using [`logging.config.fileConfig`][].

        Note that `"TRACE_HIKARI"` is a library-specific logging level
        which is expected to be more verbose than `"DEBUG"`.
    allow_color : bool
        If [`False`][], no colour is allowed. If [`True`][], the
        output device must be supported for colour to be enabled.
    force_color : bool
        If [`True`][], always force colour.

    Examples
    --------
    Simple logging setup:

    ```py
        init_logging("INFO")  # Registered logging level
        # or
        init_logging(20)  # Logging level as an int
    ```

    File config:

    ```py
        # See https://docs.python.org/3/library/logging.config.html#configuration-file-format for more info
        init_logging("path/to/file.ini")
    ```

    Setting up logging through a dict config:

    ```py
        # See https://docs.python.org/3/library/logging.config.html#dictionary-schema-details for more info
        init_logging(
            {
                "version": 1,
                "incremental": True,  # In incremental setups, the default stream handler will be setup
                "loggers": {
                    "hikari.gateway": {"level": "DEBUG"},
                    "hikari.ratelimits": {"level": "TRACE_HIKARI"},
                },
            }
        )
    ```
    """
    # One observation that has been repeatedly made from seeing beginners writing
    # bots in Python is that most people seem to have no idea what logging is or
    # why it is beneficial to use it. This results in them spending large amounts
    # of time scratching their head wondering why something is not working, staring
    # at a blank screen. If they had enabled logging, they would have immediately
    # known where the issue was. This usually ends up with support servers on Discord
    # being spammed with the same basic questions again and again and again...
    #
    # As part of Hikari's set of opinionated defaults, we turn logging on with
    # a desirable format that is coloured in an effort to draw the user's attention
    # to it, rather than encouraging them to ignore it.
    if flavor is None:
        return

    # Apparently this makes logging even more efficient!
    logging.logThreads = False
    logging.logProcesses = False
    logging.logMultiprocessing = False

    # DeprecationWarning is disabled by default, but it's useful to have enabled
    warnings.simplefilter("always", DeprecationWarning)
    logging.captureWarnings(True)

    if len(logging.root.handlers) != 0:
        # Something else is already setup, so don't overwrite it
        return

    if isinstance(flavor, str):
        # Syntactic sugar to allow paths as strings
        path = pathlib.Path(flavor)
        if path.expanduser().exists():
            flavor = path

    # Config through file
    if isinstance(flavor, os.PathLike):
        try:
            logging.config.fileConfig(flavor)
        except Exception as ex:
            raise RuntimeError("A problem occurred while trying to setup logging through file configuration") from ex
        return

    # Config through dict
    if isinstance(flavor, dict):
        try:
            logging.config.dictConfig(flavor)
        except Exception as ex:
            raise RuntimeError("A problem occurred while trying to setup logging through dict configuration") from ex

        if not flavor.get("incremental"):
            # Non-incremental setup, return
            return

        flavor = None

    # Default config (stream)
    try:
        if supports_color(allow_color, force_color):
            logging.basicConfig(level=flavor, stream=sys.stdout)
            handler = logging.root.handlers[0]
            handler.setFormatter(
                colorlog.formatter.ColoredFormatter(
                    fmt=(
                        "%(log_color)s%(bold)s%(levelname)-1.1s%(thin)s "  # Logging level
                        "%(asctime)23.23s "  # Date and time
                        "%(bold)s%(name)s: "  # Logger name
                        "%(thin)s%(message)s%(reset)s"  # Message
                    ),
                    force_color=True,
                )
            )
        else:
            logging.basicConfig(
                level=flavor,
                stream=sys.stdout,
                format=(
                    "%(levelname)-1.1s "  # Logging level
                    "%(asctime)23.23s "  # Date and time
                    "%(name)s: "  # Logger name
                    "%(message)s"  # Message
                ),
            )

    except Exception as ex:
        raise RuntimeError("A problem occurred while trying to setup default logging configuration") from ex


_UNCONDITIONAL_ANSI_FLAGS: typing.Final[typing.FrozenSet[str]] = frozenset(("PYCHARM_HOSTED", "WT_SESSION"))
"""Set of env variables which always indicate that ANSI flags should be included."""


def _read_banner(package: str) -> str:
    if sys.version_info >= (3, 9):
        with importlib.resources.files(package).joinpath("banner.txt").open("r", encoding="utf-8") as fp:
            return fp.read()
    else:
        return importlib.resources.read_text(package, "banner.txt", encoding="utf-8")


def print_banner(
    package: typing.Optional[str],
    allow_color: bool,
    force_color: bool,
    extra_args: typing.Optional[typing.Dict[str, str]] = None,
) -> None:
    """Print a banner of choice to [`sys.stdout`][].

    Inspired by Spring Boot, we display an ASCII logo on startup. This is styled
    to grab the user's attention, and contains info such as the library version,
    the Python interpreter, the OS, and links to our Discord server and
    documentation. Users can override this by placing a `banner.txt` in some
    package and referencing it in this call.

    !!! note
        The `banner.txt` must be in the root folder of the package.

    !!! warning
        This function is blocking!

    Parameters
    ----------
    package : typing.Optional[str]
        The package to find the `banner.txt` in, or [`None`][] if no
        banner should be shown.
    allow_color : bool
        If [`False`][], no colour is allowed. If [`True`][], the
        output device must be supported for colour to be enabled.
    force_color : bool
        If [`True`][], always force colour.
    extra_args : typing.Optional[typing.Dict[str, str]]
        If provided, extra $-substitutions to use when printing the banner.
        Default substitutions can not be overwritten.

    Raises
    ------
    ValueError
        If `extra_args` contains a default $-substitution.
    """
    if package is None:
        return

    raw_banner = _read_banner(package)

    system_bits = (platform.machine(), platform.system(), platform.release())
    filtered_system_bits = (s.strip() for s in system_bits if s.strip())

    args = {
        # Hikari stuff.
        "hikari_version": about.__version__,
        "hikari_git_sha1": about.__git_sha1__[:8],
        "hikari_copyright": about.__copyright__,
        "hikari_license": about.__license__,
        "hikari_install_location": os.path.abspath(os.path.dirname(about.__file__)),
        "hikari_documentation_url": about.__docs__,
        "hikari_discord_invite": about.__discord_invite__,
        "hikari_source_url": about.__url__,
        # Python stuff.
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        # Platform specific stuff I might remove later.
        "system_description": " ".join(filtered_system_bits),
    }

    if extra_args:
        for key in extra_args:
            if key in args:
                raise ValueError(f"Cannot overwrite $-substitution `{key}`. Please use a different key.")
        args.update(extra_args)

    if supports_color(allow_color, force_color):
        args.update(colorlog.escape_codes.escape_codes)
    else:
        for code in colorlog.escape_codes.escape_codes:
            args[code] = ""

    banner_str = string.Template(raw_banner).safe_substitute(args)
    sys.stdout.buffer.write(banner_str.encode("utf-8"))
    sys.stdout.flush()


def warn_if_not_optimized(suppress: bool) -> None:
    """Log a warning if not running in optimization mode."""
    if __debug__ and not suppress:
        _LOGGER.warning(
            "You are running on optimization level 0 (no optimizations), which may slow down your application. "
            "For production, consider using at least level 1 optimization by passing [-O][] to the python "
            "interpreter call"
        )


def supports_color(allow_color: bool, force_color: bool) -> bool:
    """Return [`True`][] if the terminal device supports color output.

    Parameters
    ----------
    allow_color : bool
        If [`False`][], no color is allowed. If [`True`][], the
        output device must be supported for this to return [`True`][].
    force_color : bool
        If [`True`][], return [`True`][] always, otherwise only
        return [`True`][] if the device supports color output and the
        `allow_color` flag is not [`False`][].

    Returns
    -------
    bool
        [`True`][] if color is allowed on the output terminal, or
        [`False`][] otherwise.
    """
    if not allow_color:
        return False

    # isatty is not always implemented, https://code.djangoproject.com/ticket/6223
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    clicolor = os.environ.get("CLICOLOR")
    if os.environ.get("CLICOLOR_FORCE", "0") != "0" or force_color:
        # https://bixense.com/clicolors/
        return True
    if clicolor is not None and clicolor != "0" and is_a_tty:
        # https://bixense.com/clicolors/
        return True
    if clicolor == "0":
        # https://bixense.com/clicolors/
        return False
    if os.environ.get("COLORTERM", "").casefold() in ("truecolor", "24bit"):
        # Seems to be used by Gnome Terminal, and Tmpod will beat me if I don't add it.
        # https://gist.github.com/XVilka/8346728#true-color-detection
        return True

    plat = sys.platform
    if plat == "Pocket PC":
        return False

    if plat == "win32":
        color_support = os.environ.get("TERM_PROGRAM") in ("mintty", "Terminus")
        color_support |= "ANSICON" in os.environ
        color_support &= is_a_tty
    else:
        color_support = is_a_tty

    color_support |= bool(os.environ.keys() & _UNCONDITIONAL_ANSI_FLAGS)
    return color_support


_VERSION_REGEX: typing.Final[typing.Pattern[str]] = re.compile(r"^(\d+)\.(\d+)\.(\d+)(\.[a-z]+)?(\d+)?$", re.I)


# This is a modified version of packaging.version.Version to better suit our needs
class HikariVersion:
    """Hikari strict version."""

    __slots__: typing.Sequence[str] = ("version", "prerelease", "_cmp")

    version: typing.Tuple[int, int, int]
    prerelease: typing.Optional[typing.Tuple[str, int]]

    def __init__(self, vstring: str) -> None:
        match = _VERSION_REGEX.match(vstring)
        if not match:
            raise ValueError(f"Invalid version: '{vstring}'")

        (major, minor, patch, prerelease, prerelease_num) = match.group(1, 2, 3, 4, 5)

        self.version = (int(major), int(minor), int(patch))
        self.prerelease = (prerelease, int(prerelease_num) if prerelease_num else 0) if prerelease else None

        prerelease_num = int(prerelease_num) if prerelease else float("inf")
        self._cmp = self.version + (prerelease_num,)

    def __str__(self) -> str:
        vstring = ".".join(map(str, self.version))

        if self.prerelease:
            vstring += "".join(map(str, self.prerelease))

        return vstring

    def __repr__(self) -> str:
        return f"HikariVersion('{str(self)}')"

    def __eq__(self, other: typing.Any) -> bool:
        return self._compare(other, lambda s, o: s == o)

    def __ne__(self, other: typing.Any) -> bool:
        return self._compare(other, lambda s, o: s != o)

    def __lt__(self, other: typing.Any) -> bool:
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other: typing.Any) -> bool:
        return self._compare(other, lambda s, o: s <= o)

    def __gt__(self, other: typing.Any) -> bool:
        return self._compare(other, lambda s, o: s > o)

    def __ge__(self, other: typing.Any) -> bool:
        return self._compare(other, lambda s, o: s >= o)

    def _compare(self, other: typing.Any, method: typing.Callable[[CmpTuple, CmpTuple], bool]) -> bool:
        if not isinstance(other, HikariVersion):
            return NotImplemented

        return method(self._cmp, other._cmp)


async def check_for_updates(http_settings: config.HTTPSettings, proxy_settings: config.ProxySettings) -> None:
    """Perform a check for newer versions of the library, logging any found."""
    if about.__git_sha1__.casefold() == "head":
        # We are not in a PyPI release, return
        return

    try:
        async with net.create_client_session(
            connector=net.create_tcp_connector(dns_cache=False, limit=1, http_settings=http_settings),
            connector_owner=True,
            http_settings=http_settings,
            raise_for_status=True,
            trust_env=proxy_settings.trust_env,
        ) as cs:
            async with cs.get(
                "https://pypi.org/pypi/hikari/json",
                allow_redirects=http_settings.max_redirects is not None,
                max_redirects=http_settings.max_redirects if http_settings.max_redirects is not None else 10,
                proxy=proxy_settings.url,
                proxy_headers=proxy_settings.all_headers,
            ) as resp:
                data = data_binding.default_json_loads(await resp.read())
                assert isinstance(data, dict)

        this_version = HikariVersion(about.__version__)
        is_dev = this_version.prerelease is not None
        newest_version: typing.Optional[HikariVersion] = None

        for release_string, artifacts in data["releases"].items():
            if not all(artifact["yanked"] for artifact in artifacts):
                v = HikariVersion(release_string)
                if (v.prerelease is not None and not is_dev) or v <= this_version:
                    # Don't encourage the user to upgrade from a stable to a dev release, nor a lower version...
                    continue

                if newest_version is not None and newest_version > v:
                    continue

                newest_version = v

        if newest_version:
            _LOGGER.info("A newer version of hikari is available, consider upgrading to %s", newest_version)
    except Exception as ex:
        _LOGGER.warning("Failed to fetch hikari version details", exc_info=ex)
