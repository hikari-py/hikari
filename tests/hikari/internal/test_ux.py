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
import contextlib
import importlib
import logging
import logging.config
import os
import pathlib
import platform
import string
import sys
import time

import colorlog
import mock
import pytest

from hikari import _about
from hikari.impl import config
from hikari.internal import data_binding
from hikari.internal import net
from hikari.internal import ux
from tests.hikari import hikari_test_helpers


class TestInitLogging:
    def test_when_handlers_already_set_up(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[None]))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_basic_config = stack.enter_context(mock.patch.object(logging, "basicConfig"))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))

        with stack:
            ux.init_logging("LOGGING_LEVEL", True, False)

        logging_dict_config.assert_not_called()
        logging_basic_config.assert_not_called()
        colored_formatter.assert_not_called()

    def test_when_handlers_specify_not_to_set_up(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[]))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_basic_config = stack.enter_context(mock.patch.object(logging, "basicConfig"))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))

        with stack:
            ux.init_logging(None, True, False)

        logging_dict_config.assert_not_called()
        logging_basic_config.assert_not_called()
        colored_formatter.assert_not_called()

    def test_when_flavour_is_a_dict_and_is_not_incremental(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[]))
        stack.enter_context(mock.patch.object(ux, "supports_color", return_value=False))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_file_config = stack.enter_context(mock.patch.object(logging.config, "fileConfig"))
        logging_basic_config = stack.enter_context(mock.patch.object(logging, "basicConfig"))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))

        with stack:
            ux.init_logging({"hikari": {"level": "INFO"}}, True, False)

        logging_file_config.assert_not_called()
        logging_dict_config.assert_called_once_with({"hikari": {"level": "INFO"}})
        logging_basic_config.assert_not_called()
        colored_formatter.assert_not_called()

    def test_when_flavour_is_a_dict_and_is_incremental(self):
        # This will emulate it being populated during the basicConfig call
        def _basicConfig(*args, **kwargs):
            logging_basic_config(*args, **kwargs)
            stack.enter_context(mock.patch.object(logging.root, "handlers", new=[handler]))

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[]))
        stack.enter_context(mock.patch.object(ux, "supports_color", return_value=False))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_file_config = stack.enter_context(mock.patch.object(logging.config, "fileConfig"))
        handler = mock.Mock()
        logging_basic_config = mock.Mock()
        stack.enter_context(mock.patch.object(logging, "basicConfig", new=_basicConfig))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))

        with stack:
            ux.init_logging({"incremental": True, "hikari": {"level": "INFO"}}, True, False)

        logging_file_config.assert_not_called()
        logging_dict_config.assert_called_once_with({"incremental": True, "hikari": {"level": "INFO"}})
        logging_basic_config.assert_called_once_with(
            level=None, stream=sys.stdout, format="%(levelname)-1.1s %(asctime)23.23s %(name)s: %(message)s"
        )
        colored_formatter.assert_not_called()
        handler.setFormatter.assert_not_called()

    def test_when_supports_color(self):
        # This will emulate it being populated during the basicConfig call
        def _basicConfig(*args, **kwargs):
            logging_basic_config(*args, **kwargs)
            stack.enter_context(mock.patch.object(logging.root, "handlers", new=[handler]))

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[]))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_file_config = stack.enter_context(mock.patch.object(logging.config, "fileConfig"))
        handler = mock.Mock()
        logging_basic_config = mock.Mock()
        stack.enter_context(mock.patch.object(logging, "basicConfig", new=_basicConfig))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))
        supports_color = stack.enter_context(mock.patch.object(ux, "supports_color", return_value=True))

        with stack:
            ux.init_logging("LOGGING_LEVEL", True, False)

        logging_file_config.assert_not_called()
        logging_dict_config.assert_not_called()
        logging_basic_config.assert_called_once_with(level="LOGGING_LEVEL", stream=sys.stdout)
        colored_formatter.assert_called_once_with(
            fmt="%(log_color)s%(bold)s%(levelname)-1.1s%(thin)s %(asctime)23.23s %(bold)s%(name)s: "
            "%(thin)s%(message)s%(reset)s",
            force_color=True,
        )
        supports_color.assert_called_once_with(True, False)
        handler.setFormatter.assert_called_once_with(colored_formatter.return_value)

    def test_when_doesnt_support_color(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[]))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_basic_config = stack.enter_context(mock.patch.object(logging, "basicConfig"))
        logging_file_config = stack.enter_context(mock.patch.object(logging.config, "fileConfig"))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))
        supports_color = stack.enter_context(mock.patch.object(ux, "supports_color", return_value=False))

        with stack:
            ux.init_logging("LOGGING_LEVEL", True, False)

        logging_dict_config.assert_not_called()
        logging_file_config.assert_not_called()
        logging_basic_config.assert_called_once_with(
            level="LOGGING_LEVEL", format="%(levelname)-1.1s %(asctime)23.23s %(name)s: %(message)s", stream=sys.stdout
        )
        colored_formatter.assert_not_called()
        supports_color.assert_called_once_with(True, False)

    def test_when_flavour_is_pathlike(self):
        path = pathlib.Path("some/path/to/somewhere.ini")

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[]))
        pathlib_path = stack.enter_context(mock.patch.object(pathlib, "Path"))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_basic_config = stack.enter_context(mock.patch.object(logging, "basicConfig"))
        logging_file_config = stack.enter_context(mock.patch.object(logging.config, "fileConfig"))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))
        supports_color = stack.enter_context(mock.patch.object(ux, "supports_color", return_value=False))

        with stack:
            ux.init_logging(path, True, False)

        pathlib_path.assert_not_called()
        logging_dict_config.assert_not_called()
        logging_file_config.assert_called_once_with(path)
        logging_basic_config.assert_not_called()
        colored_formatter.assert_not_called()
        supports_color.assert_not_called()

    def test_when_flavour_is_an_existing_path(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(logging, "root", handlers=[]))
        pathlib_path = stack.enter_context(mock.patch.object(pathlib, "Path"))
        logging_dict_config = stack.enter_context(mock.patch.object(logging.config, "dictConfig"))
        logging_basic_config = stack.enter_context(mock.patch.object(logging, "basicConfig"))
        logging_file_config = stack.enter_context(mock.patch.object(logging.config, "fileConfig"))
        colored_formatter = stack.enter_context(mock.patch.object(colorlog.formatter, "ColoredFormatter"))
        supports_color = stack.enter_context(mock.patch.object(ux, "supports_color", return_value=False))

        with stack:
            ux.init_logging("some/path/to/somewhere.ini", True, False)

        pathlib_path.assert_called_once_with("some/path/to/somewhere.ini")
        logging_dict_config.assert_not_called()
        logging_file_config.assert_called_once_with(pathlib_path.return_value)
        logging_basic_config.assert_not_called()
        colored_formatter.assert_not_called()
        supports_color.assert_not_called()


