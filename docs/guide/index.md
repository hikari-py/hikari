# Usage Guide

This guide will show developers how exactly they can use `hikari`. It will go over using the `GatewayBot` to listen for and handle dispatched events from Discord.

`hikari` is a lightweight and modular Discord bot library. You can create gateway applications (those that communicate with a websocket with Discord directly) or REST API applications (communicating over HTTP). The most common is the gateway application, implemented with `GatewayBot`.

`hikari` is written in Python and supports all non-deprecated/current versions.
Environment setup will be discussed in a further page.

It is recommended that you read and understand all of Discord's interaction objects and functionality before moving further, discussed below.

If you already have a Discord application made and have the token, skip to [Environment](environment/index.md).

To get started, start by visiting [Application](application.md).

## Guilds (Servers)

[Guilds](https://discord.com/developers/docs/resources/guild#guild-object) are commonly referred to as "servers". Discord doesn't call guilds "servers" in documentation.

## Intents

Discord outlines intents as what your bot/application **intends** on implementing and using. Most intents are unpriveleged (meaning no authorization is necessary) where some are **priveleged**, meaning Discord must manually authorize your bot to access information provided by those intents once your bot reaches a certain threshold of guilds.
A list of all publicly documented intents can be found [here](https://discord.com/developers/docs/events/gateway#list-of-intents).

## REST (HTTP)

The Discord REST API allows HTTP requests to add/update/delete objects and systems within Discord.
Most Discord objects (like guilds, channels, messages, users/members) have REST functionality (like `channel.create_message()`, etc.) implemented by `hikari`.

## Snowflakes (IDs)

[Snowflakes](https://discord.com/developers/docs/reference#snowflakes) are Discord's unique identifiers (or `ID`s). They are essentially regular integers and are treated that way by `hikari` internally.
Discord provides a diagram that shows how they are made and what specific parts of the snowflake are for.
