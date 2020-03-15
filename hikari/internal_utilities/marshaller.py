#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
This is an internal marshalling utility used by internal API components.

Warnings
--------
You should not change anything in this file, if you do, you will likely get
unexpected behaviour elsewhere.
"""

import typing

import attr

from hikari.internal_utilities import assertions

_RAW_NAME_ATTR = __name__ + "_RAW_NAME"
_SERIALIZER_ATTR = __name__ + "_SERIALIZER"
_DESERIALIZER_ATTR = __name__ + "_DESERIALIZER"
_TRANSIENT_ATTR = __name__ + "_TRANSIENT"
_OPTIONAL_ATTR = __name__ + "_OPTIONAL"

MARSHALLER_META_ATTR = "__hikari_marshaller_meta_attr__"

T_contra = typing.TypeVar("T_contra", contravariant=True)


def attrib(
    *,
    # Mandatory! We do not want to rely on type annotations alone, as they will
    # break if we use __future__.annotations anywhere. If we relied on the
    # field type, that would work, but attrs doesn't let us supply field.type
    # as an attr.ib() kwargs AND use type hints at the same time, and without
    # type hints, the library loses the ability to be type checked properly
    # anymore, so we have to pass this explicitly regardless.
    deserializer: typing.Callable[[typing.Any], typing.Any],
    raw_name: typing.Optional[str] = None,
    transient: bool = False,
    optional: bool = False,
    serializer: typing.Callable[[typing.Any], typing.Any] = None,
    **kwargs,
):
    metadata = kwargs.setdefault("metadata", {})
    metadata[_RAW_NAME_ATTR] = raw_name
    metadata[_SERIALIZER_ATTR] = serializer
    metadata[_DESERIALIZER_ATTR] = deserializer
    metadata[_TRANSIENT_ATTR] = transient
    metadata[_OPTIONAL_ATTR] = optional
    return attr.ib(**kwargs)


def _no_deserialize(name):
    def error(*_, **__) -> typing.NoReturn:
        raise TypeError(f"Field {name} does not support deserialization")

    return error


def _no_serialize(name):
    def error(*_, **__) -> typing.NoReturn:
        raise TypeError(f"Field {name} does not support serialization")

    return error


class _AttributeDescriptor:
    __slots__ = ("raw_name", "field_name", "is_optional", "is_transient", "deserializer", "serializer")

    def __init__(
        self,
        raw_name: str,
        field_name: str,
        is_optional: bool,
        is_transient: bool,
        deserializer: typing.Callable[[typing.Any], typing.Any],
        serializer: typing.Callable[[typing.Any], typing.Any],
    ) -> None:
        self.raw_name = raw_name
        self.field_name = field_name
        self.is_optional = is_optional
        self.is_transient = is_transient  # Do not serialize
        self.deserializer = deserializer
        self.serializer = serializer


class _EntityDescriptor:
    __slots__ = ("entity_type", "attribs")

    def __init__(self, entity_type: typing.Type, attribs: typing.Collection[_AttributeDescriptor],) -> None:
        self.entity_type = entity_type
        self.attribs = tuple(attribs)


def _construct_attribute_descriptor(field: attr.Attribute) -> _AttributeDescriptor:
    raw_name = typing.cast(str, field.metadata.get(_RAW_NAME_ATTR) or field.name)
    field_name = typing.cast(str, field.name)

    return _AttributeDescriptor(
        raw_name=raw_name,
        field_name=field_name,
        is_optional=field.metadata[_OPTIONAL_ATTR],
        is_transient=field.metadata[_TRANSIENT_ATTR],
        deserializer=field.metadata[_DESERIALIZER_ATTR],
        serializer=field.metadata[_SERIALIZER_ATTR] or _no_serialize(field_name),
    )


def _construct_entity_descriptor(entity: typing.Any):
    assertions.assert_that(
        hasattr(entity, "__attrs_attrs__"),
        f"{entity.__module__}.{entity.__qualname__} is not an attr class",
        error_type=TypeError,
    )

    return _EntityDescriptor(entity, [_construct_attribute_descriptor(field) for field in attr.fields(entity)])


class HikariEntityMarshaller:
    """
    This is a global marshaller helper that can help to deserialize and
    serialize any internal components that are decorated with the
    :obj:`marshaller_aware` decorator, and that are :mod:`attr` classes.
    """

    def __init__(self):
        self._registered_entities: typing.MutableMapping[typing.Type, _EntityDescriptor] = {}

    def register(self, cls):
        entity_descriptor = _construct_entity_descriptor(cls)
        self._registered_entities[cls] = entity_descriptor
        return cls

    def deserialize(self, raw_data: typing.Mapping[str, typing.Any], target_type: typing.Type[T_contra]) -> T_contra:
        """Deserialize a given raw data item into the target type.

        Parameters
        ----------
        raw_data
            The raw data to deserialize.
        target_type
            The type to deserialize to.

        Returns
        -------
        The deserialized instance.
        """
        try:
            descriptor = self._registered_entities[target_type]
        except KeyError:
            raise TypeError(f"No registered entity {target_type.__module__}.{target_type.__qualname__}")

        kwargs = {}

        for a in descriptor.attribs:
            if a.raw_name not in raw_data:
                if not a.is_optional:
                    raise ValueError(
                        f"Non-optional field {a.field_name} (from raw {a.raw_name}) is not specified in the input "
                        f"payload\n\n{raw_data}"
                    )
                kwargs[a.field_name] = None
                continue

            try:
                data = raw_data[a.raw_name]
                # Use the deserializer if it is there, otherwise use the constructor of the type of the field.
                kwargs[a.field_name] = a.deserializer(data) if a.deserializer else data
            except Exception:
                raise ValueError(
                    "Failed to deserialize data to instance of "
                    f"{target_type.__module__}.{target_type.__qualname__} because marshalling failed on "
                    f"attribute {a.field_name}"
                )

        return target_type(**kwargs)

    def serialize(self, obj: typing.Optional[typing.Any]) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Serialize a given entity into a raw data item.

        Parameters
        ----------
        obj
            The entity to serialize.

        Returns
        -------
        The serialized raw data item.
        """
        if obj is None:
            return None

        input_type = type(obj)

        try:
            descriptor = self._registered_entities[input_type]
        except KeyError:
            raise TypeError(f"No registered entity {input_type.__module__}.{input_type.__qualname__}")

        raw_data = {}

        for a in descriptor.attribs:
            if a.is_transient:
                continue
            value = getattr(obj, a.field_name)
            raw_data[a.raw_name] = a.serializer(value) or repr(value)

        return raw_data


HIKARI_ENTITY_MARSHALLER = HikariEntityMarshaller()


def attrs(**kwargs):
    assertions.assert_that(not kwargs.get("auto_attribs"), "Cannot use auto attribs here")
    kwargs["auto_attribs"] = False
    return lambda cls: kwargs.pop("marshaller", HIKARI_ENTITY_MARSHALLER).register(attr.s(**kwargs)(cls))
