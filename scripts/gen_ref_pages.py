"""Generate the code reference pages.

Based on https://mkdocstrings.github.io/recipes/#generate-pages-on-the-fly
"""

import os
from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

src = Path(__file__).parent.parent / "hikari"

# Respect env var to skip generating reference docs
if (value := os.environ.get("SKIP_REFERENCE_DOCS")) and value != "0":
    print("Skipping reference docs")
    exit(0)

# Get the custom index page & copy it over
with mkdocs_gen_files.open("reference/index.md", "w") as fd:
    with open("docs/reference_index.md", "r") as index:
        fd.write(index.read())

mkdocs_gen_files.set_edit_path("reference/index.md", "docs/reference_index.md")


for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if "internal" in parts:
        continue
    elif parts[-1] == "__init__":
        parts = parts[:-1]
        # Ignore the root __init__.py
        if parts == ():
            continue
        # Make the __init__.py the index page of the module
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    # Ignore the __main__.py and private modules
    elif parts[-1] == "__main__":
        continue
    elif parts[-1].startswith("_"):
        continue

    nav[parts] = doc_path.as_posix()

    # We could probably use some sort of template file for this if needed
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(
            "---\n"
            f"title: hikari.{ident}\n"
            f"description: hikari.{ident} - API reference\n"
            "---\n"
            "\n"
            f"# `hikari.{ident}`\n"
            "\n"
            f"::: hikari.{ident}\n"
        )

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    print("* [API Reference](index.md)", file=nav_file)
    nav_file.writelines(nav.build_literate_nav())
