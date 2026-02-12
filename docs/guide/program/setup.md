# Program Setup

We need to set up our bot's program to run, and here's how to do it.
Each section will be discussed in detail for further understanding.

## Creating our File

`Python` file names, by convention, end in `.py` to signify that the file is a `Python` program file.
Entrypoint files (where `Python` begins execution) are typically named `main.py`.

Open your project folder in the IDE of your choice and create a `main.py` file and follow the directions below.

## Import hikari

We need to tell the `Python` interpreter that we wish to use the `hikari` library in our program. This can be done by importing `hikari`:

```python
import hikari
```

## Defining the Bot

To create a Discord gateway bot, we need to create a `hikari`.`GatewayBot` instance.
This bot takes our [OAuth2 Token](../oauth2.md#bot) from earlier and identifies itself with Discord as a gateway bot.

There are extra parameters that this bot takes, but these will be discussed later.

```python
bot = hikari.GatewayBot(TOKEN)
```

## Listen for Events

The Discord gateway will send any events we intend to listen to through gateway events (implemented in children implementations of `hikari.Event`).
To listen for these events, we need to register them with our bot instance.

When events are dispatched by the bot, the event itself is passed into the first parameter of an asynchronous/coroutine function that can be named anything (keep it readable and understandable, however). This function should not return anything.

If we want to print `"Hello world"` when the bot is started, we listen for the `hikari.StartedEvent` with the following:

```python
@bot.listen(hikari.StartedEvent)
async def bot_started(event: hikari.StartedEvent) -> None:
    print("Hello world")
```

The `bot.listen(hikari.StartedEvent)` decorator is the `GatewayBot`'s way of registering events in a clean and readable manner.

It is important to note that stating `hikari.StartedEvent` in the listening decorator and as the type annotation for the first parameter of `bot_started` can be repetitive. The following are also correct for registering events with the bot:

```python
# Annotating the first parameter only (the common method)
@bot.listen()
async def bot_started(event: hikari.StartedEvent) -> None:
    ...
```

```python
# Declaring the event type in the decorator only (less preferable)
@bot.listen(hikari.StartedEvent)
async def bot_started(event) -> None:
    ...
```

It is also important to note that depending on your implementation and design of your bot, the `@bot.listen` decorator may not work for your use case, however this is not very common for basic bots.
The following `bot.subscribe()` method may also be used to register event listeners:

```python
async def bot_started(event: hikari.StartedEvent) -> None:
    print("Hello world")

bot.subscribe(hikari.StartedEvent, bot_started)
```

## Running the Bot

To actually run the bot and make it work, we have to run the bot itself.

```python
bot.run()
```

Super simple.

## Final Program

```python
import hikari

bot = hikari.GatewayBot(TOKEN)

@bot.listen()
async def bot_started(event: hikari.GatewayBot) -> None:
    print("Hello world")

bot.run()
```

```
>>> Hello world
```

Congratulations! The bot is running and you should see the bot online in the server you invited it to.

To respond to messages sent by users, follow our [Reply Program](examples/reply-program.md).
