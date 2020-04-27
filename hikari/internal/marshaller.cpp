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

#define Py_LIMITED_API 0x308000

#include <algorithm>
#include <sstream>
#include <string>
#include <Python.h>


#define UNUSED(x) ((void)(x))
#define RETURN_IF_NULL(var) if((var) == nullptr) { return nullptr; }


namespace hikari::internal::marshaller {
    static PyObject * dereference_handle(PyObject *py_module, PyObject *params) {
        UNUSED(py_module);

        const char *handle_cstr;
        PyArg_ParseTuple(params, "s:handle_string", &handle_cstr);

        const auto handle_str = std::string(handle_cstr);
        const auto hash_pos = handle_str.find_first_of("#");
        
        if (hash_pos == handle_str.npos) {
            return PyImport_ImportModule(handle_cstr);
        } else {
            const auto module_name = handle_str.substr(0, hash_pos);
            const auto module_obj = PyImport_ImportModule(module_name.c_str());
            RETURN_IF_NULL(module_obj);

            auto attr_name = std::stringstream(handle_str.substr(hash_pos + 1));            

            std::string token;
            PyObject *target = module_obj;
            
            while (std::getline(attr_name, token, '.')) {
                target = PyObject_GetAttrString(target, token.c_str());
                RETURN_IF_NULL(target)
            }

            return target;
        }
    }

    static PyMethodDef methods[] = { 
        // name, ptr, arg_type, docstring
        {"derefence_handle", dereference_handle, METH_VARARGS, ""},
        {nullptr, nullptr, 0, nullptr},
    };

    static PyModuleDef self = {
        PyModuleDef_HEAD_INIT,         // head
        "hikari.internal.marshaller",  // module name
        "",                            // docstring
        -1,                            // heap-size
        methods,                       // method table
        nullptr,                       // slots (multiphase init only)
        nullptr,                       // call during GC traversal of module
        nullptr,                       // call during GC clearing of module
        nullptr,                       // call during deallocation of module
    };

    PyMODINIT_FUNC PyInit_marshaller() {
        return PyModule_Create(&self);
    }
}
