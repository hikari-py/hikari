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
    from distutils import version as _version

    import hikari as _hikari

    show_inherited_members = True
    extract_module_toc_into_sidebar = True
    list_class_variables_in_index = True
    sort_identifiers = True
    show_type_annotations = True

    show_source_code = True

    git_link_template = "https://gitlab.com/nekokatt/hikari/blob/{commit}/{path}#L{start_line}-L{end_line}"

    link_prefix = ""

    hljs_style = "atom-one-light"

    if "dev" in _version.LooseVersion(_hikari.__version__).version:
        search_query = "inurl:github.com/nekokatt/hikari  site:nekokatt.gitlab.io/hikari/hikari"
    else:  # TODO: "hikari/staging/hikari" temporarily changed to "hikari/hikari" for staging site search link.
        search_query = "inurl:github.com/nekokatt/hikari  site:nekokatt.gitlab.io/hikari/hikari"

    site_accent = "#ff029a"
    site_logo = "https://assets.gitlab-static.net/uploads/-/system/project/avatar/12050696/Hikari-Logo_1.png"
    site_description = "A Discord Bot framework for modern Python and asyncio built on good intentions"

    # Versions of stuff
    mathjax_version = "2.7.5"
    bootstrap_version = "4.5.0"
    highlightjs_version = "9.12.0"
    jquery_version = "3.5.1"
    popperjs_version = "1.16.0"

    root_url = "https://gitlab.com/nekokatt/hikari"
%>
