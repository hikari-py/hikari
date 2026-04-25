# Hikari Examples - A collection of examples for Hikari.
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
"""Test bot showing off modal and message components.

Slash commands registered:
* /modal-text          - modal with a Label-wrapped text input
* /modal-multi         - modal with Label-wrapped text input, text select, and file upload
* /message-components  - message with container, section + button accessory,
                         action rows of buttons, text/user/role/channel select menus,
                         text display, media gallery and separators
"""

from __future__ import annotations

import os
import typing

import hikari
from hikari.impl import special_endpoints as se

bot = hikari.GatewayBot(token=os.environ["BOT_TOKEN"])

# Set to a guild ID for instant command updates, or hikari.UNDEFINED for global.
COMMAND_GUILD_ID = hikari.UNDEFINED

THUMBNAIL_URL = "https://cdn.discordapp.com/embed/avatars/0.png"
GALLERY_URLS = (
    "https://cdn.discordapp.com/embed/avatars/1.png",
    "https://cdn.discordapp.com/embed/avatars/2.png",
    "https://cdn.discordapp.com/embed/avatars/3.png",
)


@bot.listen()
async def register_commands(_: hikari.StartingEvent) -> None:
    application = await bot.rest.fetch_application()
    commands = [
        bot.rest.slash_command_builder("modal-text", "Open a single text input modal."),
        bot.rest.slash_command_builder("modal-multi", "Open a modal with text, select, and file upload."),
        bot.rest.slash_command_builder("message-components", "Send a message using message components."),
    ]
    await bot.rest.set_application_commands(application=application.id, commands=commands, guild=COMMAND_GUILD_ID)


def _build_text_modal_components() -> list[se.LabelComponentBuilder]:
    return [
        se.LabelComponentBuilder(
            label="What's your favourite colour?",
            description="Free-form short answer.",
            component=se.TextInputBuilder(
                custom_id="favourite-colour",
                style=hikari.TextInputStyle.SHORT,
                placeholder="e.g. blurple",
                required=True,
                max_length=40,
            ),
        )
    ]


def _build_multi_modal_components() -> list[se.LabelComponentBuilder]:
    text_label = se.LabelComponentBuilder(
        label="Bug summary",
        description="Briefly describe the bug.",
        component=se.TextInputBuilder(
            custom_id="bug-summary", style=hikari.TextInputStyle.PARAGRAPH, required=True, max_length=1000
        ),
    )

    severity_select: se.TextSelectMenuBuilder[typing.NoReturn] = se.TextSelectMenuBuilder(
        custom_id="severity", placeholder="Pick severity", min_values=1, max_values=1
    )
    for label, value in (("Low", "low"), ("Medium", "medium"), ("High", "high"), ("Critical", "critical")):
        severity_select.add_option(label, value)
    severity_label = se.LabelComponentBuilder(label="Severity", component=severity_select)

    upload_label = se.LabelComponentBuilder(
        label="Attachments",
        description="Upload up to 3 supporting files.",
        component=se.FileUploadComponentBuilder(custom_id="attachments", min_values=0, max_values=3, is_required=False),
    )

    return [text_label, severity_label, upload_label]


def _build_button_action_row() -> se.MessageActionRowBuilder:
    row = se.MessageActionRowBuilder()
    row.add_interactive_button(hikari.ButtonStyle.PRIMARY, "v2:btn:primary", label="Primary", emoji="\N{ROCKET}")
    row.add_interactive_button(hikari.ButtonStyle.SUCCESS, "v2:btn:success", label="Success")
    row.add_interactive_button(hikari.ButtonStyle.DANGER, "v2:btn:danger", label="Danger")
    row.add_link_button("https://hikari-py.dev", label="Docs")
    return row


def _build_text_select_row() -> se.MessageActionRowBuilder:
    # Exactly one flavour required.
    row = se.MessageActionRowBuilder()
    menu = row.add_text_menu("v2:sel:flavour", placeholder="Pick a flavour", min_values=1, max_values=1)
    for label, value, emoji in (
        ("Vanilla", "vanilla", "\N{ICE CREAM}"),
        ("Chocolate", "chocolate", "\N{CHOCOLATE BAR}"),
        ("Strawberry", "strawberry", "\N{STRAWBERRY}"),
    ):
        menu.add_option(label, value, emoji=emoji)
    return row


def _build_entity_select_row() -> se.MessageActionRowBuilder:
    # 2 to 5 users — multi-select with a floor.
    row = se.MessageActionRowBuilder()
    row.add_select_menu(
        hikari.ComponentType.USER_SELECT_MENU, "v2:sel:user", placeholder="Pick 2-5 users", min_values=2, max_values=5
    )
    return row


def _build_channel_select_row() -> se.MessageActionRowBuilder:
    # Optional, up to 3 channels — min 0 lets the user clear their pick.
    row = se.MessageActionRowBuilder()
    row.add_channel_menu(
        "v2:sel:channel",
        placeholder="Pick up to 3 text channels (optional)",
        channel_types=[hikari.ChannelType.GUILD_TEXT, hikari.ChannelType.GUILD_NEWS],
        min_values=0,
        max_values=3,
    )
    return row


