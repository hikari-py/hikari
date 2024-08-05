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
"""Generate the version for the release depending on the date and past releases."""
import datetime
import os
import sys

sys.path.append(os.getcwd())

from hikari import __version__ as previous_version_str
from hikari.internal import ux

is_prerelease = sys.argv[1].lower() in {"true", "1", "y"}

current_date = datetime.date.today()
new_mayor = int(str(current_date.year)[-2:])
new_minor = current_date.month

previous_version = ux.HikariVersion(previous_version_str)
if previous_version.major == new_mayor and previous_version.minor == new_minor:
    # There has already been a release with this combination

    if is_prerelease:
        # We will be releasing with the same modifier as the current
        # version in the master branch in git, so no changes needed
        #
        # __version__ will always contain the 'dev' prerelease modifier
        assert previous_version.prerelease
        version = previous_version

    else:
        # We need to increment the micro version
        version = ux.HikariVersion(f"{new_mayor}.{new_minor}.{previous_version.micro + 1}")

else:
    # We don't have any collisions, so we have the version
    vstring = f"{new_mayor}.{new_minor}.0"

    # Add the prerelease indicator, if needed
    if is_prerelease:
        vstring += ".dev0"

    version = ux.HikariVersion(vstring)

print(version)