class TestRedBanner:
    def test_when_above_3_9(self):
        class MockFile:
            context_entered = 0
            context_exited = 0

            def __enter__(self):
                self.context_entered += 1
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.context_exited += 1
                return None

            def read(self):
                return read

        class MockTraversable:
            joint_path = None
            open_mode = None
            mock_file = None
            open_encoding = None

            def joinpath(self, path):
                self.joint_path = path
                return self

            def open(self, mode, encoding):
                self.open_mode = mode
                self.open_encoding = encoding
                return self.mock_file

        traversable = MockTraversable()
        traversable.mock_file = MockFile()
        read = object()

        with mock.patch.object(sys, "version_info", new=(3, 9)):
            with mock.patch.object(importlib.resources, "files", return_value=traversable, create=True) as read_text:
                assert ux._read_banner("hikaru") is read

        read_text.assert_called_once_with("hikaru")
        assert traversable.joint_path == "banner.txt"
        assert traversable.open_mode == "r"
        assert traversable.open_encoding == "utf-8"
        assert traversable.mock_file.context_entered == 1
        assert traversable.mock_file.context_exited == 1

    def test_when_below_3_9(self):
        with mock.patch.object(sys, "version_info", new=(2, 7)):
            with mock.patch.object(importlib.resources, "read_text") as read_text:
                assert ux._read_banner("hikaru") is read_text.return_value

        read_text.assert_called_once_with("hikaru", "banner.txt", encoding="utf-8")


