# -*- coding: utf-8 -*-
# This code is licended under the WTFPL license.
"""A simple bot to demonstrate how to use rillrate with hikari to make a web dashboard for the bot.

Just connect to `http://localhost:6361/ui/` to explore your dashboard!
"""
import logging
import os
from typing import Any

import rillrate
from rillrate import prime as rr_prime

import hikari

PREFIX = ","

# Name used to group dashboards.
# You could have multiple packages for different applications, such as a package for the bot
# dashboards, and another package for a web server running alongside the bot.
PACKAGE = "Package"
# Dashboards are a part inside of package, they can be used to group different types of
# dashboards that you may want to use, like a dashboard for system status, another dashboard
# for cache status, and another one to configure features or trigger actions on the bot.
DASHBOARD = "Dashboard"
# This are menus inside the dashboard, you can use them to group specific sets
# of data inside the same dashboard.
GROUP_CONFIG = "1 - Config"
# All of the 3 configurable namescapes are sorted alphabetically.


def is_command(cmd_name: str, content: str) -> bool:
    """Check if the message sent is a valid command."""
    return content.startswith(f"{PREFIX}{cmd_name}")


# This is how I do global data on the library, as Bot is generally accessible everywhere, so
# it's the best you can do to put the global data in there.
# In this case, I'll use this to store the values modifiable by the dashboard.
class Data:
    """Global data shared across the entire bot, used to store dashboard values."""

    def __init__(self) -> None:
        self.value = 0


class Bot(hikari.GatewayBot):
    """Just implementing the data to the Bot."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.data = Data()


# Startup the dashboard.
# To see the dashboard, go to http://localhost:6361/ui/
rillrate.install()
bot = Bot(token=os.environ["BOT_TOKEN"])


values = list(range(0, 256 + 1, 32))

selector = rr_prime.Selector(f"{PACKAGE}.{DASHBOARD}.{GROUP_CONFIG}.Selector", label="Choose!", options=values)
slider = rr_prime.Slider(
    f"{PACKAGE}.{DASHBOARD}.{GROUP_CONFIG}.Slider", label="More fine grain control", min=0, max=256, step=2
)


def _selector_callback(activity: rillrate.Activity, action: rillrate.Action) -> None:
    logging.info("Selector activity: %s | action = %s", activity, action)

    if action is not None:
        logging.info("Selected: %s", action.value)

        # Update both the selector and slider, so they show with the same value.
        selector.apply(action.value)
        slider.apply(float(action.value))

        # Overwrite the current stored value on the global data with the new selected value.
        bot.data.value = int(action.value)


def _slider_callback(activity: rillrate.Activity, action: rillrate.Action) -> None:
    logging.info("Slider activity: %s | action = %s", activity, action)

    if action is not None:
        logging.info("Slided: %f", action.value)

        slider.apply(action.value)
        selector.apply(str(int(action.value)))

        # Overwrite the current stored value on the global data with the new selected value.
        bot.data.value = int(action.value)


selector.sync_callback(_selector_callback)
slider.sync_callback(_slider_callback)


@bot.listen()
async def message(event: hikari.GuildMessageCreateEvent) -> None:
    """Listen for messages being created."""
    if event.is_bot or not event.content:
        return

    # Command Framework 101 :D
    if is_command("ping", event.content):
        await event.message.respond("Ping?")
    elif is_command("value", event.content):
        await event.message.respond(f"Current value: {bot.data.value}")


bot.run()
