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

FROM        python:3.9-rc
COPY        . /hikari
WORKDIR     /hikari
RUN         pip install poetry https://github.com/html5lib/html5lib-python/zipball/af19281fa28788830684b4c8fc6d0c588b092616 -q
RUN         poetry update
ENTRYPOINT  ["poetry", "run", "nox"]
CMD         []
