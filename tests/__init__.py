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
import warnings

# Python 3.8 is much more vocal about deprecation warnings; it also deprecates @asyncio.coroutine
# which a lot of stuff still relies on, so I get spammed with warnings that I have little
# control over. This shuts some of those up.
for old_module in ["asynctest", "asynctest.mock", "aiofiles.base"]:
    print("Suppressing deprecation warnings in", old_module)
    warnings.filterwarnings("ignore", category=DeprecationWarning, module=old_module)
