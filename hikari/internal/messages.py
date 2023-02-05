# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Utility functions used for managing messages on Discord."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("build_message_payload",)

import typing

from hikari import embeds as embeds_
from hikari import files
from hikari import undefined
from hikari.internal import data_binding

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import messages as messages_
    from hikari import snowflakes
    from hikari import users
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import special_endpoints

    class _AttachmentPayload(typing.TypedDict):
        filename: str
        id: int


def _extend_attachments(
    payloads: typing.List[_AttachmentPayload],
    to_upload: typing.Dict[int, files.Resource[typing.Any]],
    edit: bool,
    attachments: typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]],
) -> None:
    attachment_id = 0
    for attachment in attachments:
        if edit and isinstance(attachment, messages_.Attachment):
            payloads.append({"id": attachment.id, "filename": attachment.filename})

        else:
            resource = files.ensure_resource(attachment)
            to_upload[attachment_id] = resource
            payloads.append({"id": attachment_id, "filename": resource.filename})
            attachment_id += 1


def build_message_payload(
    entity_factory: entity_factory_.EntityFactory,
    /,
    *,
    content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
    attachments: undefined.UndefinedNoneOr[
        typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
    ] = undefined.UNDEFINED,
    components: undefined.UndefinedNoneOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
    embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
    flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
    tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    user_mentions: undefined.UndefinedOr[
        typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
    ] = undefined.UNDEFINED,
    role_mentions: undefined.UndefinedOr[
        typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
    ] = undefined.UNDEFINED,
    edit: bool = False,
) -> typing.Tuple[data_binding.JSONObjectBuilder, typing.Mapping[int, files.Resource[typing.Any]]]:
    """Create a message create/edit payload."""
    to_upload: typing.Dict[int, files.Resource[typing.Any]] = {}
    attachment_payloads: typing.List[_AttachmentPayload] = []
    if attachments:
        _extend_attachments(attachment_payloads, to_upload, edit, attachments)

    serialized_components: undefined.UndefinedOr[typing.List[data_binding.JSONObject]] = undefined.UNDEFINED
    if components is not undefined.UNDEFINED:
        if components is not None:
            serialized_components = [component.build() for component in components]
        else:
            serialized_components = []

    serialized_embeds: undefined.UndefinedOr[data_binding.JSONArray] = undefined.UNDEFINED
    if embeds is not undefined.UNDEFINED:
        serialized_embeds = []
        if embeds is not None:
            for e in embeds:
                embed_payload, embed_attachments = entity_factory.serialize_embed(e)
                _extend_attachments(attachment_payloads, to_upload, edit, embed_attachments)
                serialized_embeds.append(embed_payload)

    body = data_binding.JSONObjectBuilder()
    body.put("content", content, conversion=lambda v: v if v is None else str(v))
    body.put("tts", tts)
    body.put("flags", flags)
    body.put("embeds", serialized_embeds)
    body.put("components", serialized_components)

    if not edit or not undefined.all_undefined(mentions_everyone, mentions_reply, user_mentions, role_mentions):
        parsed_mentions: typing.List[str] = []
        allowed_mentions: typing.Dict[str, typing.Any] = {"parse": parsed_mentions}

        if mentions_everyone is True:
            parsed_mentions.append("everyone")

        if mentions_reply is True:
            allowed_mentions["replied_user"] = True

        if user_mentions is True:
            parsed_mentions.append("users")
        elif isinstance(user_mentions, typing.Collection):
            # Duplicates will cause Discord to error.
            ids = {str(int(u)) for u in user_mentions}
            allowed_mentions["users"] = list(ids)

        if role_mentions is True:
            parsed_mentions.append("roles")
        elif isinstance(role_mentions, typing.Collection):
            # Duplicates will cause Discord to error.
            ids = {str(int(r)) for r in role_mentions}
            allowed_mentions["roles"] = list(ids)

        body.put("allowed_mentions", allowed_mentions)

    if attachment_payloads:
        body.put("attachments", attachment_payloads)

    elif attachments is not undefined.UNDEFINED:
        body.put("attachments", None)

    return body, to_upload


def build_form_builder(
    to_upload: typing.Mapping[int, files.Resource[typing.Any]], /
) -> data_binding.URLEncodedFormBuilder:
    """Create a `hikari.data_binding.URLEncodedFormBuidder` from a list of attachments to upload."""
    form_builder = data_binding.URLEncodedFormBuilder()

    for attachment_id, resource in to_upload.items():
        form_builder.add_resource(f"files[{attachment_id}]", resource)

    return form_builder
