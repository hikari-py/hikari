# -*- coding: utf-8 -*-
def main():
    import json
    import os.path as path
    import re
    from functools import lru_cache

    import pdoc
    from pdoc import cli

    # We don't document stuff on the index of the documentation, but pdoc doesn't know that,
    # so we have to patch the function that generates the index.
    def _patched_generate_lunr_search(top_module, index_docstrings, template_config):
        def trim_docstring(docstring):
            return re.sub(
                r"""
                \s+|                   # whitespace sequences
                \s+[-=~]{3,}\s+|       # title underlines
                ^[ \t]*[`~]{3,}\w*$|   # code blocks
                \s*[`#*]+\s*|          # common markdown chars
                \s*([^\w\d_>])\1\s*|   # sequences of punct of the same kind
                \s*</?\w*[^>]*>\s*     # simple HTML tags
            """,
                " ",
                docstring,
                flags=re.VERBOSE | re.MULTILINE,
            )

        def recursive_add_to_index(dobj):
            url = to_url_id(dobj.module)
            if url != 0:  # 0 is index.html
                info = {
                    "ref": dobj.refname,
                    "url": url,
                }
                if index_docstrings:
                    info["doc"] = trim_docstring(dobj.docstring)
                if isinstance(dobj, pdoc.Function):
                    info["func"] = 1

                index.append(info)

            for member_dobj in getattr(dobj, "doc", {}).values():
                recursive_add_to_index(member_dobj)

        @lru_cache()
        def to_url_id(module):
            url = module.url()
            if top_module.is_package:  # Reference from subfolder if its a package
                _, url = url.split("/", maxsplit=1)
            if url not in url_cache:
                url_cache[url] = len(url_cache)
            return url_cache[url]

        index = []
        url_cache = {}
        recursive_add_to_index(top_module)
        urls = [i[0] for i in sorted(url_cache.items(), key=lambda i: i[1])]

        # If top module is a package, output the index in its subfolder, else, in the output dir
        main_path = path.join(cli.args.output_dir, *top_module.name.split(".") if top_module.is_package else "")
        with cli._open_write_file(path.join(main_path, "index.js")) as f:
            f.write("URLS=")
            json.dump(urls, f, indent=0, separators=(",", ":"))
            f.write(";\nINDEX=")
            json.dump(index, f, indent=0, separators=(",", ":"))

        # Generate search.html
        with cli._open_write_file(path.join(main_path, "search.html")) as f:
            rendered_template = pdoc._render_template("/search.mako", module=top_module, **template_config)
            f.write(rendered_template)

    cli._generate_lunr_search = _patched_generate_lunr_search

    cli.main()


if __name__ == "__main__":
    main()
