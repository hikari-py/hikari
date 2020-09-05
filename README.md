[![hikarivers](https://img.shields.io/pypi/v/hikari)](https://pypi.org/project/hikari)
[![pyvers](https://img.shields.io/pypi/pyversions/hikari)](https://pypi.org/project/hikari)
[![codecov](https://img.shields.io/codecov/c/github/nekokatt/hikari)](https://codecov.io/gh/nekokatt/hikari)
[![prs](https://img.shields.io/github/issues-pr/nekokatt/hikari)](https://github.com/nekokatt/hikari/pulls)
[![issues](https://img.shields.io/github/issues-raw/nekokatt/hikari)](https://github.com/nekokatt/hikari/issues)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://pypi.org/project/black/)
[![mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](https://pypi.org/project/mypy/)
[![docs](https://img.shields.io/badge/documentation-up-00FF00.svg)](https://nekokatt.github.io/hikari/hikari)

[![Discord](https://discord.com/api/guilds/574921006817476608/widget.png?style=banner2)](https://discord.gg/Jx4cNGG)

# _hikari_

An opinionated, static typed Discord microframework for Python3 and asyncio.

Built on good intentions and the hope that it will be extendable and reusable,
rather than an obstacle for future development.

```py
import hikari

bot = hikari.Bot(token="...")


@bot.listen()
async def ping(event: hikari.MessageCreateEvent) -> None:
    # If a non-bot user sends a message "hk.ping", respond with "Pong!"

    if not event.message.author.is_bot and event.message.content.startswith("hk.ping"):
        await event.message.reply("Pong!")


bot.run()
```

Events are determined by the type annotation on the event parameter, or
alternatively as a type passed to the `@bot.listen()` decorator, if you do not
want to use type hints.

```py
@bot.listen(hikari.MessageCreateEvent)
async def ping(event):
    ...
```

----

## Installation

Install hikari from PyPI with the following command:

```bash
python -m pip install hikari -U --pre
# Windows users may need to run this instead...
py -3 -m pip install hikari -U --pre
```

----

## Additional resources

You may wish to use a command framework on top of Hikari so that you can start
writing a bot quickly without implementing your own command handler.

Hikari does not include a command framework by default, so you will want to pick
a third party library to do it.

- [`lightbulb`](https://gitlab.com/tandemdude/lightbulb) - a simple and easy to
  use command framework for Hikari.

----

## Making your application more efficient

As your application scales, you may need to adjust some things to keep it
performing nicely.

### Python optimisation flags

CPython and Stackless Python provide two optimisation flags that remove internal
safety checks that are useful for development, and change other internal
settings in the interpreter.

- `python bot.py` - no optimisation - this is the default.
- `python -O bot.py` - first level optimisation - features such as internal
    assertions will be disabled.
- `python -OO bot.py` - second level optimisation - more features (**including
    all docstrings**) will be removed from the loaded code at runtime.

### `hikari[speedups]`

If you have a C compiler (Microsoft VC++ Redis 14.0 or newer, or a modern copy
of GCC/G++, Clang, etc), you can install hikari using
`pip install -U hikari[speedups]`. This will install `aiodns`, `cchardet`,  and
`ciso8601`, which will provide you with a small performance boost.

### `uvloop`

**If you use Linux**, you will get additional performance benefits from using
a library called `uvloop`. This replaces the default `asyncio` event loop with
one that uses `libuv` internally. You can run `pip install uvloop` and then
amend your script to be something similar to the following example to utilise it
in your application:

```py
import os
import hikari

if os.name != "nt":
    import uvloop
    uvloop.install()

bot = hikari.Bot(...)
...
```

### Compiled extensions

Eventually, we will start providing the option to use compiled components of
this library over pure Python ones if it suits your use case. This should also
enable further scalability of your application, should
[_PEP 554 -- Multiple Interpreters in the Stdlib_](https://www.python.org/dev/peps/pep-0554/#abstract)
be accepted.

Currently, this functionality does not yet exist.

---

## Developing Hikari

If you wish to contribute something, you should first start by cloning the
repository.

The first thing you should run is `pip install nox` to install nox. This handles
running predefined tasks and pipelines.

To initialize a development environment and install everything you need, simply
run `nox -s init`. This will create a venv and install everything you need in it
to get started.

Once this is complete, you can run `nox` without any arguments to ensure
everything builds and is correct.

### Where can I start?

Check out the issues tab on GitHub. If you are nervous, look for issues
marked as ![good-first-issue-badge](https://img.shields.io/github/labels/nekokatt/hikari/good%20first%20issue) for
 something easy to start with!

[![good-first-issues](https://img.shields.io/github/issues/nekokatt/hikari/good%20first%20issue)](https://github.com/nekokatt/hikari/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)
