# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""A simple bot that opens modals from slash commands and echoes what was submitted."""

from __future__ import annotations

import os

import hikari

bot = hikari.GatewayBot(token=os.environ["BOT_TOKEN"])

# Set this to the guild to create the slash commands in.
# To create global commands, set to `hikari.UNDEFINED`.
COMMAND_GUILD_ID = 0


@bot.listen()
async def register_commands(_: hikari.StartingEvent) -> None:
    """Register the feedback and bug-report commands."""
    application = await bot.rest.fetch_application()

    commands = [
        bot.rest.slash_command_builder("feedback", "Open a short feedback form."),
        bot.rest.slash_command_builder("bug-report", "Open a bug report form with every modal component."),
    ]

    await bot.rest.set_application_commands(application=application.id, commands=commands, guild=COMMAND_GUILD_ID)


def build_feedback_modal() -> list[hikari.api.ComponentBuilder]:
    """Build a modal with a text input, a radio group and a checkbox."""
    colour = hikari.impl.LabelComponentBuilder(
        label="What's your favourite colour?",
        description="Free-form short answer.",
        component=hikari.impl.TextInputBuilder(custom_id="colour", placeholder="e.g. blurple", max_length=40),
    )

    source = hikari.impl.LabelComponentBuilder(
        label="How did you hear about us?",
        component=hikari.impl.RadioGroupBuilder(custom_id="source")
        .add_option("A friend", "friend")
        .add_option("Search engine", "search")
        .add_option("Somewhere else", "other", description="Tell us in the text field above."),
    )

    newsletter = hikari.impl.LabelComponentBuilder(
        label="Subscribe to updates", component=hikari.impl.CheckboxBuilder(custom_id="newsletter")
    )

    return [colour, source, newsletter]


def build_bug_report_modal() -> list[hikari.api.ComponentBuilder]:
    """Build a modal with a text display, text input, text select, checkbox group and file upload."""
    intro = hikari.impl.TextDisplayComponentBuilder(content="Fill in as much as you can. Only the summary is required.")

    summary = hikari.impl.LabelComponentBuilder(
        label="Bug summary",
        description="Briefly describe the bug.",
        component=hikari.impl.TextInputBuilder(
            custom_id="summary", style=hikari.TextInputStyle.PARAGRAPH, max_length=1000
        ),
    )

    severity = hikari.impl.LabelComponentBuilder(
        label="Severity",
        component=hikari.impl.TextSelectMenuBuilder(custom_id="severity", placeholder="Pick severity")
        .add_option("Low", "low")
        .add_option("Medium", "medium")
        .add_option("High", "high")
        .add_option("Critical", "critical"),
    )

    areas = hikari.impl.LabelComponentBuilder(
        label="Affected areas",
        description="Tick everything that applies.",
        component=hikari.impl.CheckboxGroupBuilder(
            custom_id="areas",
            options=[
                hikari.impl.GroupOptionBuilder("Gateway", "gateway"),
                hikari.impl.GroupOptionBuilder("REST", "rest"),
                hikari.impl.GroupOptionBuilder("Cache", "cache"),
                hikari.impl.GroupOptionBuilder("Docs", "docs"),
            ],
            min_values=0,
            is_required=False,
        ),
    )

    attachments = hikari.impl.LabelComponentBuilder(
        label="Attachments",
        description="Up to 3 screenshots or log files.",
        component=hikari.impl.FileUploadComponentBuilder(
            custom_id="attachments", min_values=0, max_values=3, is_required=False, file_types=["image", ".log", ".txt"]
        ),
    )

    return [intro, summary, severity, areas, attachments]


@bot.listen()
async def handle_commands(event: hikari.CommandInteractionCreateEvent) -> None:
    """Open the modal belonging to the executed slash command."""
    if event.interaction.command_name == "feedback":
        await event.interaction.create_modal_response(
            "Feedback", custom_id="feedback", components=build_feedback_modal()
        )

    elif event.interaction.command_name == "bug-report":
        await event.interaction.create_modal_response(
            "Bug report", custom_id="bug-report", components=build_bug_report_modal()
        )


def describe_component(component: hikari.ModalLabelComponentTypesT) -> str:
    """Describe the value a user submitted for a single label component."""
    if isinstance(component, hikari.ModalTextInputComponent):
        return f"text `{component.custom_id}`: {component.value!r}"

    if isinstance(component, hikari.ModalRadioGroupComponent):
        return f"radio group `{component.custom_id}`: {component.value or '(none)'}"

    if isinstance(component, hikari.ModalCheckboxComponent):
        return f"checkbox `{component.custom_id}`: {component.is_checked}"

    if isinstance(component, hikari.ModalFileUploadComponent):
        return f"file upload `{component.custom_id}`: {len(component.values)} file(s)"

    values = ", ".join(str(value) for value in component.values) or "(none)"
    return f"`{component.custom_id}`: {values}"


@bot.listen()
async def handle_modals(event: hikari.ModalInteractionCreateEvent) -> None:
    """Echo back what was submitted through a modal."""
    lines = [f"Submitted `{event.interaction.custom_id}`:"]

    lines.extend(
        f"- {describe_component(component.component)}"
        for component in event.interaction.components
        if isinstance(component, hikari.ModalLabelComponent)
    )

    if event.interaction.resolved and event.interaction.resolved.attachments:
        lines.extend(
            f"- {attachment.filename} ({attachment.size} B)"
            for attachment in event.interaction.resolved.attachments.values()
        )

    await event.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE, "\n".join(lines), flags=hikari.MessageFlag.EPHEMERAL
    )


bot.run()
