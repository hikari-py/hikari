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
"""Wrapper around nox to give default job kwargs."""
import functools
import os
from typing import Callable

from nox.sessions import Session
from nox import session as _session
from nox import options as _options


_options.sessions = []


def session(*, only_if=lambda: True, default: bool = False, reuse_venv: bool = False, **kwargs):
    def decorator(func: Callable[[Session], None]):
        func.__name__ = func.__name__.replace("_", "-")
        if default:
            _options.sessions.append(func.__name__)

        return _session(reuse_venv=reuse_venv, **kwargs)(func) if only_if() else func
    return decorator


def inherit_environment_vars(func):
    @functools.wraps(func)
    def logic(session):
        for n, v in os.environ.items():
            session.env[n] = v
        return func(session)
    return logic
