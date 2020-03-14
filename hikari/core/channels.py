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
import attr

from hikari.core import entities


@attr.s(slots=True)
class Channel(entities.UniqueEntity):
    ...


@attr.s(slots=False)
class TextChannel(Channel):
    ...


@attr.s(slots=False)
class DMChannel(Channel):
    ...


@attr.s(slots=False)
class GroupDMChannel(DMChannel):
    ...


@attr.s(slots=False)
class GuildChannel(Channel):
    ...


@attr.s(slots=False)
class GuildTextChannel(GuildChannel, TextChannel):
    ...


@attr.s(slots=False)
class GuildVoiceChannel(GuildChannel):
    ...


@attr.s(slots=False)
class GuildCategory(GuildChannel):
    ...


@attr.s(slots=False)
class GuildStoreChannel(GuildChannel):
    ...


@attr.s(slots=False)
class GuildNewsChannel(GuildChannel, TextChannel):
    ...