class TestPrintBanner:
    def test_when_package_is_none(self):
        with mock.patch.object(sys.stdout, "write") as write:
            ux.print_banner(None, True, False)

        write.assert_not_called()

    @pytest.fixture
    def mock_args(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(platform, "release", return_value="1.0.0"))
        stack.enter_context(mock.patch.object(platform, "system", return_value="Potato"))
        stack.enter_context(mock.patch.object(platform, "machine", return_value="Machine"))
        stack.enter_context(mock.patch.object(platform, "python_implementation", return_value="CPython"))
        stack.enter_context(mock.patch.object(platform, "python_version", return_value="4.0.0"))

        stack.enter_context(mock.patch.object(_about, "__version__", new="2.2.2"))
        stack.enter_context(mock.patch.object(_about, "__git_sha1__", new="12345678901234567890"))
        stack.enter_context(mock.patch.object(_about, "__copyright__", new="2020, Nekokatt"))
        stack.enter_context(mock.patch.object(_about, "__license__", new="MIT"))
        stack.enter_context(mock.patch.object(_about, "__file__", new="~/hikari"))
        stack.enter_context(mock.patch.object(_about, "__docs__", new="https://nekokatt.github.io/hikari/docs"))
        stack.enter_context(mock.patch.object(_about, "__discord_invite__", new="https://discord.gg/Jx4cNGG"))
        stack.enter_context(mock.patch.object(_about, "__url__", new="https://nekokatt.github.io/hikari"))

        with stack:
            yield None

    def test_when_supports_color(self, mock_args):
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(colorlog.escape_codes, "escape_codes", new={"red": 0, "green": 1, "blue": 2})
        )
        stack.enter_context(mock.patch.object(time, "sleep"))
        supports_color = stack.enter_context(mock.patch.object(ux, "supports_color", return_value=True))
        read_banner = stack.enter_context(mock.patch.object(ux, "_read_banner"))
        template = stack.enter_context(mock.patch.object(string, "Template"))
        abspath = stack.enter_context(mock.patch.object(os.path, "abspath", return_value="some path"))
        dirname = stack.enter_context(mock.patch.object(os.path, "dirname"))
        stdout = stack.enter_context(mock.patch.object(sys, "stdout"))

        with stack:
            ux.print_banner("hikaru", True, False)

        args = {
            # Hikari stuff.
            "hikari_version": "2.2.2",
            "hikari_git_sha1": "12345678",
            "hikari_copyright": "2020, Nekokatt",
            "hikari_license": "MIT",
            "hikari_install_location": "some path",
            "hikari_documentation_url": "https://nekokatt.github.io/hikari/docs",
            "hikari_discord_invite": "https://discord.gg/Jx4cNGG",
            "hikari_source_url": "https://nekokatt.github.io/hikari",
            "python_implementation": "CPython",
            "python_version": "4.0.0",
            "system_description": "Machine Potato 1.0.0",
            "red": 0,
            "green": 1,
            "blue": 2,
        }

        read_banner.assert_called_once_with("hikaru")
        template.assert_called_once_with(read_banner.return_value)
        safe_substitute = template.return_value.safe_substitute
        safe_substitute.assert_called_once_with(args)
        dirname.assert_called_once_with("~/hikari")
        abspath.assert_called_once_with(dirname())
        supports_color.assert_called_once_with(True, False)
        stdout.buffer.write.assert_called_once_with(safe_substitute.return_value.encode.return_value)
        stdout.flush.assert_called_once_with()

    def test_when_doesnt_supports_color(self, mock_args):
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(colorlog.escape_codes, "escape_codes", new={"red": 0, "green": 1, "blue": 2})
        )
        stack.enter_context(mock.patch.object(time, "sleep"))
        supports_color = stack.enter_context(mock.patch.object(ux, "supports_color", return_value=False))
        read_banner = stack.enter_context(mock.patch.object(ux, "_read_banner"))
        template = stack.enter_context(mock.patch.object(string, "Template"))
        abspath = stack.enter_context(mock.patch.object(os.path, "abspath", return_value="some path"))
        dirname = stack.enter_context(mock.patch.object(os.path, "dirname"))
        stdout = stack.enter_context(mock.patch.object(sys, "stdout"))

        with stack:
            ux.print_banner("hikaru", True, False)

        args = {
            # Hikari stuff.
            "hikari_version": "2.2.2",
            "hikari_git_sha1": "12345678",
            "hikari_copyright": "2020, Nekokatt",
            "hikari_license": "MIT",
            "hikari_install_location": "some path",
            "hikari_documentation_url": "https://nekokatt.github.io/hikari/docs",
            "hikari_discord_invite": "https://discord.gg/Jx4cNGG",
            "hikari_source_url": "https://nekokatt.github.io/hikari",
            "python_implementation": "CPython",
            "python_version": "4.0.0",
            "system_description": "Machine Potato 1.0.0",
            "red": "",
            "green": "",
            "blue": "",
        }

        template.assert_called_once_with(read_banner.return_value)
        safe_substitute = template.return_value.safe_substitute
        safe_substitute.assert_called_once_with(args)
        dirname.assert_called_once_with("~/hikari")
        abspath.assert_called_once_with(dirname())
        supports_color.assert_called_once_with(True, False)
        stdout.buffer.write.assert_called_once_with(safe_substitute.return_value.encode.return_value)
        stdout.flush.assert_called_once_with()

    def test_use_extra_args(self, mock_args):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(colorlog.escape_codes, "escape_codes", new={}))
        stack.enter_context(mock.patch.object(time, "sleep"))
        read_banner = stack.enter_context(mock.patch.object(ux, "_read_banner"))
        template = stack.enter_context(mock.patch.object(string, "Template"))
        stack.enter_context(mock.patch.object(os.path, "abspath", return_value="some path"))
        stdout = stack.enter_context(mock.patch.object(sys, "stdout"))

        extra_args = {"extra_argument_1": "one", "extra_argument_2": "two"}

        with stack:
            ux.print_banner("hikaru", True, False, extra_args=extra_args)

        args = {
            # Hikari stuff.
            "hikari_version": "2.2.2",
            "hikari_git_sha1": "12345678",
            "hikari_copyright": "2020, Nekokatt",
            "hikari_license": "MIT",
            "hikari_install_location": "some path",
            "hikari_documentation_url": "https://nekokatt.github.io/hikari/docs",
            "hikari_discord_invite": "https://discord.gg/Jx4cNGG",
            "hikari_source_url": "https://nekokatt.github.io/hikari",
            "python_implementation": "CPython",
            "python_version": "4.0.0",
            "system_description": "Machine Potato 1.0.0",
        }

        args.update(extra_args)

        read_banner.assert_called_once_with("hikaru")
        template.assert_called_once_with(read_banner.return_value)
        safe_substitute = template.return_value.safe_substitute
        safe_substitute.assert_called_once_with(args)
        stdout.buffer.write.assert_called_once_with(safe_substitute.return_value.encode.return_value)
        stdout.flush.assert_called_once_with()

    def test_overwrite_args_raises_error(self, mock_args):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(time, "sleep"))
        stack.enter_context(mock.patch.object(colorlog.escape_codes, "escape_codes", new={}))
        stack.enter_context(mock.patch.object(ux, "_read_banner"))
        stack.enter_context(mock.patch.object(string, "Template"))
        stack.enter_context(mock.patch.object(sys.stdout, "write"))
        stack.enter_context(mock.patch.object(os.path, "abspath", return_value="some path"))

        extra_args = {"hikari_version": "overwrite"}

        with stack:
            with pytest.raises(
                ValueError, match=r"Cannot overwrite \$-substitution `hikari_version`. Please use a different key."
            ):
                ux.print_banner("hikari", True, False, extra_args=extra_args)


