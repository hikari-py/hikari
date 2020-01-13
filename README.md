[![](https://img.shields.io/discord/574921006817476608.svg?logo=Discord&logoColor=white&label=discord)](https://discord.gg/HMnGbsv)
[![](https://img.shields.io/lgtm/alerts/gitlab/nekokatt/hikari)](https://lgtm.com/projects/gl/nekokatt/hikari)
[![](https://img.shields.io/lgtm/grade/python/gitlab/nekokatt/hikari)](https://lgtm.com/projects/gl/nekokatt/hikari?mode=tree)
[![](https://gitlab.com/nekokatt/hikari/badges/master/coverage.svg)](https://gitlab.com/nekokatt/hikari/pipelines)
[![](https://img.shields.io/gitlab/pipeline/nekokatt/hikari/master?label=ci%20(master)&logo=gitlab)](https://gitlab.com/nekokatt/hikari/pipelines)
[![](https://img.shields.io/gitlab/pipeline/nekokatt/hikari/staging?label=ci%20(staging)&logo=gitlab)](https://gitlab.com/nekokatt/hikari/pipelines)
[![](https://img.shields.io/website/https/nekokatt.gitlab.io/hikari.svg?down_color=red&down_message=not%20building&label=docs%20(master)&logo=gitlab&logoColor=white&up_message=up-to-date)](https://nekokatt.gitlab.io/hikari)
[![](https://img.shields.io/website/https/nekokatt.gitlab.io/hikari/staging.svg?down_color=red&down_message=not%20building&label=docs%20(staging)&logo=gitlab&logoColor=white&up_message=up-to-date)](https://nekokatt.gitlab.io/hikari/staging/)
[![](https://badgen.net/pypi/v/hikari)](https://pypi.org/project/hikari)
[![](https://badgen.net/pypi/license/hikari)](?)
[![](https://img.shields.io/pypi/implementation/hikari.svg)](?)
[![](https://img.shields.io/pypi/format/hikari.svg)](?)
[![](https://img.shields.io/pypi/dm/hikari)](?)
[![](https://img.shields.io/pypi/status/hikari)](?)
[![](https://img.shields.io/pypi/pyversions/hikari)](?)
[![](https://img.shields.io/badge/code%20style-black-000000.svg)](?)
[![](https://img.shields.io/sourcegraph/rrc/gitlab.com/nekokatt/hikari)](https://sourcegraph.com/gitlab.com/nekokatt/hikari)
[![](https://img.shields.io/static/v1?label=sourcegraph&message=view%20now!&color=blueviolet&logo=sourcegraph)](https://sourcegraph.com/gitlab.com/nekokatt/hikari)

# hikari

An opinionated Discord API for Python 3 and asyncio.

**THIS API IS CURRENTLY IN A PRE-ALPHA STAGE, SO NEW VERSIONS WILL CONTAIN BREAKING CHANGES WITHOUT A MINOR
VERSION INCREMENTATION. ALL FEATURES ARE PROVISIONAL AND CAN CHANGE AT ANY TIME UNTIL THIS API IS IN A USABLE 
STATE FOR A FULL FIRST RELEASE.**
 
 **[Please VISIT MY DISCORD](https://discord.gg/HMnGbsv) if you wish to receive progress updates or help out, any
 help and contribution is more than welcome :-)**
 
If you wish to explore the code in an online interactive viewer, you can use Sourcegraph on 
[master](https://sourcegraph.com/gitlab.com/nekokatt/hikari@master) and [staging](https://sourcegraph.com/gitlab.com/nekokatt/hikari@staging)
too!

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
function does what is expected of it to provide hard evidence that a build is not fundamentally broken before
deploying it.

The final aim is for maintainability. This API attempts to be as documented and expandable as possible internally. If
something isn't right and you have some understanding of Python, hopefully you should be able to pick it up and tweak it
to solve your use case, rather than fighting inflexible internal abstractions that hide the information you need.

## What is this API **not**?

This API is **not** for people using anything older than CPython 3.7. 

It currently is **not** able to provide voice functionality. Again, this may be added in the future.

## FAQ

### Contributing to Hikari

[View the contributing guide!](https://gitlab.com/nekokatt/hikari/wikis/Contributing)
