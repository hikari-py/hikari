# hikari

An opinionated Discord API for Python 3 and asyncio.

## What is this API?

A base Python Discord API framework for CPython 3.7 and CPython 3.8 Designed for ease of use,
customization, and sane defaults.

This API is designed to provide the pure-python interface to the RESTful Discord API and the Gateway. This will provide
a set of basic models and abstractions that can be used to build a basic Discord bot in Python with asyncio in a
logical, idiomatic, Pythonic, concise way.

Other APIs may exist that are faster, use less memory, or are smaller. I wont dispute that. The aim of this library is
to provide a solid and consistent interface that can be __relied__ upon by the end user, and to provide regular updates
that are able to be opted into.

I also aim to provide as much automated test coverage as possible. I want to be able to immediately prove that a
function does what is expected of it, not push to production and find out I forgot to regression test something
manually. The Discord API provides too much functionality to be able to feasibly manually test every corner before
every commit. Aiming for testability also enables this API to be kept as tidy as possible internally, as each testable
unit is forced to be easily mockable or able to be extracted and used independently of the rest of the API. Think LEGO,
but it is Python code. The same is said for security testing, documentation generation, and releasing. The entire
deployment pipeline is automated as much as possible to keep the updates flowing and to prevent human error wherever
possible.

The final aim is for maintainability. This API attempts to be as documented and expandable as possible internally. If
something isn't right and you have some understanding of Python, hopefully you should be able to pick it up and tweak it
to solve your use case, rather than fighting inflexible internal abstractions that hide the information you need.

## What is this API **not**?

This API is **not** designed to be backwards compatible with ye olde Python version. Python gets new features for a
reason: that reason is optimisation, usability, and readability. If you want to use a version of Python that is three
major versions behind the most recent major stable release, this is not for you.

It is **not** a self-botting API. Go elsewhere. Unlike other APIs, the aim is to not provide the user with tools
clearly implemented for the sole purpose of exploiting Discord and breaching their ToS. It screws up your experience of
their platform and it screws up my experience of their platform, so this API will not encourage it in any way.

It is **not** an OAuth2 API wrapper for Discord. Maybe some day.

It currently is **not** able to provide voice functionality. Again, this may be added in the future.

## FAQ

### Contributing to Hikari

[View the contributing guide!](https://gitlab.com/nekokatt/hikari/-/wiki_pages/Contributing)
