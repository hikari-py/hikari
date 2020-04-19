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
    # Template configuration. Copy over in your template directory
    # (used with `--template-dir`) and adapt as necessary.
    # Note, defaults are loaded from this distribution file, so your
    # config.mako only needs to contain values you want overridden.
    # You can also run pdoc with `--config KEY=VALUE` to override
    # individual values.
    html_lang = 'en'
    show_inherited_members = True
    extract_module_toc_into_sidebar = True
    list_class_variables_in_index = True
    sort_identifiers = True
    show_type_annotations = True
    # Show collapsed source code block next to each item.
    # Disabling this can improve rendering speed of large modules.
    show_source_code = True
    # If set, format links to objects in online source code repository
    # according to this template. Supported keywords for interpolation
    # are: commit, path, start_line, end_line.
    git_link_template = 'https://gitlab.com/nekokatt/hikari/blob/{commit}/{path}#L{start_line}-L{end_line}'
    # A prefix to use for every HTML hyperlink in the generated documentation.
    # No prefix results in all links being relative.
    link_prefix = ''
    # Enable syntax highlighting for code/source blocks by including Highlight.js
    syntax_highlighting = True
    # Set the style keyword such as 'atom-one-light' or 'github-gist'
    #     Options: https://github.com/highlightjs/highlight.js/tree/master/src/styles
    #     Demo: https://highlightjs.org/static/demo/
    hljs_style = 'rainbow'
    # If set, insert Google Analytics tracking code. Value is GA
    # tracking id (UA-XXXXXX-Y).
    google_analytics = ''
    # If set, insert Google Custom Search search bar widget above the sidebar index.
    # The whitespace-separated tokens represent arbitrary extra queries (at least one
    # must match) passed to regular Google search. Example:
    #search_query = 'inurl:github.com/USER/PROJECT  site:PROJECT.github.io  site:PROJECT.website'
    search_query = "inurl:github.com/nekokatt/hikari  site:nekokatt.gitlab.io/hikari"
    # If set, render LaTeX math syntax within \(...\) (inline equations),
    # or within \[...\] or $$...$$ or `.. math::` (block equations)
    # as nicely-formatted math formulas using MathJax.
    # Note: in Python docstrings, either all backslashes need to be escaped (\\)
    # or you need to use raw r-strings.
    latex_math = True
%>
