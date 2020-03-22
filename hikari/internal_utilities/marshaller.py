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
"""This is an internal marshalling utility used by internal API components.

Warnings
--------
You should not change anything in this file, if you do, you will likely get
unexpected behaviour elsewhere.
"""
__all__ = [
    "RAISE",
    "dereference_handle",
    "attrib",
    "attrs",
    "HIKARI_ENTITY_MARSHALLER",
    "HikariEntityMarshaller",
]

import importlib
import typing
import weakref

import attr

from hikari.internal_utilities import assertions

_RAW_NAME_ATTR = __name__ + "_RAW_NAME"
_SERIALIZER_ATTR = __name__ + "_SERIALIZER"
_DESERIALIZER_ATTR = __name__ + "_DESERIALIZER"
_TRANSIENT_ATTR = __name__ + "_TRANSIENT"
_IF_UNDEFINED = __name__ + "IF_UNDEFINED"
_IF_NONE = __name__ + "_IF_NONE"

MARSHALLER_META_ATTR = "__hikari_marshaller_meta_attr__"

RAISE = object()

EntityT = typing.TypeVar("EntityT", contravariant=True)


def dereference_handle(handle_string: str) -> typing.Any:
    """Parse a given handle string into an object reference.

    Parameters
    ----------
    handle_string : :obj:`str`
        The handle to the object to refer to. This is in the format
        ``fully.qualified.module.name#object.attribute``. If no ``#`` is
        input, then the reference will be made to the module itself.

    Returns
    -------
    :obj:`typing.Any`
        The thing that is referred to from this reference.

    Examples
    --------
    ``"collections#deque"``:
        Refers to :obj:`collections.deque`
    ``"asyncio.tasks#Task"``:
        Refers to :obj:`asyncio.tasks.Task`
    ``"hikari.net"``:
        Refers to :obj:`hikari.net`
    ``"foo.bar#baz.bork.qux"``:
        Would refer to a theoretical ``qux`` attribute on a ``bork``
        attribute on a ``baz`` object in the ``foo.bar`` module.
    """
    if "#" not in handle_string:
        module, attribute_names = handle_string, ()
    else:
        module, _, attribute_string = handle_string.partition("#")
        attribute_names = attribute_string.split(".")

    obj = importlib.import_module(module)
    for attr_name in attribute_names:
        obj = getattr(obj, attr_name)

    return weakref.proxy(obj)


def attrib(
    *,
    # Mandatory! We do not want to rely on type annotations alone, as they will
    # break if we use __future__.annotations anywhere. If we relied on the
    # field type, that would work, but attrs doesn't let us supply field.type
    # as an attr.ib() kwargs AND use type hints at the same time, and without
    # type hints, the library loses the ability to be type checked properly
    # anymore, so we have to pass this explicitly regardless.
    deserializer: typing.Callable[[typing.Any], typing.Any],
    if_none: typing.Union[typing.Callable[..., typing.Any], None, type(RAISE)] = RAISE,
    if_undefined: typing.Union[typing.Callable[..., typing.Any], None, type(RAISE)] = RAISE,
    raw_name: typing.Optional[str] = None,
    transient: bool = False,
    serializer: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None,
    **kwargs,
) -> typing.Any:
    """Create an :func:`attr.ib` with marshaller metadata attached.

    Parameters
    ----------
    deserializer : :obj:`typing.Callable` [ [ :obj:`typing.Any` ], :obj:`typing.Any` ]
        The deserializer to use to deserialize raw elements.
    raw_name : :obj:`str`, optional
        The raw name of the element in its raw serialized form. If not provided,
        then this will use the field's default name later.
    transient : :obj:`bool`
        If ``True``, the field is marked as transient, meaning it will not be
        serialized. Defaults to ``False``.
    if_none : :obj:`typing.Union` [ :obj:`typing.Callable` [ ... , :obj:`typing.Any` ], :obj:`None` ], optional
        Either a default factory function called to get the default for when
        this field is ``None`` or ``None`` to specify that this should default
        to ``None``. Will raise an exception when ``None`` is received for this
        field later if this isn't specified.
    if_undefined : :obj:`typing.Union` [ :obj:`typing.Callable` [  ... , :obj:`typing.Any` ], :obj:`None` ], optional
        Either a default factory function called to get the default for when
        this field isn't defined or ``None`` to specify that this should default
        to ``None``. Will raise an exception when this field is undefined later
        on if this isn't specified.
    serializer : :obj:`typing.Callable` [ [ :obj:`typing.Any` ], :obj:`typing.Any` ], optional
        The serializer to use. If not specified, then serializing the entire
        class that this attribute is in will trigger a :obj:`TypeError`
        later.
    **kwargs :
        Any kwargs to pass to :func:`attr.ib`.

    Returns
    -------
    :obj:`typing.Any`
        The result of :func:`attr.ib` internally being called with additional
        metadata.
    """
    # Sphinx decides to be really awkward and inject the wrong default values
    # by default. Not helpful when it documents non-optional shit as defaulting
    # to None. Hack to fix this seems to be to turn on autodoc's
    # typing.TYPE_CHECKING mode, and then if that is enabled, always return
    # some dummy class that has a repr that returns a literal "..." string.
    if typing.TYPE_CHECKING:
        return type("Literal", (), {"__repr__": lambda *_: "..."})()

    metadata = kwargs.pop("metadata", {})
    metadata[_RAW_NAME_ATTR] = raw_name
    metadata[_SERIALIZER_ATTR] = serializer
    metadata[_DESERIALIZER_ATTR] = deserializer
    metadata[_IF_NONE] = if_none
    metadata[_IF_UNDEFINED] = if_undefined
    metadata[_TRANSIENT_ATTR] = transient

    return attr.ib(**kwargs, metadata=metadata)


