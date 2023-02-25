# Advanced Usage

```{attention}
This guide only applies to GatewayBot. REST-only applications cannot receive events through the gateway.
```

## wait_for

Sometimes you may want to wait for an event to be received in a procedural manner, then proceed
with execution.

With `wait_for()` you can block until you receive an event with a given predicate and timeout.

In the example below, the bot prompts the user to play a number guessing game.
Each iteration, the bot waits for the user to input a number, evaluates it, then gives an
appropiate response.

```py
# We use random for number-generation and asyncio for exception handling
import asyncio
import random

import hikari

# -- Snip --

@bot.listen()
async def guessing_game(event: hikari.MessageCreateEvent) -> None:

    if not event.is_human:
        return

    me = bot.get_me()

    # We only want to respond to messages where the bot is pinged
    # Please note that bots by default do not receive message content for messages
    # where they are not pinged or DMd, see the intents section for more information!
    if me.id not in event.message.user_mentions_ids:
        return

    number = random.randint(1, 10)
    guess = None
    player = event.author

    await event.message.respond("I thought of a number between 1 and 10!\nPlease enter your first guess!")

    while guess != number:
        try:
            input_event = await bot.wait_for(
                hikari.MessageCreateEvent, 
                # We only want to check for input coming from the player
                # We also want to ensure there is content to parse
                predicate=lambda e: e.author_id == player.id and e.content is not None,
                # Timeout, in seconds
                timeout=60
            )
        except asyncio.TimeoutError:
            await event.message.respond(f"{player.mention} did not guess the number in time!")
            break

        if not input_event.content.isdigit():
            await input_event.message.respond(f"{player.mention}, please enter a valid guess!")
            continue
        
        guess = int(input_event.content)

        if guess < number:
            await input_event.message.respond(f"{player.mention}, your guess is too low!")
        elif guess > number:
            await input_event.message.respond(f"{player.mention}, your guess is too high!")
        
    await event.message.respond(f"You guessed the number! It was **{number}**!")

# -- Snip --
```

---

## stream

If you prefer a more functional approach to event handling, you can also use hikari's event streams!

In the example below, we query the user for their 3 most favorite movies and gather them into a list.

```py
@bot.listen()
async def favorite_movie_collector(event: hikari.MessageCreateEvent) -> None:

    if not event.is_human:
        return

    me = bot.get_me()

    # We only want to respond to messages where the bot is pinged
    # Please note that bots by default do not receive message content for messages
    # where they are not pinged or DMd, see the intents section for more information!
    if me.id not in event.message.user_mentions_ids:
        return


    await event.message.respond("Please enter your 3 favorite movies!")

    with bot.stream(hikari.MessageCreateEvent, timeout=None) as stream:
        movies = await (
            stream
            .filter(lambda e: e.author_id == event.author.id and bool(event.message.content))
            .limit(3)
            .map(lambda e: e.message.content)
            .collect(list)
        )

        await event.message.respond(f"Your favorite movies are:```{' '.join(movies)}```")
```

For more methods available on hikari's `LazyIterator`, check [this page](https://docs.hikari-py.dev/en/latest/reference/hikari/iterators/#hikari.iterators.LazyIterator).
