<!--
Copyright (c) 2020 Nekokatt

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-->

<%!
    from distutils import version as _version

    import hikari as _hikari

    show_inherited_members = True
    extract_module_toc_into_sidebar = True
    list_class_variables_in_index = True
    sort_identifiers = True
    show_type_annotations = True

    show_source_code = True

    git_link_template = "https://github.com/nekokatt/hikari/blob/{commit}/{path}#L{start_line}-L{end_line}"

    link_prefix = ""

    hljs_style = "atom-one-dark"

    lunr_search = {"fuzziness": 0}


    site_accent = "#ff029a"
    site_logo = "https://nekokatt.github.io/hikari/logo.png"
    site_description = "A Discord Bot framework for modern Python and asyncio built on good intentions"

    # Versions of stuff
    mathjax_version = "2.7.5"
    bootstrap_version = "4.5.0"
    highlightjs_version = "9.12.0"
    jquery_version = "3.5.1"
    popperjs_version = "1.16.0"

    root_url = "https://github.com/nekokatt/hikari"
%>
