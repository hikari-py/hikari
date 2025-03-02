# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""A simple bot to demonstrate how to use rillrate with hikari to make a web dashboard for the bot.

Just visit `http://localhost:6361/ui/` to explore your dashboard!
"""

from __future__ import annotations

import logging
import os

import rillrate
from rillrate import prime as rr_prime

import hikari

PREFIX = ","

# Name used to group dashboards.
# You could have multiple packages for different applications, such as a package for the bot
# dashboards, and another package for a web server running alongside the bot.
PACKAGE = "Rillrate Example"
# Dashboards are a part inside of package, they can be used to group different types of
# dashboards that you may want to use, like a dashboard for system status, another dashboard
# for cache status, and another one to configure features or trigger actions on the bot.
DASHBOARD = "Control Panel"
# These are menus inside the dashboard, you can use them to group specific sets
# of data inside the same dashboard.
GROUP_CONFIG = "1 - Example"
# All the 3 configurable namespaces are sorted alphabetically.


# Class with all our dashboard logic
class RillRateDashboard:
    """Global data shared across the entire bot, used to store dashboard values."""

    __slots__ = ("logger", "value", "selector", "slider")

    def __init__(self) -> None:
        self.logger = logging.getLogger("dashboard")
        self.value = 0

        # Install rillrate - Spins up the rillrate service in a separate thread, making it non-blocking :)
        rillrate.install()

        # Register the dashboard objects
        dummy_values = [str(i) for i in range(0, 256 + 1, 32)]
        self.selector = rr_prime.Selector(
            f"{PACKAGE}.{DASHBOARD}.{GROUP_CONFIG}.Selector", label="Choose!", options=dummy_values
        )
        self.slider = rr_prime.Slider(
            f"{PACKAGE}.{DASHBOARD}.{GROUP_CONFIG}.Slider", label="More fine grain control", min=0, max=256, step=2
        )

        # Add sync callbacks - This way we tell rillrate what functions to call when a sync event occurs
        self.selector.sync_callback(self._selector_callback)
        self.slider.sync_callback(self._slider_callback)

    def _selector_callback(self, activity: rillrate.Activity, action: rillrate.Action) -> None:
        self.logger.info("Selector activity: %s | action = %s", activity, action)

        if action is not None:
            value = int(action.value)
            self.logger.info("Selected: %s", value)

            # Update the slider too, so they show the same value.
            self.slider.apply(value)

            # Overwrite the current stored value on the global data with the new selected value.
            self.value = value

    def _slider_callback(self, activity: rillrate.Activity, action: rillrate.Action) -> None:
        self.logger.info("Slider activity: %s | action = %s", activity, action)

        if action is not None:
            value = int(action.value)
            self.logger.info("Slided to: %s", value)

            # Update the selector too, so they show the same value.
            # It is important to note that since not all values are present in the selector, it might be empty sometimes
            self.selector.apply(str(value))

            # Overwrite the current stored value on the global data with the new selected value.
            self.value = value


bot = hikari.GatewayBot(token=os.environ["BOT_TOKEN"])
dashboard = RillRateDashboard()


def is_command(cmd_name: str, content: str) -> bool:
    """Check if the message sent is a valid command."""
    return content == f"{PREFIX}{cmd_name}"


@bot.listen()
async def message(event: hikari.GuildMessageCreateEvent) -> None:
    """Listen for messages being created."""
    if not event.is_human or not event.content:
        return

    # Command Framework 101 :D
    if event.content.startswith(PREFIX):
        if is_command("ping", event.content):
            await event.message.respond("Pong!")
        elif is_command("value", event.content):
            await event.message.respond(f"Current value: {dashboard.value}")


bot.run()