class TestWarnIfNotOptimized:
    @pytest.mark.skipif(not __debug__, reason="Not running in optimized mode")
    def test_when_not_optimized(self):
        with mock.patch.object(ux, "_LOGGER") as logger:
            ux.warn_if_not_optimized(suppress=False)

        logger.warning.assert_called()

    @pytest.mark.skipif(__debug__, reason="Running in optimized mode")
    def test_when_optimized(self):
        with mock.patch.object(ux, "_LOGGER") as logger:
            ux.warn_if_not_optimized(suppress=False)

        logger.warning.assert_not_called()

    @pytest.mark.skipif(not __debug__, reason="Not running in optimized mode")
    def test_when_optimized_and_suppressed(self):
        with mock.patch.object(ux, "_LOGGER") as logger:
            ux.warn_if_not_optimized(suppress=True)

        logger.warning.assert_not_called()


class TestSupportsColor:
    def test_when_not_allow_color(self):
        assert ux.supports_color(False, True) is False

    def test_when_CLICOLOR_FORCE_in_env(self):
        with mock.patch.dict(os.environ, {"CLICOLOR_FORCE": "1"}, clear=True):
            assert ux.supports_color(True, False) is True

    def test_when_force_color(self):
        with mock.patch.dict(os.environ, {"CLICOLOR_FORCE": "0"}, clear=True):
            assert ux.supports_color(True, True) is True

    def test_when_CLICOLOR_and_is_a_tty(self):
        with mock.patch.object(sys.stdout, "isatty", return_value=True):
            with mock.patch.dict(os.environ, {"CLICOLOR_FORCE": "0", "CLICOLOR": "1"}, clear=True):
                assert ux.supports_color(True, False) is True

    def test_when_CLICOLOR_is_0(self):
        with mock.patch.object(sys.stdout, "isatty", return_value=True):
            with mock.patch.dict(os.environ, {"CLICOLOR_FORCE": "0", "CLICOLOR": "0"}, clear=True):
                assert ux.supports_color(True, False) is False

    @pytest.mark.parametrize("colorterm", ["truecolor", "24bit", "TRUECOLOR", "24BIT"])
    def test_when_COLORTERM_has_correct_value(self, colorterm):
        with mock.patch.dict(os.environ, {"COLORTERM": colorterm}, clear=True):
            assert ux.supports_color(True, False) is True

    def test_when_plat_is_Pocket_PC(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.dict(os.environ, {}, clear=True))
        stack.enter_context(mock.patch.object(sys, "platform", new="Pocket PC"))

        with stack:
            assert ux.supports_color(True, False) is False

    @pytest.mark.parametrize(
        ("term_program", "ansicon", "isatty", "expected"),
        [
            ("mintty", False, True, True),
            ("Terminus", False, True, True),
            ("some other", True, True, True),
            ("some other", False, True, False),
            ("some other", False, False, False),
            ("mintty", True, False, False),
            ("Terminus", True, False, False),
        ],
    )
    def test_when_plat_is_win32(self, term_program, ansicon, isatty, expected):
        environ = {"TERM_PROGRAM": term_program}
        if ansicon:
            environ["ANSICON"] = "ooga booga"

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.dict(os.environ, environ, clear=True))
        stack.enter_context(mock.patch.object(sys.stdout, "isatty", return_value=isatty))
        stack.enter_context(mock.patch.object(sys, "platform", new="win32"))

        with stack:
            assert ux.supports_color(True, False) is expected

    @pytest.mark.parametrize("isatty", [True, False])
    def test_when_plat_is_not_win32(self, isatty):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.dict(os.environ, {}, clear=True))
        stack.enter_context(mock.patch.object(sys.stdout, "isatty", return_value=isatty))
        stack.enter_context(mock.patch.object(sys, "platform", new="linux"))

        with stack:
            assert ux.supports_color(True, False) is isatty

    @pytest.mark.parametrize("isatty", [True, False])
    @pytest.mark.parametrize("plat", ["linux", "win32"])
    def test_when_PYCHARM_HOSTED(self, isatty, plat):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.dict(os.environ, {"PYCHARM_HOSTED": "OOGA BOOGA"}, clear=True))
        stack.enter_context(mock.patch.object(sys.stdout, "isatty", return_value=isatty))
        stack.enter_context(mock.patch.object(sys, "platform", new=plat))

        with stack:
            assert ux.supports_color(True, False) is True

    @pytest.mark.parametrize("isatty", [True, False])
    @pytest.mark.parametrize("plat", ["linux", "win32"])
    def test_when_WT_SESSION(self, isatty, plat):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.dict(os.environ, {"WT_SESSION": "OOGA BOOGA"}, clear=True))
        stack.enter_context(mock.patch.object(sys.stdout, "isatty", return_value=isatty))
        stack.enter_context(mock.patch.object(sys, "platform", new=plat))

        with stack:
            assert ux.supports_color(True, False) is True


