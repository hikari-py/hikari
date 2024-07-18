"""Generate the code reference pages.

Based on https://mkdocstrings.github.io/recipes/#generate-pages-on-the-fly
"""

import pathlib

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

for path in sorted(pathlib.Path("hikari").rglob("*.py")):
    module_path = path.relative_to(".").with_suffix("")
    doc_path = path.relative_to(".").with_suffix(".md")
    full_doc_path = pathlib.Path("reference", doc_path)

    parts = tuple(module_path.parts)

    index = False

    # Ignore the internals module
    if "internal" in parts:
        continue
    elif parts[-1] == "__init__":
        index = True
        parts = parts[:-1]
        # Make the __init__.py the index page of the module
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")

    # Ignore dunder and private modules
    elif parts[-1].startswith("_"):
        continue

    nav[parts] = doc_path.as_posix()

    # We could probably use some sort of template file for this if needed
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        full_name = ".".join(parts)
        fd.write(
            "---\n"
            f"title: `{full_name}`\n"
            f"description: {full_name} - API reference\n"
            "---\n"
            f"# `{full_name}`\n"
            f"::: {full_name}\n"
        )

        # As of this commit b327b908 in griffe the idea of "exported" members has changed
        # when it comes to `__init__` files, but we can work around it by explicitly
        # removing all members from the init renders, leaving only the docstrings
        # see: https://github.com/mkdocstrings/griffe/commit/d9546c8eb8f4ce5d3a216309937a6552
        # see: https://github.com/mkdocstrings/python/issues/39
        if index:
            fd.write("    options:\n")
            fd.write("      members: false\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, pathlib.Path("..", path))

with mkdocs_gen_files.open("reference/summary.md", "w") as nav_file:
    for item in nav.items():
        path = pathlib.Path(item.filename).with_suffix("")

        if path.name == "index":
            path = path.parent

        full_name = ".".join(path.parts)
        nav_file.write("    " * item.level + f"* [{full_name}]({item.filename})\n")