def _no_serialize(name):
    def error(*_, **__) -> typing.NoReturn:
        raise TypeError(f"Field {name} does not support serialization")

    return error


class _AttributeDescriptor:
    __slots__ = ("raw_name", "field_name", "if_none", "if_undefined", "is_transient", "deserializer", "serializer")

    def __init__(
        self,
        raw_name: str,
        field_name: str,
        if_none: typing.Callable[..., typing.Any],
        if_undefined: typing.Callable[..., typing.Any],
        is_transient: bool,
        deserializer: typing.Callable[[typing.Any], typing.Any],
        serializer: typing.Callable[[typing.Any], typing.Any],
    ) -> None:
        self.raw_name = raw_name
        self.field_name = field_name
        self.if_none = if_none
        self.if_undefined = if_undefined
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
        if_none=field.metadata[_IF_NONE],
        if_undefined=field.metadata[_IF_UNDEFINED],
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
    """This is a global marshaller helper that can help to deserialize and
    serialize any internal components that are decorated with the
    :obj:`attrs` decorator, and that are :mod:`attr` classes using fields
    with the :obj:`attrib` function call descriptor.
    """

    def __init__(self) -> None:
        self._registered_entities: typing.MutableMapping[typing.Type, _EntityDescriptor] = {}

    def register(self, cls: typing.Type[EntityT]) -> typing.Type[EntityT]:
        """Registers an attrs type for fast future deserialization.

        Parameters
        ----------
        cls : :obj:`typing.Type` [ :obj:`typing.Any` ]
            The type to register.

        Returns
        -------
        :obj:`typing.Type` [ :obj:`typing.Any` ]
            The input argument. This enables this to be used as a decorator if
            desired.

        Raises
        ------
        :obj:`TypeError`
            If the class is not an :mod:`attrs` class.
        """
        entity_descriptor = _construct_entity_descriptor(cls)
        self._registered_entities[cls] = entity_descriptor
        return cls

    def deserialize(self, raw_data: typing.Mapping[str, typing.Any], target_type: typing.Type[EntityT]) -> EntityT:
        """Deserialize a given raw data item into the target type.

        Parameters
        ----------
        raw_data : :obj:`typing.Mapping` [ :obj:`str`, :obj:`typing.Any` ]
            The raw data to deserialize.
        target_type : :obj:`typing.Type` [ :obj:`typing.Any` ]
            The type to deserialize to.

        Returns
        -------
        :obj:`typing.Any`
            The deserialized instance.

        Raises
        ------
        :obj:`LookupError`
            If the entity is not registered.
        :obj:`AttributeError`
            If the field is not optional, but the field was not present in the
            raw payload, or it was present, but it was assigned `None`.
        :obj:`TypeError`
            If the deserialization call failed for some reason.
        """
        try:
            descriptor = self._registered_entities[target_type]
        except KeyError:
            raise LookupError(f"No registered entity {target_type.__module__}.{target_type.__qualname__}")

        kwargs = {}

        for a in descriptor.attribs:
            if a.raw_name not in raw_data:
                if a.if_undefined is RAISE:
                    raise AttributeError(
                        f"Required field {a.field_name} (from raw {a.raw_name}) is not specified in the input "
                        f"payload\n\n{raw_data}"
                    )
                elif a.if_undefined:
                    kwargs[a.field_name] = a.if_undefined()
                else:
                    kwargs[a.field_name] = None
                continue
            elif (data := raw_data[a.raw_name]) is None:
                if a.if_none is RAISE:
                    raise AttributeError(
                        f"Non-nullable field {a.field_name} (from raw {a.raw_name}) is `None` in the input "
                        f"payload\n\n{raw_data}"
                    )
                elif a.if_none:
                    kwargs[a.field_name] = a.if_none()
                else:
                    kwargs[a.field_name] = None
                continue

            try:
                # Use the deserializer if it is there, otherwise use the constructor of the type of the field.
                kwargs[a.field_name] = a.deserializer(data) if a.deserializer else data
            except Exception as exc:
                raise TypeError(
                    "Failed to deserialize data to instance of "
                    f"{target_type.__module__}.{target_type.__qualname__} because marshalling failed on "
                    f"attribute {a.field_name}"
                ) from exc

        return target_type(**kwargs)

    def serialize(self, obj: typing.Optional[typing.Any]) -> typing.Optional[typing.Mapping[str, typing.Any]]:
        """Serialize a given entity into a raw data item.

        Parameters
        ----------
        obj : :obj:`typing.Any`, optional
            The entity to serialize.

        Returns
        -------
        :obj:`typing.Mapping` [ :obj:`str`, :obj:`typing.Any` ], optional
            The serialized raw data item.

        Raises
        ------
        :obj:`LookupError`
            If the entity is not registered.
        """
        if obj is None:
            return None

        input_type = type(obj)

        try:
            descriptor = self._registered_entities[input_type]
        except KeyError:
            raise LookupError(f"No registered entity {input_type.__module__}.{input_type.__qualname__}")

        raw_data = {}

        for a in descriptor.attribs:
            if a.is_transient:
                continue
            value = getattr(obj, a.field_name)
            raw_data[a.raw_name] = a.serializer(value) or repr(value)

        return raw_data