class TestHikariVersion:
    @pytest.mark.parametrize("v", ["1", "1.0.0dev2"])
    def test_init_when_version_number_is_invalid(self, v):
        with pytest.raises(ValueError, match=rf"Invalid version: '{v}'"):
            ux.HikariVersion(v)

    def test_init_when_prerelease(self):
        assert ux.HikariVersion("1.2.3.dev99").prerelease == (".dev", 99)

    def test_init_when_no_prerelease(self):
        assert ux.HikariVersion("1.2.3").prerelease is None

    def test_str_when_prerelease(self):
        assert str(ux.HikariVersion("1.2.3.dev99")) == "1.2.3.dev99"

    def test_str_when_no_prerelease(self):
        assert str(ux.HikariVersion("1.2.3")) == "1.2.3"

    def test_repr(self):
        assert repr(ux.HikariVersion("1.2.3.dev99")) == "HikariVersion('1.2.3.dev99')"

    @pytest.mark.parametrize(
        ("other", "result"),
        [
            (ux.HikariVersion("1.2.3.dev99"), True),
            (ux.HikariVersion("42.212.4.dev99"), False),
            (ux.HikariVersion("1.2.3.dev98"), False),
            (ux.HikariVersion("1.2.3"), False),
        ],
    )
    def test_eq(self, other, result):
        assert (ux.HikariVersion("1.2.3.dev99") == other) is result

    @pytest.mark.parametrize(
        ("other", "result"),
        [
            (ux.HikariVersion("1.2.3.dev99"), False),
            (ux.HikariVersion("42.212.4.dev99"), True),
            (ux.HikariVersion("1.2.3.dev98"), True),
            (ux.HikariVersion("1.2.3"), True),
        ],
    )
    def test_ne(self, other, result):
        assert (ux.HikariVersion("1.2.3.dev99") != other) is result

    @pytest.mark.parametrize(
        ("other", "result"),
        [
            (ux.HikariVersion("1.2.3.dev99"), False),
            (ux.HikariVersion("42.212.4.dev99"), True),
            (ux.HikariVersion("1.2.3.dev98"), False),
            (ux.HikariVersion("1.2.3"), True),
        ],
    )
    def test_lt(self, other, result):
        assert (ux.HikariVersion("1.2.3.dev99") < other) is result

    @pytest.mark.parametrize(
        ("other", "result"),
        [
            (ux.HikariVersion("1.2.3.dev99"), True),
            (ux.HikariVersion("42.212.4.dev99"), True),
            (ux.HikariVersion("1.2.3.dev98"), False),
            (ux.HikariVersion("1.2.3"), True),
        ],
    )
    def test_le(self, other, result):
        assert (ux.HikariVersion("1.2.3.dev99") <= other) is result

    @pytest.mark.parametrize(
        ("other", "result"),
        [
            (ux.HikariVersion("1.2.3.dev99"), False),
            (ux.HikariVersion("42.212.4.dev99"), False),
            (ux.HikariVersion("1.2.3.dev98"), True),
            (ux.HikariVersion("1.2.3"), False),
        ],
    )
    def test_ge(self, other, result):
        assert (ux.HikariVersion("1.2.3.dev99") > other) is result

    @pytest.mark.parametrize(
        ("other", "result"),
        [
            (ux.HikariVersion("1.2.3.dev99"), True),
            (ux.HikariVersion("42.212.4.dev99"), False),
            (ux.HikariVersion("1.2.3.dev98"), True),
            (ux.HikariVersion("1.2.3"), False),
        ],
    )
    def test_gt(self, other, result):
        assert (ux.HikariVersion("1.2.3.dev99") >= other) is result


