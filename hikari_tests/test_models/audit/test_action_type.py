#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from hikari.models.audit import action_type


def test_get_category():
    assert action_type.ActionType.MEMBER_KICK.category == action_type.ActionTypeCategory.MEMBER


def test_get_events():
    member_events = {e for e in action_type.ActionType if e.name.startswith("MEMBER_")}
    actual = action_type.ActionTypeCategory.MEMBER.events
    assert member_events == actual
