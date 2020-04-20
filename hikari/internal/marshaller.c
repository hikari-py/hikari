/*******************************************************************************
 * Copyright © Nekokatt 2019-2020                                              *
 *                                                                             *
 * This file is part of Hikari.                                                *
 *                                                                             *
 * Hikari is free software: you can redistribute it and/or modify              *
 * it under the terms of the GNU Lesser General Public License as published by *
 * the Free Software Foundation, either version 3 of the License, or           *
 * (at your option) any later version.                                         *
 *                                                                             *
 * Hikari is distributed in the hope that it will be useful,                   *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of              *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               *
 * GNU Lesser General Public License for more details.                         *
 *                                                                             *
 * You should have received a copy of the GNU Lesser General Public License    *
 * along with Hikari. If not, see <https://www.gnu.org/licenses/>.             *
 *                                                                             *
 *******************************************************************************/

///
/// Accelerated implementation of hikari.internal.marshaller for platforms with
/// a C compiler in the working environment, and built using CPython.
///
/// @author Nekokatt
/// @since  1.0.1
///

// Ensure cross compatibility with any Python version >= 3.8.0.
#define Py_LIMITED_API 0x308000

#include <Python.h>

#include <string.h>
#include <stdlib.h>


PyDoc_STRVAR(
    module_doc,
    "An internal marshalling utility used by internal API components.\n"
    "\n"
    "!!! warning\n"
    "   You should not change anything in this file, if you do, you will likely get\n"
    "   unexpected behaviour elsewhere.\n"
);


static PyObject *_import_module;


///
/// Given a root object "obj", and a period-delimited collection
/// of attribute names, perform the equivalent of
/// "eval('obj.' + attr_name)" without executing arbitrary code
/// unnecesarilly.
///
/// @param obj the object to begin on.
/// @param attr_name the string name of the attribute to get,
///     period delimited.
/// @returns NULL if an exception occurred, or the referenced object
///
/// @author Nekokatt
/// @since 1.0.1
///
static PyObject *
_recursive_getattr(PyObject * obj, const char * restrict attr_name)
{
    char * temp = malloc(strlen(attr_name) + 1);
    char * delim;

    while ((delim = strstr(attr_name, "."))) {
        temp = strncpy(temp, attr_name, delim - attr_name);
        // skip pass the period.
        attr_name = delim + 1;
        obj = PyObject_GetAttrString(obj, temp);
    }

    // getattr
    obj = PyObject_GetAttrString(obj, attr_name);
    free(temp);

    return obj;
}


PyDoc_STRVAR(
    dereference_handle_doc,
    "Parse a given handle string into an object reference.\n"
    "\n"
    "Parameters\n"
    "----------\n"
    "handle_string : str\n"
    "    The handle to the object to refer to. This is in the format\n"
    "    `fully.qualified.module.name#object.attribute`. If no `#` is\n"
    "    input, then the reference will be made to the module itself.\n"
    "\n"
    "Returns\n"
    "-------\n"
    "typing.Any\n"
    "    The thing that is referred to from this reference.\n"
    "\n"
    "Examples\n"
    "--------\n"
    "* `\"collections#deque\":\n"
    "\n"
    "    Refers to `collections.deque`\n"
    "\n"
    "* `\"asyncio.tasks#Task\"`:\n"
    "\n"
    "    Refers to `asyncio.tasks.Task`\n"
    "\n"
    "* `\"hikari.net\"`:\n"
    "\n"
    "    Refers to `hikari.net`\n"
    "\n"
    "* `\"foo.bar#baz.bork.qux\"`:\n"
    "\n"
    "    Would refer to a theoretical `qux` attribute on a `bork`\n"
    "    attribute on a `baz` object in the `foo.bar` module.\n"
);


///
/// Take an input string such as "foo", "foo#bar", "foo.bar#baz.bork";
/// and attempt to "eval" it to get the result. This works by delimiting
/// a module and an attribute by the "#" (or treating the whole string
/// as a module if that character is not present), and then
/// traversing the object graph to get nested attributes.
///
/// This is an accelerated implementation of
/// `marshaller.dereference_handle` in `marshaller.py`.
///
/// @param _ the module.
/// @param args any parameters passed to the function call.
/// @returns NULL if an exception was raised, or a PyObject reference
///          otherwise.
/// @author Nekokatt
/// @since 1.0.1
///
static PyObject *
dereference_handle(PyObject *_, PyObject *args)
{
    const char * handle_str;
    PyArg_ParseTuple(args, "s:handle_string", &handle_str);
    // Substring from the '#' onwards
    const char * p_strstr = strstr(handle_str, "#");

    if (p_strstr == NULL || (p_strstr - handle_str) <= 1) {
        // string was in format "module_name" only, or just
        // ended with a "#" erraneously (just ignore this).
        return PyObject_CallFunction(_import_module, "s", handle_str);
    } else {
        // +1 for null end byte..., -1 because it would include "#" otherwise.
        const size_t module_len = p_strstr - handle_str;
        char * module_str = malloc(module_len);

        strncpy(module_str, handle_str, module_len);
        PyObject * module = PyObject_CallFunction(_import_module, "s", module_str);
        free(module_str);

        if (module == NULL) {
            // Expect an exception to have been raised in the interpreter.
            return NULL;
        }

        PyObject * result = _recursive_getattr(module, p_strstr + 1);
        Py_DECREF(module);
        return result;
    }
}

///
/// Public method table for this module.
///
static PyMethodDef method_table[] = {
    {"dereference_handle", dereference_handle, METH_VARARGS, dereference_handle_doc},
    {NULL, NULL, 0, NULL}
};

///
/// This module descriptor.
///
static struct PyModuleDef this_module = {
    PyModuleDef_HEAD_INIT,
    "hikari.internal.marshaller",
    module_doc,
    -1,
    method_table,
};

///
/// Init this module.
///
PyMODINIT_FUNC
PyInit_marshaller(void)
{
    PyObject * importlib = PyImport_ImportModule("importlib");
    if (importlib == NULL) {
        return NULL;
    }

    _import_module = PyObject_GetAttrString(importlib, "import_module");
    Py_DecRef(importlib);

    if (_import_module == NULL) {
        return NULL;
    }

    return PyModule_Create(&this_module);
}
