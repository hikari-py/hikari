# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""User-experience extensions and utilities."""
from __future__ import annotations

__all__: typing.List[str] = ["init_logging", "print_banner", "supports_color", "HikariVersion", "check_for_updates"]

import distutils.version
import importlib.resources
import logging.config
import os
import platform
import re
import string
import sys
import time
import typing

import colorlog  # type: ignore[import]

from hikari import _about as about
from hikari.internal import net

if typing.TYPE_CHECKING:
    from hikari import config

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
    flavor: typing.Union[None, str, int, typing.Dict[str, typing.Any]],
    allow_color: bool,
    force_color: bool,
) -> None:
    """Attempt to initialize logging for the user.

    If any handlers already exist, this is ignored entirely. This ensures the
    user can use any existing logging configuration without us interfering.
    You can manually disable this by passing `None` as the `flavor` parameter.

    Parameters
    ----------
    flavor : typing.Optional[builtins.None, builtins.str, typing.Dict[builtins.str, typing.Any]]
        The hint for configuring logging.

        This can be `builtins.None` to not enable logging automatically.

        If you pass a `builtins.str` or a `builtins.int`, it is interpreted as
        the global logging level to use, and should match one of `"DEBUG"`,
        `"INFO"`, `"WARNING"`, `"ERROR"` or `"CRITICAL"`, if `builtins.str`.
        The configuration will be set up to use a `colorlog` coloured logger,
        and to use a sane logging format strategy. The output will be written
        to `sys.stderr` using this configuration.

        If you pass a `builtins.dict`, it is treated as the mapping to pass to
        `logging.config.dictConfig`.
    allow_color : builtins.bool
        If `builtins.False`, no colour is allowed. If `builtins.True`, the
        output device must be supported for this to return `builtins.True`.
    force_color : builtins.bool
        If `builtins.True`, return `builtins.True` always, otherwise only
        return `builtins.True` if the device supports colour output and the
        `allow_color` flag is not `builtins.False`.
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

    if len(logging.root.handlers) != 0 or flavor is None:
        # Skip, the user is using something else to configure their logging.
        return

    if isinstance(flavor, dict):
        logging.config.dictConfig(flavor)
        return

    # Apparently this makes logging even more efficient!
    logging.logThreads = False
    logging.logProcesses = False
    if supports_color(allow_color, force_color):
        colorlog.basicConfig(
            level=flavor,
            format="%(log_color)s%(bold)s%(levelname)-1.1s%(thin)s %(asctime)23.23s %(bold)s%(name)s: "
            "%(thin)s%(message)s%(reset)s",
            stream=sys.stderr,
        )
    else:
        logging.basicConfig(
            level=flavor,
            format="%(levelname)-1.1s %(asctime)23.23s %(name)s: %(message)s",
            stream=sys.stderr,
        )

    logging.captureWarnings(True)


def print_banner(package: typing.Optional[str], allow_color: bool, force_color: bool) -> None:
    """Print a banner of choice to `sys.stdout`.

    Inspired by Spring Boot, we display an ASCII logo on startup. This is styled
    to grab the user's attention, and contains info such as the library version,
    the Python interpreter, the OS, and links to our Discord server and
    documentation. Users can override this by placing a `banner.txt' in some
    package and referencing it in this call.

    Parameters
    ----------
    package : typing.Optional[builtins.str]
        The package to find the `banner.txt` in, or `builtins.None` if no
        banner should be shown.

        !!! note
            The `banner.txt` must be in the root folder of the package.
    allow_color : builtins.bool
        If `builtins.False`, no colour is allowed. If `builtins.True`, the
        output device must be supported for this to return `builtins.True`.
    force_color : builtins.bool
        If `builtins.True`, return `builtins.True` always, otherwise only
        return `builtins.True` if the device supports colour output and the
        `allow_color` flag is not `builtins.False`.
    """
    if package is None:
        return

    raw_banner = importlib.resources.read_text(package, "banner.txt")

    system_bits = (
        platform.machine(),
        platform.system(),
        platform.release(),
    )
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

    if supports_color(allow_color, force_color):
        args.update(colorlog.escape_codes)
    else:
        for code in colorlog.escape_codes:
            args[code] = ""

    sys.stdout.write(string.Template(raw_banner).safe_substitute(args))
    # Give the stream some time to flush
    sys.stdout.flush()
    time.sleep(0.125)


def supports_color(allow_color: bool, force_color: bool) -> bool:
    """Return `builtins.True` if the terminal device supports color output.

    Parameters
    ----------
    allow_color : builtins.bool
        If `builtins.False`, no color is allowed. If `builtins.True`, the
        output device must be supported for this to return `builtins.True`.
    force_color : builtins.bool
        If `builtins.True`, return `builtins.True` always, otherwise only
        return `builtins.True` if the device supports color output and the
        `allow_color` flag is not `builtins.False`.

    Returns
    -------
    builtins.bool
        `builtins.True` if color is allowed on the output terminal, or
        `builtins.False` otherwise.
    """
    if not allow_color:
        return False

    # isatty is not always implemented, https://code.djangoproject.com/ticket/6223
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    if os.getenv("CLICOLOR_FORCE", "0") != "0" or force_color:
        # https://bixense.com/clicolors/
        return True
    elif os.getenv("CLICOLOR", "0") != "0" and is_a_tty:
        # https://bixense.com/clicolors/
        return True
    elif os.getenv("COLORTERM", "").casefold() in ("truecolor", "24bit"):
        # Seems to be used by Gnome Terminal, and Tmpod will beat me if I don't add it.
        # https://gist.github.com/XVilka/8346728#true-color-detection
        return True

    plat = sys.platform
    color_support = False

    if plat != "Pocket PC":
        if plat == "win32":
            color_support |= os.getenv("TERM_PROGRAM", None) in ("mintty", "Terminus")
            color_support |= "ANSICON" in os.environ
            color_support &= is_a_tty
        else:
            color_support = is_a_tty

        color_support |= bool(os.getenv("PYCHARM_HOSTED", ""))

    return color_support


class HikariVersion(distutils.version.StrictVersion):
    """Hikari-compatible strict version."""

    # Not typed correctly on distutils, so overriding it raises a false positive...
    version_re: typing.ClassVar[typing.Final[re.Pattern[str]]] = re.compile(  # type: ignore[misc]
        r"^(\d+)\.(\d+)(\.(\d+))?(\.[a-z]+)?(\d+)?$", re.I
    )

    # Parse doesnt set the prerelease correctly, so we overwrite it to fix it.
    #
    # Not typed correctly on distutils, so overriding it raises a false positive...
    def parse(self, vstring: str) -> None:  # type: ignore[override]
        match = self.version_re.match(vstring)
        if not match:
            raise ValueError(f"invalid version number '{vstring}'")

        (major, minor, patch, prerelease, prerelease_num) = match.group(1, 2, 4, 5, 6)

        self.version = (int(major), int(minor), int(patch) if patch else 0)

        if prerelease:
            self.prerelease = (prerelease, int(prerelease_num))
        else:
            self.prerelease = None

    def __str__(self) -> str:
        vstring = ".".join(map(str, self.version))

        if self.prerelease:
            vstring = vstring + self.prerelease[0] + str(self.prerelease[1])

        return vstring


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
                data = await resp.json()

        this_version = HikariVersion(about.__version__)
        is_dev = this_version.prerelease is not None
        newer_releases: typing.List[HikariVersion] = []

        for release_string, artifacts in data["releases"].items():
            if not all(artifact["yanked"] for artifact in artifacts):
                v = HikariVersion(release_string)
                if v.prerelease is not None and not is_dev:
                    # Don't encourage the user to upgrade from a stable to a dev release...
                    continue

                if v.version == this_version.version and v.prerelease == this_version.prerelease:
                    continue

                if v > this_version:
                    newer_releases.append(v)
        if newer_releases:
            newest = max(newer_releases)
            _LOGGER.info("A newer version of hikari is available, consider upgrading to %s", newest)
    except Exception as ex:
        _LOGGER.debug("Failed to fetch hikari version details", exc_info=ex)
