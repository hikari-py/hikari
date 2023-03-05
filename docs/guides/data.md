# Obtaining Data

Many operations you might want to do via your bot may require additional data to complete, for example, information
about users, guilds, channels, and so on. There's two main ways of obtaining this information, both detailed below.

## REST

The first option is to query the Discord API directly for this information, which, while typically guarantees to
provide the most up-to-date information possible, is much slower and consumes API ratelimits. Therefore it is advisable
to avoid calling these often (e.g. per event).

```py
bot = hikari.GatewayBot(...)
# OR
bot = hikari.RESTBot(...)

# -- Snip --

# Requesting a specific guild's data
guild_id = ...
guild = await bot.rest.fetch_guild(guild_id)
print(f"The guild's name is {guild.name}!")

```

All rest calls can be performed via the `bot`'s `RESTClient` instance, which can be accessed via `bot.rest`.

```{note}
Please note that the available data may depend on what intents your bot has. For example, you cannot fetch specific members
without the `GUILD_MEMBERS` intent. Please see the intents section of the guide for more on this.
```

You can also use the `RESTClient` to perform actions on Discord via your bot, for example send a message, create a new role,
or kick someone.

```py
channel_id = ...
await bot.rest.create_message(channel_id, "Hello!")
```

For all available rest methods, see [this page](https://docs.hikari-py.dev/en/latest/reference/hikari/api/rest/).

## Cache

```{note}
The cache is only available if your application uses `GatewayBot` as its base.
```

hikari, by default, caches most objects received in events through the gateway, and also performs a process called "chunking"
on startup, where it populates the bot's cache with guilds, channels (and members, if you have that priviliged intent). Accessing
data this way is much faster, and doesn't consume ratelimits, therefore it is the recommended way of obtaining information.

```py
guild_id = ...
guild = bot.cache.get_guild(guild_id)
print(f"The guild's name is {guild.name}!")
```

All cache calls can be performed via the `bot`'s `Cache` instance, which can be accessed via `bot.cache`.

To configure what gets cached by hikari, you may pass an instance of :obj:`hikari.impl.config.CacheSettings` to the `cache_settings` keyword-only argument of
the `GatewayBot` upon instantiation.
