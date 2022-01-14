# -*- coding: utf-8 -*-
# cython: language_level=3
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

import json
import os.path as path
import re

import pdoc
from pdoc import cli


def _patched_generate_lunr_search(modules, index_docstrings, template_config):
    # This will only be called once due to how we generate the documentation, so we can ignore the rest
    assert len(modules) == 1, "expected only 1 module to be generated, got more"
    top_module = modules[0]

    def trim_docstring(docstring):
        return re.sub(
            r"""
            \s+[-=~]{3,}\s+|       # title underlines
            ^[ \t]*[`~]{3,}\w*$|   # code blocks
            \s*[`#*]+\s*|          # common markdown chars
            \s*([^\w\d_>])\1\s*|   # sequences of punct of the same kind
            \s*</?\w*[^>]*>\s*     # simple HTML tags
            \s+                    # whitespace sequences
        """,
            " ",
            docstring,
            flags=re.VERBOSE | re.MULTILINE,
        )

    def recursive_add_to_index(dobj):
        if dobj.module.name != "hikari":  # Do not index root
            url = to_url_id(dobj)
            # r: ref
            # u: url
            # d: docstring
            # f: function
            info = {"r": dobj.refname, "u": url}
            if index_docstrings:
                info["d"] = trim_docstring(dobj.docstring)
            if isinstance(dobj, pdoc.Function):
                info["f"] = 1

            index.append(info)

        for member_dobj in getattr(dobj, "doc", {}).values():
            if dobj.module.name == "hikari" and not isinstance(member_dobj, pdoc.Module):
                continue

            recursive_add_to_index(member_dobj)

    def to_url_id(dobj):
        # pdocs' .url() doesn't take in account that some attributes are inherited,
        # which generates an invalid url. Because of this, we need to take matter
        # into our own hands.
        url = dobj.refname.replace(".", "/")
        if not isinstance(dobj, pdoc.Module):
            depth = 1
            obj = getattr(dobj, "cls", None)
            while obj:
                depth += 1
                obj = getattr(obj, "cls", None)

            url = "/".join(url.split("/")[:-depth])

        if top_module.is_package:  # Reference from subfolder if its a package
            _, url = url.split("/", maxsplit=1)
        if url not in url_cache:
            url_cache[url] = len(url_cache)
        return url_cache[url]

    index = []
    url_cache = {}
    recursive_add_to_index(top_module)
    urls = sorted(url_cache.keys(), key=url_cache.__getitem__)

    # If top module is a package, output the index in its subfolder, else, in the output dir
    main_path = path.join(cli.args.output_dir, *top_module.name.split(".") if top_module.is_package else "")
    with cli._open_write_file(path.join(main_path, "index.json")) as f:
        json.dump({"urls": urls, "index": index}, f)

    # Generate search.html
    with cli._open_write_file(path.join(main_path, "search.html")) as f:
        rendered_template = pdoc._render_template("/search.mako", module=top_module, **template_config)
        f.write(rendered_template)


if __name__ == "__main__":
    cli._generate_lunr_search = _patched_generate_lunr_search

    cli.main()