HIKARI_ENTITY_MARSHALLER = HikariEntityMarshaller()


def attrs(**kwargs):
    """Creates a decorator for a class to make it into an :mod:`attrs` class.

    This decorator will register the

    Parameters
    ----------
    **kwargs :
        Any kwargs to pass to :func:`attr.s`.

    Other Parameters
    ----------------
    auto_attribs : :obj:`bool`
        This must always be ``False`` if specified, or a :obj:`ValueError`
        will be raised, as this feature is not compatible with this marshaller
        implementation. If not specified, it will default to ``False``.
    marshaller : :obj:`HikariEntityMarshaller`
        If specified, this should be an instance of a marshaller to use. For
        most internal purposes, you want to not specify this, since it will
        then default to the hikari-global marshaller instead. This is useful,
        however, for testing and for external usage.

    Returns
    -------
    A decorator to decorate a class with.

    Raises
    ------
    :obj:`ValueError`
        If you attempt to use the `auto_attribs` feature provided by
        :mod:`attr`.

    Example
    -------

    .. code-block:: python

        @attrs()
        class MyEntity:
            id: int = attrib(deserializer=int, serializer=str)
            password: str = attrib(deserializer=int, transient=True)
            ...

    """
    assertions.assert_that(not kwargs.get("auto_attribs"), "Cannot use auto attribs here")
    kwargs["auto_attribs"] = False
    return lambda cls: kwargs.pop("marshaller", HIKARI_ENTITY_MARSHALLER).register(attr.s(**kwargs)(cls))
