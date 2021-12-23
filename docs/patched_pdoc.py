# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""A script that patches some pdoc functionality before calling it."""
import os
import pathlib
import sys

import sphobjinv
from pdoc import __main__ as pdoc_main
from pdoc import doc as pdoc_doc
from pdoc.render import env as pdoc_env

sys.path.append(os.getcwd())

import hikari

# '-o' is the flag to provide the output dir. If it wasn't provided, we don't output the inventory
generate_inventory = "-o" in sys.argv

if generate_inventory:
    project_inventory = sphobjinv.Inventory()
    project_inventory.project = "hikari"
    project_inventory.version = hikari.__version__

    type_to_role = {
        "module": "module",
        "class": "class",
        "function": "func",
        "variable": "var",
    }

    def _add_to_inventory(dobj: pdoc_doc.Doc):
        if dobj.name.startswith("_"):
            # These won't be documented anyways, so we can ignore them
            return ""

        uri = dobj.modulename.replace(".", "/") + ".html"

        if dobj.qualname:
            uri += "#" + dobj.qualname

        project_inventory.objects.append(
            sphobjinv.DataObjStr(
                name=dobj.fullname,
                domain="py",
                role=type_to_role[dobj.type],
                uri=uri,
                priority="1",
                dispname="-",
            )
        )

        return ""

    pdoc_env.globals["add_to_inventory"] = _add_to_inventory

else:
    # Just dummy functions
    def _empty(*args, **kwargs):
        return ""

    pdoc_env.globals["add_to_inventory"] = _empty

# Run pdoc
pdoc_env.globals["__hikari_version__"] = hikari.__version__
pdoc_env.globals["__git_sha1__"] = hikari.__git_sha1__
pdoc_main.cli()

if generate_inventory:
    # Output the inventory
    text = project_inventory.data_file(contract=True)
    ztext = sphobjinv.compress(text)
    path = str(pathlib.Path.cwd() / "public" / "docs" / "objects.inv")
    sphobjinv.writebytes(path, ztext)
    print(f"Inventory written to {path!r}")
