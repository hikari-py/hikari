#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
This runs a single sharded http and gateway. It provides a Tkinter window that you can type Python code into and have
it evaluated with three variables in scope: `http`, `gateway`, and `loop`.

All you need to do is set the TOKEN environment variable to be your bot account's token and away you go.

This is a partial proof of concept that the library is usable, but mostly to enable me to run HTTP queries while
connected to the gateway without using Postman and writing the queries out by hand. It uses a Tkinter window to
separate the REPL output and the logs, which are set to debug for convenience.
"""
import ast
import asyncio
import contextlib
import io
import logging
import os
import pprint
import textwrap
import threading
import tkinter
import tkinter.scrolledtext
import traceback

from hikari import errors
from hikari.net import gateway
from hikari.net import http_client


NSEW = tkinter.N + tkinter.S + tkinter.E + tkinter.W


class App(threading.Thread):
    def __init__(self):
        super().__init__(name="Asyncio thread", daemon=True)
        self.loop = None
        self.gateway = None
        self.http = None
        self.token = os.environ["TOKEN"]
        self.die = False

    def run(self):
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self._run())

    async def _run(self):
        while not self.die:
            try:
                self.http = http_client.HTTPClient(loop=self.loop, token=self.token)
                self.gateway = gateway.GatewayClient(loop=self.loop, token=self.token,
                                                     host=await self.http.get_gateway())
                await self.gateway.run()
            except errors.Unauthorized as ex:
                logging.exception("You are unauthorized, I cant continue :(", exc_info=ex)
                return
            except Exception as ex:
                logging.exception("An error occurred", exc_info=ex)
                await asyncio.sleep(5)

    def eval(self, code):
        return asyncio.run_coroutine_threadsafe(self._eval(code), self.loop)

    async def _eval(self, code):
        stdout = io.StringIO()

        # If we have an expr node as the root, automatically append on a
        # call to return to implicitly return the expr'ed value.
        try:
            abstract_syntax_tree = ast.parse(code)

            node: list = abstract_syntax_tree.body

            if node and type(node[0]) is ast.Expr:
                code = f"return " + code.strip()
        except Exception:
            pass

        code = textwrap.indent(code, "    ")
        code = "async def __run__():\n" + code

        try:
            with contextlib.redirect_stdout(stdout):
                try:
                    local_vars = {}
                    global_vars = {"http": self.http, "loop": self.loop, "gateway": self.gateway}
                    exec(code, global_vars, local_vars)
                    runner = local_vars["__run__"]
                    result = await runner()
                    result_repr = pprint.pformat(result, indent=4)
                    result_repr = textwrap.indent(result_repr, "<<< ")
                    stdout.write(result_repr)
                    stdout.write("\n\n" + "=" * 100 + "\n")
                except Exception:
                    print(traceback.format_exc())
        finally:
            return stdout.getvalue()


class Dialog(tkinter.Tk):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tkinter.Grid.rowconfigure(self, 0, weight=1)
        tkinter.Grid.columnconfigure(self, 0, weight=1)
        self.title("Hikari low level REPL")
        self.frame = tkinter.Frame(self)
        self.frame.grid(row=0, column=0, sticky=NSEW)

        for i in range(1, 4):
            tkinter.Grid.rowconfigure(self.frame, i, weight=1)

        tkinter.Grid.columnconfigure(self.frame, 1, weight=1)

        self.output = tkinter.scrolledtext.ScrolledText(self.frame)
        self.output.insert("1.0", textwrap.dedent(
            """
            Hikari REPL
            
            Variables:
                - `http`: the HTTP client
                - `gateway` - the gateway client
                - `loop` - the event loop
                
            Enter some code and click `run`. For example: `await http.get_gateway_bot()`.
            
            Close the window to log out.
            """
        ))
        self.output.config(state="disabled")

        self.output.config(bg="light grey")
        self.input = tkinter.scrolledtext.ScrolledText(self.frame)
        self.submit = tkinter.Button(self.frame, text="Run", command=self.on_submit)
        self.output.grid(row=1, column=1, sticky=NSEW)
        self.input.grid(row=2, column=1, sticky=NSEW)
        self.submit.grid(row=3, column=1, sticky=tkinter.E + tkinter.W)

        self.app = app

    def on_submit(self):
        # No idea what this actually means but whatever.
        code = self.input.get("1.0", tkinter.END)
        self.input.delete("1.0", tkinter.END)
        preview_code = textwrap.indent(code, ">>> ")
        self.output.config(state="normal")
        self.input.config(state="disabled")
        self.output.insert(tkinter.END, preview_code)
        output = self.app.eval(code)
        output = output.result()
        self.output.insert(tkinter.END, output)
        self.output.config(state="disabled")
        self.input.config(state="normal")
        self.output.see("end")


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    app = App()
    app.start()
    Dialog(app).mainloop()
    app.die = True
    logging.critical("Shutting down safely, please wait.")
    asyncio.run_coroutine_threadsafe(app.http.close(), app.loop).result()
    asyncio.run_coroutine_threadsafe(app.gateway.close(), app.loop).result()

