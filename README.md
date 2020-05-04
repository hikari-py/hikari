**Note:** this API is still under active daily development, and is in a
**pre-alpha** stage. If you are looking to give feedback, or want to help us 
out, then feel free to join our [Discord server](https://discord.gg/Jx4cNGG) and
chat to us. Any help is greatly appreciated, no matter what your experience 
level may be! :-)

--- 

# _hikari_

An opinionated Discord API for Python 3 and asyncio. Built on good intentions 
and the hope that it will be extendable and reusable, rather than an obstacle.

```py
import hikari

bot = hikari.StatelessBot(token="...")


@bot.on(hikari.MessageCreateEvent)
async def ping(event):
    # If a non-bot user sends a message "hk.ping", respond with "Pong!"

    if not event.author.is_bot and event.content.startswith("hk.ping"):
        await bot.rest.create_message(event.channel_id, content="Pong!")


bot.run()
```

_And if that is too verbose, this will be actively reduced with the
functionality provided by the Stateful bot implementation coming soon!_

## What does _hikari_ aim to do?

- **Provide 100% documentation for the entire library.** Build your application
  bottom-up or top-down with comprehensive documentation as standard.
- **Ensure all components are reusable.** Most people want a basic framework for
  writing a bot, and _hikari_ will provide that. However, if you decide on a
  bespoke solution using custom components, such as a _Redis_ state cache, or
  a system where all events get put on a message queue, then _hikari_ provides
  the conduit to make that happen. 
- **Automate testing as much as possible.** You don't want to introduce bugs 
  into your bot with version updates, and neither do we. _hikari_ aims for 100%
  test coverage as standard. This significantly reduces the amount of bugs and
  broken features that appear in library releases -- something most Python
  Discord libraries cannot provide any guarantee of.
- **Small improvements. Regularly.** Discord is known for pushing sudden changes
  to their public APIs with little or no warning. When this happens, you want a 
  fix, and quickly. You do not want to wait for weeks for a usable solution to 
  be released. _hikari_ is developed using a fully automated CI pipeline with
  extensive quality assurance. This enables bugfixes and new features to be 
  shipped within 30 minutes, not 30 days. 
 
## What does _hikari_ currently support?

### Library features

_hikari_ has been designed with the best practises at heart to allow developers 
to freely contribute and help the library grow. This is achieved in multiple 
ways.

- Modular, reusable components.
- Extensive documentation.
- Full type-checking.
- Minimal dependencies.
- Full unit test suite.

### Network level components

The heart of any application that uses Discord is the network layer. _hikari_
exposes all of these components with full documentation and with the ability to
reuse them in as many ways as you can think of.

Most mainstream Python Discord APIs lack one or more of the following features. _hikari_ aims to 
implement each feature as part of the design, rather than an additional component. This enables you
to utilize these components as a black box where necessary.

- Low level REST API implementation.
- Low level gateway websocket shard implementation.
- Rate limiting that complies with the `X-RateLimit-Bucket` header __properly__.
- Gateway websocket ratelimiting (prevents your websocket getting completely invalidated).
- Intents
- Proxy support for websockets and REST API.
- File IO that doesn't block you.

### High level components

- Stateless, object-oriented bot API. Serve thousands of servers on little memory.
- Sensible, type-safe event dispatching system that is reactive to type annotations, and
  supports [PEP-563](https://www.python.org/dev/peps/pep-0563/) without broken hacks and
  bodges.
- Models that extend the format provided by Discord, not fight against it. Working as close
  to the original format of information provided by Discord as possible ensures that minimal
  changes are required when a breaking API design is introduced. This reduces the amount of
  stuff you need to fix in your applications as a result.
- REST only API functionality. Want to write a web dashboard? Feel free to just reuse the 
  REST client components to achive that!
  
### Stuff coming soon

- Optional, optimised C implementations of internals to give large applications a 
  well-deserved performance boost.
- Voice support.
- Stateful bot support (intents will be supported as first-class citizens).

### Planned extension modules for the future

- Command framework (make commands and groups with the flick of a wrist).
- Optional dependency injection tools (declare what components you want in your application, and
  where you want them. Let _hikari_ work out how to put it together!)
- Full voice transcoding support, natively in your application. Do not rely on invoking ffmpeg
  in a subprocess ever again!


## Getting started

This section is still very bare, and we are still actively writing this framework every day.
[Why not pop in and say hi?](https://discord.gg/Jx4cNGG) More comprehensive tutorials will be
provided soon!