@pytest.mark.asyncio
class TestCheckForUpdates:
    @pytest.fixture
    def http_settings(self):
        return mock.Mock(spec_set=config.HTTPSettings)

    @pytest.fixture
    def proxy_settings(self):
        return mock.Mock(spec_set=config.ProxySettings)

    async def test_when_not_official_pypi_release(self, http_settings, proxy_settings):
        stack = contextlib.ExitStack()
        logger = stack.enter_context(mock.patch.object(ux, "_LOGGER"))
        create_client_session = stack.enter_context(mock.patch.object(net, "create_client_session"))
        stack.enter_context(mock.patch.object(_about, "__git_sha1__", new="HEAD"))

        with stack:
            await ux.check_for_updates(http_settings=http_settings, proxy_settings=proxy_settings)

        logger.warning.assert_not_called()
        logger.info.assert_not_called()
        create_client_session.assert_not_called()

    async def test_when_error_fetching(self, http_settings, proxy_settings):
        ex = RuntimeError("testing")
        stack = contextlib.ExitStack()
        logger = stack.enter_context(mock.patch.object(ux, "_LOGGER"))
        stack.enter_context(mock.patch.object(_about, "__git_sha1__", new="1234567890"))
        create_client_session = stack.enter_context(mock.patch.object(net, "create_client_session", side_effect=ex))
        create_tcp_connector = stack.enter_context(mock.patch.object(net, "create_tcp_connector"))

        with stack:
            await ux.check_for_updates(http_settings=http_settings, proxy_settings=proxy_settings)

        logger.warning.assert_called_once_with("Failed to fetch hikari version details", exc_info=ex)
        create_tcp_connector.assert_called_once_with(dns_cache=False, limit=1, http_settings=http_settings)
        create_client_session.assert_called_once_with(
            connector=create_tcp_connector(),
            connector_owner=True,
            http_settings=http_settings,
            raise_for_status=True,
            trust_env=proxy_settings.trust_env,
        )

    async def test_when_no_new_available_releases(self, http_settings, proxy_settings):
        data = {
            "releases": {
                "0.1.0": [{"yanked": False}],
                "1.0.0": [{"yanked": False}],
                "1.0.0.dev1": [{"yanked": False}],
                "1.0.1": [{"yanked": True}],
            }
        }
        _request = hikari_test_helpers.AsyncContextManagerMock()
        _request.read = mock.AsyncMock(return_value=data)
        _client_session = hikari_test_helpers.AsyncContextManagerMock()
        _client_session.get = mock.Mock(return_value=_request)
        stack = contextlib.ExitStack()
        logger = stack.enter_context(mock.patch.object(ux, "_LOGGER"))
        json_loads = stack.enter_context(mock.patch.object(data_binding, "default_json_loads", return_value=data))
        create_client_session = stack.enter_context(
            mock.patch.object(net, "create_client_session", return_value=_client_session)
        )
        create_tcp_connector = stack.enter_context(mock.patch.object(net, "create_tcp_connector"))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.0"))
        stack.enter_context(mock.patch.object(_about, "__git_sha1__", new="1234567890"))

        with stack:
            await ux.check_for_updates(http_settings=http_settings, proxy_settings=proxy_settings)

        logger.warning.assert_not_called()
        logger.info.assert_not_called()

        json_loads.assert_called_once_with(_request.read.return_value)
        create_tcp_connector.assert_called_once_with(dns_cache=False, limit=1, http_settings=http_settings)
        create_client_session.assert_called_once_with(
            connector=create_tcp_connector(),
            connector_owner=True,
            http_settings=http_settings,
            raise_for_status=True,
            trust_env=proxy_settings.trust_env,
        )
        _client_session.get.assert_called_once_with(
            "https://pypi.org/pypi/hikari/json",
            allow_redirects=http_settings.max_redirects is not None,
            max_redirects=http_settings.max_redirects,
            proxy=proxy_settings.url,
            proxy_headers=proxy_settings.all_headers,
        )

    @pytest.mark.parametrize("v", ["1.0.1", "1.0.1.dev10"])
    async def test_check_for_updates(self, v, http_settings, proxy_settings):
        data = {
            "releases": {
                v: [{"yanked": False}, {"yanked": True}],
                "1.0.0": [{"yanked": False}],
                "1.0.0.dev1": [{"yanked": False}],
                "0.1.0": [{"yanked": False}],
                "1.0.2": [{"yanked": True}],
            }
        }
        _request = hikari_test_helpers.AsyncContextManagerMock()
        _request.read = mock.AsyncMock()
        _client_session = hikari_test_helpers.AsyncContextManagerMock()
        _client_session.get = mock.Mock(return_value=_request)
        stack = contextlib.ExitStack()
        logger = stack.enter_context(mock.patch.object(ux, "_LOGGER"))
        json_loads = stack.enter_context(mock.patch.object(data_binding, "default_json_loads", return_value=data))
        create_client_session = stack.enter_context(
            mock.patch.object(net, "create_client_session", return_value=_client_session)
        )
        create_tcp_connector = stack.enter_context(mock.patch.object(net, "create_tcp_connector"))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.0.dev1"))
        stack.enter_context(mock.patch.object(_about, "__git_sha1__", new="1234567890"))

        with stack:
            await ux.check_for_updates(http_settings=http_settings, proxy_settings=proxy_settings)

        logger.warning.assert_not_called()
        logger.info.assert_called_once_with(
            "A newer version of hikari is available, consider upgrading to %s", ux.HikariVersion(v)
        )
        json_loads.assert_called_once_with(_request.read.return_value)
        create_tcp_connector.assert_called_once_with(dns_cache=False, limit=1, http_settings=http_settings)
        create_client_session.assert_called_once_with(
            connector=create_tcp_connector(),
            connector_owner=True,
            http_settings=http_settings,
            raise_for_status=True,
            trust_env=proxy_settings.trust_env,
        )
        _client_session.get.assert_called_once_with(
            "https://pypi.org/pypi/hikari/json",
            allow_redirects=http_settings.max_redirects is not None,
            max_redirects=http_settings.max_redirects,
            proxy=proxy_settings.url,
            proxy_headers=proxy_settings.all_headers,
        )
