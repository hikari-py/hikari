#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
import inspect
import re

from hikari.internal_utilities import logging_helpers
from tests.hikari import _helpers

package_name = __name__


class Dummy:
    class NestedDummy:
        pass


def test_get_named_logger_with_no_arguments():
    logger = logging_helpers.get_named_logger()

    assert logger.name == package_name


def test_get_named_logger_with_no_arguments_but_module_is_not_available():
    with _helpers.mock_patch(inspect.getmodule, return_value=None):
        logger = logging_helpers.get_named_logger()

    assert re.match(r"^[0-9a-z]{8}-(?:[0-9a-z]{4}-){3}[0-9a-z]{12}$", logger.name, re.I)


def test_get_named_logger_with_global_class():
    logger = logging_helpers.get_named_logger(Dummy)
    assert logger.name == package_name + ".Dummy"


def test_get_named_logger_with_nested_class():
    logger = logging_helpers.get_named_logger(Dummy.NestedDummy)
    assert logger.name == package_name + ".Dummy.NestedDummy"


def test_get_named_logger_with_global_class_instance():
    logger = logging_helpers.get_named_logger(Dummy())
    assert logger.name == package_name + ".Dummy"


def test_get_named_logger_with_nested_class_instance():
    logger = logging_helpers.get_named_logger(Dummy.NestedDummy())
    assert logger.name == package_name + ".Dummy.NestedDummy"


def test_get_named_logger_with_string():
    logger = logging_helpers.get_named_logger("potato")
    assert logger.name == "potato"


def test_get_named_logger_with_extras():
    logger = logging_helpers.get_named_logger("potato", "foo", "bar", "baz")
    assert logger.name == "potato[foo, bar, baz]"
