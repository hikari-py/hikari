## Copyright © Nekokatt 2019-2020
##
## This file is part of Hikari.
##
## Hikari is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Hikari is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Hikari. If not, see <https://www.gnu.org/licenses/>.
<%!
    from distutils import version

    import hikari

    version = "staging" if "dev" in version.LooseVersion(hikari.__version__).version else "production"
%>

<header>
    <a class="homelink" rel="home" title="Hikari Home" href="https://nekokatt.gitlab.io/hikari/">
        <img src="https://assets.gitlab-static.net/uploads/-/system/project/avatar/12050696/Hikari-Logo_1.png" alt="">
        Hikari
    </a>
    <p class="homelink-footer">This is for version ${hikari.__version__}, a ${version} release.</p>
    % if version == "production":
        <p class="homelink-footer">
            For staging please visit
            <a href="https://nekokatt.gitlab.io/hikari/staging">this page</a>.
        </p>
    % endif
    <ul class="links">
        <li><a href="http://gitlab.com/nekokatt/hikari">Source</a></li>
        <li><a href="http://gitlab.com/nekokatt/hikari/pipelines">Builds</a></li>
        <li><a href="https://discordapp.com/invite/HMnGbsv">Discord Server</a></li>
    </ul>
</header>
