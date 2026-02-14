# Bot Lifecycle

It is worth noting that `hikari` provides bot lifecycle events.
In our [basic implementation](setup.md#final-program), we use the `hikari.StartedEvent`. We will describe these for further understanding.

## StartingEvent

This event is dispatched when the bot is signalled to run (via `bot.run()`). The bot will identify itself with Discord and receive it's identity (`hikari.OwnUser`).

## StartedEvent

This event is dispatched when everything internally is running. The bot isn't 100% complete until all `StartedEvent` listeners have fired and completed.

## StoppingEvent

This event is dispatched when the bot is signalled to stop (via `bot.stop()`). All internal systems will shut down and you should save your state (databases, configurations, etc.).

## StoppedEvent

This event is dispatched when all bot systems internally are stopped. Code below the `bot.run()` can now run.
