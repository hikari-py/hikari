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
"""Defines a base interface for application components to derive from."""

from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari import app as app_


class IComponent(abc.ABC):
    """A component that makes up part of the application."""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def app(self) -> app_.IApp:
        """Application that owns this component."""
