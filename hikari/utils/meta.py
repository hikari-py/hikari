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
"""
Metadata. Contains interpreter introspection utilities, Hikari introspection utilities (e.g. version, author, etc)
and documentation decorators used within this library. There is usually zero need for you to touch anything in this
package.
"""
__all__ = ("APIResource", "link_developer_portal", "library_version", "python_version", "system_type", "user_agent")

import enum
import inspect
import platform


class APIResource(enum.Enum):
    """A documentation resource for the underlying API."""

    AUDIT_LOG = "/resources/audit-log"
    CHANNEL = "/resources/channel"
    EMOJI = "/resources/emoji"
    GUILD = "/resources/guild"
    INVITE = "/resources/invite"
    OAUTH2 = "/topics/oauth2"
    USER = "/resources/user"
    VOICE = "/resources/voice"
    WEBHOOK = "/resources/webhook"
    GATEWAY = "/topics/gateway"


def link_developer_portal(scope: APIResource, specific_resource: str = None):
    """Injects some common documentation into the given member's docstring."""

    def decorator(obj):
        base_url = "https://discordapp.com/developers/docs"
        doc = inspect.cleandoc(inspect.getdoc(obj) or "")
        base_resource = base_url + scope.value
        frag = obj.__name__.lower().replace("_", "-") if specific_resource is None else specific_resource
        uri = base_resource + "#" + frag

        setattr(obj, "__doc__", f"Read the documentation on `Discord's developer portal <{uri}>`_.\n\n{doc}")
        return obj

    return decorator


def library_version() -> str:
    """
    Creates a string that is representative of the version of this library.

    Example:
        hikari 0.0.1a1
    """
    from hikari import __version__

    return f"hikari v{__version__}"


def python_version() -> str:
    """
    Creates a comprehensive string representative of this version of Python, along with the compiler used, if present.

    Examples:
        CPython3.7:
            CPython 3.7.3 GCC 8.2.1 20181127
        PyPy3.6:
            PyPy 3.6.1 release-pypy3.6-v7.1.1
    """
    attrs = [
        platform.python_implementation(),
        platform.python_version(),
        platform.python_branch(),
        platform.python_compiler(),
    ]
    return " ".join(a for a in attrs if a.strip())


def system_type() -> str:
    """
    Get a string representing the system type.
    """
    # Might change this eventually to be more detailed, who knows.
    return platform.system()


def user_agent() -> str:
    """
    Creates a User-Agent header string acceptable by the API.

    Examples:
        CPython3.7:
            DiscordBot (https://gitlab.com/nekokatt/hikari, 0.0.1a) CPython 3.7.3 GCC 8.2.1 20181127 Linux
        PyPy3.6:
            DiscordBot (https://gitlab.com/nekokatt/hikari, 0.0.1a) PyPy 3.6.1 release-pypy3.6-v7.1.1 Linux
    """
    from hikari import __version__, __url__

    system = system_type()
    python = python_version()
    return f"DiscordBot ({__url__}, {__version__}) {python} {system}"
