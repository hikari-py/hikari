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
"""An internal marshalling utility used by internal API components.

Warning
-------
You should not change anything in this file, if you do, you will likely get
unexpected behaviour elsewhere.

|internal|
"""
__all__ = [
    "RAISE",
    "dereference_handle",
    "attrib",
    "marshallable",
    "HIKARI_ENTITY_MARSHALLER",
    "HikariEntityMarshaller",
]

import importlib
import typing
import weakref

import attr

from hikari.internal import assertions

_RAW_NAME_ATTR: typing.Final[str] = __name__ + "_RAW_NAME"
_SERIALIZER_ATTR: typing.Final[str] = __name__ + "_SERIALIZER"
_DESERIALIZER_ATTR: typing.Final[str] = __name__ + "_DESERIALIZER"
_TRANSIENT_ATTR: typing.Final[str] = __name__ + "_TRANSIENT"
_IF_UNDEFINED: typing.Final[str] = __name__ + "IF_UNDEFINED"
_IF_NONE: typing.Final[str] = __name__ + "_IF_NONE"
_PASSED_THROUGH_SINGLETONS: typing.Final[typing.Sequence[bool]] = [False, True, None]
RAISE: typing.Final[typing.Any] = object()

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
        Refers to ``asyncio.tasks.Task``
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
    deserializer: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None,
    if_none: typing.Union[typing.Callable[[], typing.Any], None, type(RAISE)] = RAISE,
    if_undefined: typing.Union[typing.Callable[[], typing.Any], None, type(RAISE)] = RAISE,
    raw_name: typing.Optional[str] = None,
    transient: bool = False,
    serializer: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None,
    **kwargs,
) -> attr.Attribute:
    """Create an :func:`attr.ib` with marshaller metadata attached.

    Parameters
    ----------
    deserializer : :obj:`typing.Callable` [ [ :obj:`typing.Any` ], :obj:`typing.Any` ], optional
        The deserializer to use to deserialize raw elements.
    raw_name : :obj:`str`, optional
        The raw name of the element in its raw serialized form. If not provided,
        then this will use the field's default name later.
    transient : :obj:`bool`
        If :obj:`True`, the field is marked as transient, meaning it will not be
        serialized. Defaults to :obj:`False`.
    if_none
        Either a default factory function called to get the default for when
        this field is :obj:`None` or one of :obj:`None`, :obj:`False` or
        :obj:`True` to specify that this should default to the given singleton.
        Will raise an exception when :obj:`None` is received for this field
        later if this isn't specified.
    if_undefined
        Either a default factory function called to get the default for when
        this field isn't defined or one of :obj:`None`, :obj:`False` or
        :obj:`True` to specify that this should default to the given singleton.
        Will raise an exception when this field is undefined later on if this
        isn't specified.
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

    attribute = attr.ib(**kwargs, metadata=metadata)
    # Fool pylint into thinking this is any type.
    return typing.cast(typing.Any, attribute)


def _not_implemented(op, name):
    def error(*_, **__) -> typing.NoReturn:
        raise NotImplementedError(f"Field {name} does not support operation {op}")

    return error


def _default_validator(value: typing.Any):
    assertions.assert_that(
        value is RAISE or value in _PASSED_THROUGH_SINGLETONS or callable(value),
        message=(
            "Invalid default factory passed for `if_undefined` or `if_none`; "
            f"expected a callable or one of the 'passed through singletons' but got {value}."
        ),
        error_type=RuntimeError,
    )


class _AttributeDescriptor:
    __slots__ = (
        "raw_name",
        "field_name",
        "constructor_name",
        "if_none",
        "if_undefined",
        "is_transient",
        "deserializer",
        "serializer",
    )

    def __init__(
        self,
        raw_name: str,
        field_name: str,
        constructor_name: str,
        if_none: typing.Union[typing.Callable[..., typing.Any], None, type(RAISE)],
        if_undefined: typing.Union[typing.Callable[..., typing.Any], None, type(RAISE)],
        is_transient: bool,
        deserializer: typing.Callable[[typing.Any], typing.Any],
        serializer: typing.Callable[[typing.Any], typing.Any],
    ) -> None:
        _default_validator(if_undefined)
        _default_validator(if_none)
        self.raw_name = raw_name
        self.field_name = field_name
        self.constructor_name = constructor_name
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

    constructor_name = field_name

    # Attrs strips leading underscores for generated __init__ methods.
    while constructor_name.startswith("_"):
        constructor_name = constructor_name[1:]

    return _AttributeDescriptor(
        raw_name=raw_name,
        field_name=field_name,
        constructor_name=constructor_name,
        if_none=field.metadata[_IF_NONE],
        if_undefined=field.metadata[_IF_UNDEFINED],
        is_transient=field.metadata[_TRANSIENT_ATTR],
        deserializer=field.metadata[_DESERIALIZER_ATTR] or _not_implemented("deserialize", field_name),
        serializer=field.metadata[_SERIALIZER_ATTR] or _not_implemented("serialize", field_name),
    )


def _construct_entity_descriptor(entity: typing.Any):
    assertions.assert_that(
        hasattr(entity, "__attrs_attrs__"),
        f"{entity.__module__}.{entity.__qualname__} is not an attr class",
        error_type=TypeError,
    )

    return _EntityDescriptor(entity, [_construct_attribute_descriptor(field) for field in attr.fields(entity)])


class HikariEntityMarshaller:
    """Hikari's utility to manage automated serialization and deserialization.

    It can deserialize and serialize any internal components that that are
    decorated with the :obj:`marshallable` decorator, and that are
    :func:`attr.s` classes using fields with the :obj:`attrib` function call
    descriptor.
    """

    def __init__(self) -> None:
        self._registered_entities: typing.MutableMapping[typing.Type, _EntityDescriptor] = {}

    def register(self, cls: typing.Type[EntityT]) -> typing.Type[EntityT]:
        """Register an attrs type for fast future deserialization.

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
            If the class is not an :obj:`attr.s` class.
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
            raw payload, or it was present, but it was assigned :obj:`None`.
        :obj:`TypeError`
            If the deserialization call failed for some reason.
        """
        try:
            descriptor = self._registered_entities[target_type]
        except KeyError:
            raise LookupError(f"No registered entity {target_type.__module__}.{target_type.__qualname__}")

        kwargs = {}

        for a in descriptor.attribs:
            kwarg_name = a.constructor_name

            if a.raw_name not in raw_data:
                if a.if_undefined is RAISE:
                    raise AttributeError(
                        "Failed to deserialize data to instance of "
                        f"{target_type.__module__}.{target_type.__qualname__} due to required field {a.field_name} "
                        f"(from raw key {a.raw_name}) not being included in the input payload\n\n{raw_data}"
                    )
                if a.if_undefined in _PASSED_THROUGH_SINGLETONS:
                    kwargs[kwarg_name] = a.if_undefined
                else:
                    kwargs[kwarg_name] = a.if_undefined()
                continue

            if (data := raw_data[a.raw_name]) is None:
                if a.if_none is RAISE:
                    raise AttributeError(
                        "Failed to deserialize data to instance of "
                        f"{target_type.__module__}.{target_type.__qualname__} due to non-nullable field {a.field_name}"
                        f" (from raw key {a.raw_name}) being `None` in the input payload\n\n{raw_data}"
                    )
                if a.if_none in _PASSED_THROUGH_SINGLETONS:
                    kwargs[kwarg_name] = a.if_none
                else:
                    kwargs[kwarg_name] = a.if_none()
                continue

            try:
                # Use the deserializer if it is there, otherwise use the constructor of the type of the field.
                kwargs[kwarg_name] = a.deserializer(data) if a.deserializer else data
            except Exception as exc:
                raise TypeError(
                    "Failed to deserialize data to instance of "
                    f"{target_type.__module__}.{target_type.__qualname__} because marshalling failed on "
                    f"attribute {a.field_name} (passed to constructor as {kwarg_name})"
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
            if value is not None:
                raw_data[a.raw_name] = a.serializer(value)

        return raw_data


HIKARI_ENTITY_MARSHALLER = HikariEntityMarshaller()


def marshallable(*, marshaller: HikariEntityMarshaller = HIKARI_ENTITY_MARSHALLER):
    """Create a decorator for a class to make it into an :obj:`attr.s` class.

    Parameters
    ----------
    marshaller : :obj:`HikariEntityMarshaller`
        If specified, this should be an instance of a marshaller to use. For
        most internal purposes, you want to not specify this, since it will
        then default to the hikari-global marshaller instead. This is
        useful, however, for testing and for external usage.

    Returns
    -------
    ``decorator(T) -> T``
        A decorator to decorate a class with.

    Notes
    -----
    The ``auto_attribs`` functionality provided by :obj:`attr.s` is not
    supported by this marshaller utility. Do not attempt to use it!

    Example
    -------

    .. code-block:: python

        @attrs()
        class MyEntity:
            id: int = attrib(deserializer=int, serializer=str)
            password: str = attrib(deserializer=int, transient=True)
            ...

    """

    def decorator(cls):
        return marshaller.register(cls)

    return decorator
