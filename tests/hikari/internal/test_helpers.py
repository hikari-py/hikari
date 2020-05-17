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
import pytest

from hikari.models import guilds, users
from hikari.internal import helpers
from tests.hikari import _helpers


@pytest.mark.parametrize(
    ("kwargs", "expected_result"),
    [
        (
            {"mentions_everyone": True, "user_mentions": True, "role_mentions": True},
            {"parse": ["everyone", "users", "roles"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": False, "role_mentions": False},
            {"parse": [], "users": [], "roles": []},
        ),
        (
            {"mentions_everyone": True, "user_mentions": ["1123123"], "role_mentions": True},
            {"parse": ["everyone", "roles"], "users": ["1123123"]},
        ),
        (
            {"mentions_everyone": True, "user_mentions": True, "role_mentions": ["1231123"]},
            {"parse": ["everyone", "users"], "roles": ["1231123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": ["1123123"], "role_mentions": True},
            {"parse": ["roles"], "users": ["1123123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": True, "role_mentions": ["1231123"]},
            {"parse": ["users"], "roles": ["1231123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": ["1123123"], "role_mentions": False},
            {"parse": [], "roles": [], "users": ["1123123"]},
        ),
        (
            {"mentions_everyone": False, "user_mentions": False, "role_mentions": ["1231123"]},
            {"parse": [], "roles": ["1231123"], "users": []},
        ),
        (
            {"mentions_everyone": False, "user_mentions": ["22222"], "role_mentions": ["1231123"]},
            {"parse": [], "users": ["22222"], "roles": ["1231123"]},
        ),
        (
            {"mentions_everyone": True, "user_mentions": ["22222"], "role_mentions": ["1231123"]},
            {"parse": ["everyone"], "users": ["22222"], "roles": ["1231123"]},
        ),
    ],
)
def test_generate_allowed_mentions(kwargs, expected_result):
    assert helpers.generate_allowed_mentions(**kwargs) == expected_result


@_helpers.parametrize_valid_id_formats_for_models("role", 3, guilds.GuildRole)
def test_generate_allowed_mentions_removes_duplicate_role_ids(role):
    result = helpers.generate_allowed_mentions(
        role_mentions=["1", "2", "1", "3", "5", "7", "2", role], user_mentions=True, mentions_everyone=True
    )
    assert result == {"roles": ["1", "2", "3", "5", "7"], "parse": ["everyone", "users"]}


@_helpers.parametrize_valid_id_formats_for_models("user", 3, users.User)
def test_generate_allowed_mentions_removes_duplicate_user_ids(user):
    result = helpers.generate_allowed_mentions(
        role_mentions=True, user_mentions=["1", "2", "1", "3", "5", "7", "2", user], mentions_everyone=True
    )
    assert result == {"users": ["1", "2", "3", "5", "7"], "parse": ["everyone", "roles"]}


@_helpers.parametrize_valid_id_formats_for_models("role", 190007233919057920, guilds.GuildRole)
def test_generate_allowed_mentions_handles_all_role_formats(role):
    result = helpers.generate_allowed_mentions(role_mentions=[role], user_mentions=True, mentions_everyone=True)
    assert result == {"roles": ["190007233919057920"], "parse": ["everyone", "users"]}


@_helpers.parametrize_valid_id_formats_for_models("user", 190007233919057920, users.User)
def test_generate_allowed_mentions_handles_all_user_formats(user):
    result = helpers.generate_allowed_mentions(role_mentions=True, user_mentions=[user], mentions_everyone=True)
    assert result == {"users": ["190007233919057920"], "parse": ["everyone", "roles"]}


@_helpers.assert_raises(type_=ValueError)
def test_generate_allowed_mentions_raises_error_on_too_many_roles():
    helpers.generate_allowed_mentions(user_mentions=False, role_mentions=list(range(101)), mentions_everyone=False)


@_helpers.assert_raises(type_=ValueError)
def test_generate_allowed_mentions_raises_error_on_too_many_users():
    helpers.generate_allowed_mentions(user_mentions=list(range(101)), role_mentions=False, mentions_everyone=False)
