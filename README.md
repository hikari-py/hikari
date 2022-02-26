<h1 align="center">hikari</h1>
<p align="center">
<a href="https://pypi.org/project/hikari"><img height="20" alt="PyPI version" src="https://img.shields.io/pypi/v/hikari"></a>
<a href="https://pypi.org/project/hikari"><img height="20" alt="Supported python versions" src="https://img.shields.io/pypi/pyversions/hikari"></a>
<br>
<a href="https://github.com/hikari-py/hikari/actions"><img height="20" alt="CI status" src="https://github.com/hikari-py/hikari/actions/workflows/ci.yml/badge.svg?branch=master&event=push"></a>
<a href="https://pypi.org/project/mypy/"><img height="20" alt="Mypy badge" src="http://www.mypy-lang.org/static/mypy_badge.svg"></a>
<a href="https://pypi.org/project/black"><img height="20" alt="Black badge" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://codeclimate.com/github/hikari-py/hikari/test_coverage"><img height="20" alt="Test coverage" src="https://api.codeclimate.com/v1/badges/f95070b25136a69b0589/test_coverage"></a>
<br>
<a href="https://discord.gg/Jx4cNGG"><img height="20" alt="Discord invite" src="https://discord.com/api/guilds/574921006817476608/widget.png"></a>
<a href="https://hikari-py.dev/hikari"><img height="20" alt="Documentation status" src="https://img.shields.io/badge/documentation-up-00FF00.svg"></a>
</p>

An opinionated, static typed Discord microframework for Python3 and asyncio that supports Discord's V8 REST API and
Gateway.

Built on good intentions and the hope that it will be extendable and reusable, rather than an obstacle for future
development.

Python 3.8, 3.9 and 3.10 are currently supported.

## Installation

Install Hikari from PyPI with the following command:

```bash
python -m pip install -U hikari
# Windows users may need to run this instead...
py -3 -m pip install -U hikari
```

----

## Bots

```py
import hikari

bot = hikari.GatewayBot(token="...")

@bot.listen()
async def ping(event: hikari.GuildMessageCreateEvent) -> None:
    # If a non-bot user sends a message "hk.ping", respond with "Pong!"
    # We check there is actually content first, if no message content exists,
    # we would get `None' here.
    if event.is_bot or not event.content:
        return

    if event.content.startswith("hk.ping"):
        await event.message.respond("Pong!")

bot.run()
```

This will only respond to messages created in guilds. You can use `DMMessageCreateEvent` instead to only listen on
DMs, or `MessageCreateEvent` to listen to both DMs and guild-based messages.

[Logging](https://docs.python.org/3/library/logging.html) will be automatically configured for you if you do not
enable it manually. This has been implemented after seeing a large number of new bot developers struggle with
writing their first bot in other frameworks simply because of working blind after not understanding or knowing how
to set up standard logging messages.

If you wish to customise the intents being used in order to change which events your bot is notified about, then you
can pass the `intents` kwarg to the `GatewayBot` constructor:

```py
# the default is to enable all unprivileged intents (all events that do not target the
# presence or activity of a specific member).
bot = hikari.GatewayBot(intents=hikari.Intents.ALL, token="...")
```

The above example would enable all intents, thus enabling events relating to member presences to be received
(you'd need to whitelist your application first to be able to start the bot if you do this).
[Other options also exist](https://hikari-py.dev/hikari/impl/bot.html#hikari.impl.bot.GatewayBot) such as
[customising timeouts for requests](https://hikari-py.dev/hikari/config.html#hikari.config.HTTPSettings.timeouts)
and [enabling a proxy](https://hikari-py.dev/hikari/config.html#hikari.config.ProxySettings).

Also note that you could pass extra options to `bot.run` during development, for example:

```py
bot.run(
    asyncio_debug=True,             # enable asyncio debug to detect blocking and slow code.

    coroutine_tracking_depth=20,    # enable tracking of coroutines, makes some asyncio
                                    # errors clearer.

    propagate_interrupts=True,      # Any OS interrupts get rethrown as errors.
)
```

[Many other helpful options](https://hikari-py.dev/hikari/impl/bot.html#hikari.impl.bot.GatewayBot.run)
exist for you to take advantage of if you wish.

Events are determined by the type annotation on the event parameter, or alternatively as a type passed to the
`@bot.listen()` decorator, if you do not want to use type hints.

```py
@bot.listen()
async def ping(event: hikari.MessageCreateEvent):
    ...

