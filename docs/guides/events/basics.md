# Basics

```{attention}
This guide only applies to GatewayBot. REST-only applications cannot receive events through the gateway.
```

## What are events?

When your application connects to the Discord Gateway, it will start receiveing information about actions
happening within the guilds your bot is a member of. These pieces of information are called "events",
and inform your bot about actions other users or bots may have triggered.

An example would be `MessageCreateEvent`, which the bot receives every time a message is sent in a channel
the bot can see. It contains some information about the message, where it was sent, etc..

## Listeners

To execute code when the bot receives an event, we can create a listener. This is an async function that
will be called every time an event of the type we specified is encountered.

```py
@bot.listen()
async def message_listener(event: hikari.MessageCreateEvent) -> None:
    print(f"I have received a message from {event.author} in {event.channel_id}!")
```

You may also put the event's type in the decorator instead of a type annotation:

```py
@bot.listen(hikari.MessageCreateEvent)
async def message_listener(event) -> None:
    print(f"I have received a message from {event.author} in {event.channel_id}!")
```

Each event type has different attributes, for a list of all event types, see [this page](https://docs.hikari-py.dev/en/latest/reference/hikari/events/).

---

```{attention}
The above example makes the assumption that you do not plan to respond to the message. If you want to do so, you must first check if the message does not
originate from your bot, otherwise you may end up in an infinite loop!
```

### Don't

```py
@bot.listen()
async def message_listener(event: hikari.MessageCreateEvent) -> None:
    # This will end up in an infinite loop with the bot responding to itself
    await event.message.respond("Hi!")
```

### Do

```py
@bot.listen()
async def message_listener(event: hikari.MessageCreateEvent) -> None:
    if event.is_bot: # Ignore messages from bots
        return
    
    await event.message.respond("Hi!")
```

---

## Subscribing listeners

It may be undesirable, or even infeasible to use the decorator-syntax above to create a listener in some cases,
such as when trying to programatically register listeners. This is where `subscribe()` comes in.

```py
bot = hikari.GatewayBot(...)

# -- Snip --

async def message_listener(event: hikari.MessageCreateEvent) -> None:
    print(f"I have received a message from {event.author} in {event.channel_id}!")

# -- Snip --

bot.subscribe(hikari.MessageCreateEvent, message_listener)
```

You may also use `unsubscribe()` to deregister a listener function from a given event type the same way.