def _build_v2_message() -> list[hikari.api.ComponentBuilder]:
    container = se.ContainerComponentBuilder(accent_color=hikari.Color(0x5865F2))
    container.add_text_display("# Components v2 demo\nA single message exercising every layout primitive.")
    container.add_component(
        se.SectionComponentBuilder(
            components=[se.TextDisplayComponentBuilder(content="Section body with a button accessory.")],
            accessory=se.InteractiveButtonBuilder(
                style=hikari.ButtonStyle.SECONDARY, custom_id="v2:btn:section", label="Click me"
            ),
        )
    )
    container.add_separator(divider=True, spacing=hikari.SpacingType.LARGE)
    container.add_text_display("**Inline buttons:**")
    container.add_component(_build_button_action_row())
    container.add_separator(divider=False, spacing=hikari.SpacingType.SMALL)
    container.add_text_display("**Inline selects:**")
    container.add_component(_build_text_select_row())
    container.add_component(_build_entity_select_row())
    container.add_component(_build_channel_select_row())
    container.add_separator(divider=True, spacing=hikari.SpacingType.LARGE)
    container.add_text_display("**Media gallery:**")
    container.add_media_gallery(items=[se.MediaGalleryItemBuilder(media=url) for url in GALLERY_URLS])
    container.add_text_display("Footer line inside the container.")

    # Top-level section with a thumbnail accessory, outside the container.
    standalone_section = se.SectionComponentBuilder(
        components=[se.TextDisplayComponentBuilder(content="Top-level section with a thumbnail accessory.")],
        accessory=se.ThumbnailComponentBuilder(media=THUMBNAIL_URL, description="Default avatar"),
    )
    return [container, standalone_section]


@bot.listen()
async def on_command(event: hikari.CommandInteractionCreateEvent) -> None:
    name = event.interaction.command_name
    if name == "modal-text":
        await event.interaction.create_modal_response(
            title="Quick question", custom_id="modal:text", components=_build_text_modal_components()
        )
    elif name == "modal-multi":
        await event.interaction.create_modal_response(
            title="Bug report", custom_id="modal:multi", components=_build_multi_modal_components()
        )
    elif name == "message-components":
        await event.interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            components=_build_v2_message(),
            flags=hikari.MessageFlag.IS_COMPONENTS_V2,
        )


def _format_modal_submission(interaction: hikari.ModalInteraction) -> str:
    lines: list[str] = [f"**Custom ID:** `{interaction.custom_id}`"]
    for top in interaction.components:
        if isinstance(top, hikari.LabelComponent):
            child = top.component
            if isinstance(child, hikari.TextInputComponent):
                lines.append(f"- text `{child.custom_id}`: `{child.value!r}`")
            elif isinstance(child, hikari.FileUploadComponent):
                ids = ", ".join(str(s) for s in child.values) or "(none)"
                lines.append(f"- file_upload `{child.custom_id}`: {ids}")
            else:
                # Select menu - values land in resolved or are inlined depending on Discord behaviour.
                lines.append(f"- select `{child.custom_id}` (type {child.type})")
        elif isinstance(top, hikari.ActionRowComponent):
            for sub in top.components:
                if isinstance(sub, hikari.TextInputComponent):
                    lines.append(f"- legacy text `{sub.custom_id}`: `{sub.value!r}`")

    if interaction.resolved and interaction.resolved.attachments:
        lines.append("**Resolved attachments:**")
        for attachment in interaction.resolved.attachments.values():
            lines.append(f"- {attachment.filename} ({attachment.size} B) {attachment.url}")

    return "\n".join(lines)


@bot.listen()
async def on_modal(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.ModalInteraction):
        return
    await event.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE,
        _format_modal_submission(event.interaction),
        flags=hikari.MessageFlag.EPHEMERAL,
    )


def _format_component_interaction(interaction: hikari.ComponentInteraction) -> str:
    cid = interaction.custom_id
    if interaction.component_type == hikari.ComponentType.BUTTON:
        return f"Button `{cid}` clicked."

    values = list(interaction.values)
    resolved = interaction.resolved
    if interaction.component_type == hikari.ComponentType.USER_SELECT_MENU and resolved:
        names = [resolved.users[hikari.Snowflake(v)].username for v in values if hikari.Snowflake(v) in resolved.users]
        return f"User select `{cid}`: {', '.join(names) or values}"
    if interaction.component_type == hikari.ComponentType.CHANNEL_SELECT_MENU and resolved:
        names = [
            resolved.channels[hikari.Snowflake(v)].name or str(v)
            for v in values
            if hikari.Snowflake(v) in resolved.channels
        ]
        return f"Channel select `{cid}`: {', '.join(names) or values}"

    return f"Select `{cid}` ({interaction.component_type}): {values}"


@bot.listen()
async def on_component(event: hikari.InteractionCreateEvent) -> None:
    if not isinstance(event.interaction, hikari.ComponentInteraction):
        return
    if not event.interaction.custom_id.startswith("v2:"):
        return
    await event.interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE,
        _format_component_interaction(event.interaction),
        flags=hikari.MessageFlag.EPHEMERAL,
    )


bot.run()
