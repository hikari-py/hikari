<div align="center">
<h1>hikari</h1>
<a href="https://pypi.org/project/hikari"><img height="20" alt="Supported python versions" src="https://img.shields.io/pypi/pyversions/hikari"></a>
<a href="https://pypi.org/project/hikari"><img height="20" alt="PyPI version" src="https://img.shields.io/pypi/v/hikari"></a>
<br>
<a href="https://github.com/hikari-py/hikari/actions"><img height="20" alt="CI status" src="https://github.com/hikari-py/hikari/actions/workflows/ci.yml/badge.svg?branch=master&event=push"></a>
<a href="https://pypi.org/project/mypy/"><img height="20" alt="Mypy badge" src="https://img.shields.io/badge/mypy-checked-blue"></a>
<a href="https://pypi.org/project/black"><img height="20" alt="Black badge" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://codeclimate.com/github/hikari-py/hikari/test_coverage"><img height="20" alt="Test coverage" src="https://api.codeclimate.com/v1/badges/f95070b25136a69b0589/test_coverage"></a>
<br>
<a href="https://discord.gg/Jx4cNGG"><img height="20" alt="Discord invite" src="https://discord.com/api/guilds/574921006817476608/widget.png"></a>
<a href="https://docs.hikari-py.dev/en/stable"><img height="20" alt="Documentation Status" src="https://readthedocs.org/projects/hikari-py/badge/?version=latest"></a>
</div>

An opinionated, static typed Discord microframework for Python3 and asyncio that supports Discord's v10 REST and
Gateway APIs.

Built on good intentions and the hope that it will be extendable and reusable, rather than an obstacle for future
development.

Python 3.8, 3.9, 3.10, 3.11 and 3.12 are currently supported.

## Installation

Install hikari from PyPI with the following command:

```bash
python -m pip install -U hikari
# Windows users may need to run this instead...
py -3 -m pip install -U hikari
```

----

## Bots

Hikari provides two different default bot implementations to suit your needs:

- [GatewayBot](#gatewaybot)
- [RESTBot](#restbot)

### GatewayBot

A [`GatewayBot`](https://docs.hikari-py.dev/en/stable/reference/hikari/impl/gateway_bot/#hikari.impl.gateway_bot.GatewayBot)
is one which will connect to Discord through the gateway and receive
events through there. A simple startup example could be the following:

```py
import hikari

bot = hikari.GatewayBot(token="...")

@bot.listen()
async def ping(event: hikari.GuildMessageCreateEvent) -> None:
    """If a non-bot user mentions your bot, respond with 'Pong!'."""

    # Do not respond to bots nor webhooks pinging us, only user accounts
    if not event.is_human:
        return

    me = bot.get_me()

    if me.id in event.message.user_mentions_ids:
        await event.message.respond("Pong!")

bot.run()
```

This will only respond to messages created in guilds. You can use `DMMessageCreateEvent` instead to only listen on
DMs, or `MessageCreateEvent` to listen to both DMs and guild-based messages. A full list of events
can be found in the [events docs](https://docs.hikari-py.dev/en/stable/reference/hikari/events/).

If you wish to customize the intents being used in order to change which events your bot is notified about, then you
can pass the `intents` kwarg to the `GatewayBot` constructor:

```py
import hikari

# the default is to enable all unprivileged intents (all events that do not target the
# presence, activity of a specific member nor message content).
bot = hikari.GatewayBot(intents=hikari.Intents.ALL, token="...")
```

The above example would enable all intents, thus enabling events relating to member presences to be received
(you'd need to whitelist your application first to be able to start the bot if you do this).

Events are determined by the type annotation on the event parameter, or alternatively as a type passed to the
`@bot.listen()` decorator, if you do not want to use type hints.

```py
import hikari

bot = hikari.GatewayBot("...")

@bot.listen()
async def ping(event: hikari.MessageCreateEvent):
    ...

# or

@bot.listen(hikari.MessageCreateEvent)
async def ping(event):
    ...
```

### RESTBot

A [`RESTBot`](https://docs.hikari-py.dev/en/stable/reference/hikari/impl/rest_bot/#hikari.impl.rest_bot.RESTBot)
spawns an interaction server to which Discord will **only** send interaction events,
which can be handled and responded to.

An example of a simple `RESTBot` could be the following:

```py
import asyncio

import hikari


# This function will handle the interactions received
async def handle_command(interaction: hikari.CommandInteraction):
    # Create an initial response to be able to take longer to respond
    yield interaction.build_deferred_response()

    await asyncio.sleep(5)

    # Edit the initial response
    await interaction.edit_initial_response("Edit after 5 seconds!")


# Register the commands on startup.
#
# Note that this is not a nice way to manage this, as it is quite spammy
# to do it every time the bot is started. You can either use a command handler
# or only run this code in a script using `RESTApp` or add checks to not update
# the commands if there were no changes
async def create_commands(bot: hikari.RESTBot):
    application = await bot.rest.fetch_application()

    await bot.rest.set_application_commands(
        application=application.id,
        commands=[
            bot.rest.slash_command_builder("test", "My first test command!"),
        ],
    )


bot = hikari.RESTBot(
    token="...",
    token_type="...",
    public_key="...",
)

bot.add_startup_callback(create_commands)
bot.set_listener(hikari.CommandInteraction, handle_command)

bot.run()
```

Unlike `GatewayBot`, registering listeners is done through `.set_listener`, and it takes in an interaction type
that the handler will take in.

Note that a bit of a setup is required to get the above code to work. You will need to host the project to
the World Wide Web (scary!) and then register the URL on the [Discord application portal](https://discord.com/developers/applications)
for your application under "Interactions Endpoint URL".

A quick way you can get your bot onto the internet and reachable by Discord (**for development environment only**) is
through a tool like [ngrok](https://ngrok.com/) or [localhost.run](https://localhost.run/). More information on how to
use them can be found in their respective websites.

### Common helpful features

Both implementations take in helpful arguments such as [customizing timeouts for requests](https://docs.hikari-py.dev/en/stable/reference/hikari/impl/config/#hikari.impl.config.HTTPSettings.timeouts)
and [enabling a proxy](https://docs.hikari-py.dev/en/stable/reference/hikari/impl/config/#hikari.impl.config.ProxySettings),
which are passed directly into the bot during initialization.

Also note that you could pass extra options to `bot.run` during development, for example:

```py
import hikari

bot = hikari.GatewayBot("...")
# or
bot = hikari.RESTBot("...", "...")

bot.run(
    asyncio_debug=True,             # enable asyncio debug to detect blocking and slow code.

    coroutine_tracking_depth=20,    # enable tracking of coroutines, makes some asyncio
                                    # errors clearer.

    propagate_interrupts=True,      # Any OS interrupts get rethrown as errors.
)
```

Many other helpful options exist for you to take advantage of if you wish. Links to the respective docs can be seen
below:

- [GatewayBot.run](https://docs.hikari-py.dev/en/stable/reference/hikari/impl/gateway_bot/#hikari.impl.gateway_bot.GatewayBot.run)
- [RESTBot.run](https://docs.hikari-py.dev/en/stable/reference/hikari/impl/rest_bot/#hikari.impl.rest_bot.RESTBot.run)

---

## REST-only applications

You may only want to integrate with the REST API, for example if writing a web dashboard.

This is relatively simple to do:

```py
import hikari
import asyncio

rest = hikari.RESTApp()

async def print_my_user(token):
    await rest.start()
  
    # We acquire a client with a given token. This allows one REST app instance
    # with one internal connection pool to be reused.
    async with rest.acquire(token) as client:
        my_user = await client.fetch_my_user()
        print(my_user)

    await rest.close()
        
asyncio.run(print_my_user("user token acquired through OAuth here"))
```

---

## Optional Features

Optional features can be specified when installing hikari:

* `server` - Install dependencies required to enable Hikari's standard interaction server (RESTBot) functionality.
* `speedups` - Detailed in [`hikari[speedups]`](#hikarispeedups).

Example:

```bash
# To install hikari with the speedups feature:
python -m pip install -U hikari[speedups]

# To install hikari with both the speedups and server features:
python -m pip install -U hikari[speedups, server]
```

## Additional resources

You may wish to use a command framework on top of hikari so that you can start writing a bot quickly without
implementing your own command handler.

Hikari does not include a command framework by default, so you will want to pick a third party library to do it:

- [`arc`](https://github.com/hypergonial/hikari-arc) - a bot framework with a focus on type-safety and correctness.
- [`crescent`](https://github.com/magpie-dev/hikari-crescent) - a command handler for hikari that keeps your project neat and tidy.
- [`lightbulb`](https://github.com/tandemdude/hikari-lightbulb) - a simple and easy to use command framework for hikari.
- [`tanjun`](https://github.com/FasterSpeeding/Tanjun) - a flexible command framework designed to extend hikari.

There are also third party libraries to help you manage components:

- [`miru`](https://github.com/hypergonial/hikari-miru) - A component handler for hikari, inspired by discord.py's views.
- [`flare`](https://github.com/brazier-dev/hikari-flare/) - a component manager designed to write simple interactions with persistent data.

---

## Making your application more efficient

As your application scales, you may need to adjust some things to keep it performing nicely.

### Python optimization flags

CPython provides two optimization flags that remove internal safety checks that are useful for development, and change
other internal settings in the interpreter.

- `python bot.py` - no optimization - this is the default.
- `python -O bot.py` - first level optimization - features such as internal assertions will be disabled.
- `python -OO bot.py` - second level optimization - more features (**including all docstrings**) will be removed from
  the loaded code at runtime.

**A minimum of first level of optimization** is recommended when running bots in a production environment.

### `hikari[speedups]`

If you have a C compiler (Microsoft VC++ Redistributable 14.0 or newer, or a modern copy of GCC/G++, Clang, etc), it is
recommended you install Hikari using `pip install -U hikari[speedups]`. This will install `aiohttp` with its available
speedups, `ciso8601` and `orjson` which will provide you with a substantial performance boost.

### `uvloop`

**If you use a UNIX-like system**, you will get additional performance benefits from using a library called `uvloop`.
This replaces the default `asyncio` event loop with one that uses `libuv` internally. You can run `pip install uvloop`
and then amend your script to be something similar to the following example to utilise it in your application:

```py
import asyncio
import os

if os.name != "nt":
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


# Your code goes here
```

### Compiled extensions

Eventually, we will start providing the option to use compiled components of this library over pure Python ones if it
suits your use case. This should also enable further scalability of your application, should
[_PEP 554 -- Multiple Interpreters in the Stdlib_](https://www.python.org/dev/peps/pep-0554/#abstract) be accepted.

Currently, this functionality does not yet exist.

---

## Developing hikari

To familiarize yourself a bit with the project, we recommend reading our
[contributing manual](https://github.com/hikari-py/hikari/blob/master/CONTRIBUTING.md).

If you wish to contribute something, you should first start by cloning the repository.

In the repository, make a virtual environment (`python -m venv .venv`) and enter it (`source .venv/bin/activate` on
Linux, or for Windows use one of `.venv\Scripts\activate.ps1`, `.venv\Scripts\activate.bat`,
`source .venv/Scripts/activate`).

The first thing you should run is `pip install -r dev-requirements.txt` to install nox.
This handles running predefined tasks and pipelines.

Once this is complete, you can run `nox` without any arguments to ensure everything builds and is correct.

### Where can I start?

Check out the issues tab on GitHub. If you are nervous, look for issues marked as "good first issue" for something
easy to start with!

[![good-first-issues](https://img.shields.io/github/issues/hikari-py/hikari/good%20first%20issue)](https://github.com/hikari-py/hikari/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)

Feel free to also join our [Discord](https://discord.gg/Jx4cNGG) to directly ask questions to the maintainers! They will
be glad to help you out and point you in the right direction.