# or

@bot.listen(hikari.MessageCreateEvent)
async def ping(event):
    ...
```

---

## REST-only applications

You may only want to integrate with the REST API, for example if writing a web dashboard.

This is relatively simple to do:

```py
rest = hikari.RESTApp()

async def print_my_user(token):
    # We acquire a client with a given token. This allows one REST app instance
    # with one internal connection pool to be reused.
    async with rest.acquire(token) as client:
        my_user = await client.fetch_my_user()
        print(my_user)

asyncio.run(print_my_user("user token here"))
```

---

## Optional Features

* `hikari[server]` - Install dependencies required to enable Hikari's standard interaction server (RESTBot) functionality.
* `hikari[speedups]` - Detailed in [`hikari[speedups]`](#hikarispeedups).

## Additional resources

You may wish to use a command framework on top of Hikari so that you can start writing a bot quickly without
implementing your own command handler.

Hikari does not include a command framework by default, so you will want to pick a third party library to do it:

- [`lightbulb`](https://github.com/tandemdude/hikari-lightbulb) - a simple and easy to use command framework for Hikari.
- [`tanjun`](https://github.com/FasterSpeeding/Tanjun) - a flexible command framework designed to extend Hikari.

---

## Making your application more efficient

As your application scales, you may need to adjust some things to keep it performing nicely.

### Python optimisation flags

CPython provides two optimisation flags that remove internal safety checks that are useful for development, and change
other internal settings in the interpreter.

- `python bot.py` - no optimisation - this is the default.
- `python -O bot.py` - first level optimisation - features such as internal
    assertions will be disabled.
- `python -OO bot.py` - second level optimisation - more features (**including
    all docstrings**) will be removed from the loaded code at runtime.

**A minimum of first level of optimizations** is recommended when running bots in a production environment.

### `hikari[speedups]`

If you have a C compiler (Microsoft VC++ Redistributable 14.0 or newer, or a modern copy of GCC/G++, Clang, etc), you
can install Hikari using `pip install -U hikari[speedups]`. This will install `aiodns`, `cchardet`, `Brotli`, and
`ciso8601` which will provide you with a small performance boost.

### `uvloop`

**If you use a UNIX-like system**, you will get additional performance benefits from using a library called `uvloop`.
This replaces the default `asyncio` event loop with one that uses `libuv` internally. You can run `pip install uvloop`
and then amend your script to be something similar to the following example to utilise it in your application:

```py
import os
import hikari

if os.name != "nt":
    import uvloop
    uvloop.install()

bot = hikari.GatewayBot(...)
...
```

### Compiled extensions

Eventually, we will start providing the option to use compiled components of this library over pure Python ones if it
suits your use case. This should also enable further scalability of your application, should
[_PEP 554 -- Multiple Interpreters in the Stdlib_](https://www.python.org/dev/peps/pep-0554/#abstract) be accepted.

Currently, this functionality does not yet exist.

---

## Developing Hikari

To familiarize yourself a bit with the project, we recommend reading our
[contributing manual](https://github.com/hikari-py/hikari/blob/master/CONTRIBUTING.md).

If you wish to contribute something, you should first start by cloning the repository.

In the repository, make a virtual environment (`python -m venv .venv`) and enter it (`source .venv/bin/activate` on
Linux, or for Windows use one of `.venv\Scripts\activate.ps1`, `.venv\Scripts\activate.bat`,
`source .venv/Scripts/activate`).

The first thing you should run is `pip install nox` to install nox. This handles running predefined tasks and pipelines.

You can install any dependencies with `pip install -r requirements.txt -r dev-requirements.txt`.

Once this is complete, you can run `nox` without any arguments to ensure everything builds and is correct.

### Where can I start?

Check out the issues tab on GitHub. If you are nervous, look for issues marked as "good first issue" for something
easy to start with!

[![good-first-issues](https://img.shields.io/github/issues/hikari-py/hikari/good%20first%20issue)](https://github.com/hikari-py/hikari/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)
