[![hikarivers](https://img.shields.io/pypi/v/hikari)](https://pypi.org/project/hikari)
[![pyvers](https://img.shields.io/pypi/pyversions/hikari)](https://pypi.org/project/hikari)
[![codecov](https://img.shields.io/codecov/c/github/nekokatt/hikari)](https://codecov.io/gh/nekokatt/hikari)
[![prs](https://img.shields.io/github/issues-pr/nekokatt/hikari)](https://github.com/nekokatt/hikari/pulls)
[![issues](https://img.shields.io/github/issues-raw/nekokatt/hikari)](https://github.com/nekokatt/hikari/issues)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://pypi.org/project/black/)
[![mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](https://pypi.org/project/mypy/)
[![docs](https://img.shields.io/badge/documentation-up-00FF00.svg)](https://nekokatt.github.io/hikari/hikari)

[![Discord](https://discord.com/api/guilds/81384788765712384/widget.png?style=banner2)](https://discord.gg/Jx4cNGG)

# _hikari_

An opinionated, static typed Discord API for Python3 and asyncio.

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

## Additional libraries

You may wish to use a command framework on top of Hikari so that you can start
writing a bot quickly without implementing your own command handler.

Hikari does not include a command framework by default, so you will want to pick
a third party library to do it.

- [`lightbulb`](https://gitlab.com/tandemdude/lightbulb) - a simple and easy to
  use command framework for Hikari.

----

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
