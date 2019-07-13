#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import json as libjson
import os


def json(file):
    def reader():
        this_file = __file__
        this_directory = os.path.abspath(os.path.dirname(this_file))
        file_path = os.path.join(this_directory, file) + ".json"

        with open(file_path) as fp:
            return libjson.load(fp)

    return reader


def with_test_data(reader):
    # noinspection PyProtectedMember
    def decorator(function):
        def wrapper(*args, **kwargs):
            test_data = reader()
            return function(*args, **kwargs, test_data=test_data)

        # We have to remove the `test_data` argument from the signature or pytest tries to resolve it as a fixture
        # incorrectly and everything dies...
        signature = inspect.signature(function)
        signature._parameters = dict(signature._parameters)
        del signature._parameters["test_data"]

        wrapper.__signature__ = signature
        wrapper.__name__ = function.__name__
        wrapper.__qualname__ = function.__qualname__
        return wrapper

    return decorator
