**Note:** this API is still under active daily development, and is in a
**pre-alpha** stage. If you are looking to give feedback, or want to help us 
out, then feel free to join our [Discord server](https://discord.gg/Jx4cNGG) and
chat to us. Any help is greatly appreciated, no matter what your experience 
level may be! :-)

--- 

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
