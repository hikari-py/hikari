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

!!! warning
    You should not change anything in this file, if you do, you will likely get
    unexpected behaviour elsewhere.
"""

from __future__ import annotations

__all__ = [
    "RAISE",
    "dereference_handle",
    "attrib",
    "marshallable",
    "HIKARI_ENTITY_MARSHALLER",
    "HikariEntityMarshaller",
    "Deserializable",
    "Serializable",
]

import importlib
import typing
import weakref

import attr

from hikari.internal import more_collections

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing

_RAW_NAME_ATTR: typing.Final[str] = __name__ + "_RAW_NAME"
_SERIALIZER_ATTR: typing.Final[str] = __name__ + "_SERIALIZER"
_DESERIALIZER_ATTR: typing.Final[str] = __name__ + "_DESERIALIZER"
_INHERIT_KWARGS: typing.Final[str] = __name__ + "_INHERIT_KWARGS"
_IF_UNDEFINED: typing.Final[str] = __name__ + "IF_UNDEFINED"
_IF_NONE: typing.Final[str] = __name__ + "_IF_NONE"
_MARSHALLER_ATTRIB: typing.Final[str] = __name__ + "_MARSHALLER_ATTRIB"
_PASSED_THROUGH_SINGLETONS: typing.Final[typing.Sequence[bool]] = [False, True, None]
RAISE: typing.Final[typing.Any] = object()
EntityT = typing.TypeVar("EntityT", contravariant=True)
ClsT = typing.Type[EntityT]


def dereference_handle(handle_string: str) -> typing.Any:
    """Parse a given handle string into an object reference.

    Parameters
    ----------
    handle_string : str
        The handle to the object to refer to. This is in the format
        `fully.qualified.module.name#object.attribute`. If no `#` is
        input, then the reference will be made to the module itself.

    Returns
    -------
    typing.Any
        The thing that is referred to from this reference.

    Examples
    --------
    * `"collections#deque"`:

        Refers to `collections.deque`

    * `"asyncio.tasks#Task"`:

        Refers to `asyncio.tasks.Task`

    * `"hikari.net"`:

        Refers to `hikari.net`

    * `"foo.bar#baz.bork.qux"`:

        Would refer to a theoretical `qux` attribute on a `bork`
        attribute on a `baz` object in the `foo.bar` module.
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
    deserializer: typing.Optional[typing.Callable[[...], typing.Any], type(RAISE)] = RAISE,
    if_none: typing.Union[typing.Callable[[], typing.Any], None, type(RAISE)] = RAISE,
    if_undefined: typing.Union[typing.Callable[[], typing.Any], None, type(RAISE)] = RAISE,
    raw_name: typing.Optional[str] = None,
    inherit_kwargs: bool = False,
    serializer: typing.Optional[typing.Callable[[typing.Any], typing.Any], type(RAISE)] = RAISE,
    **kwargs,
) -> attr.Attribute:
    """Create an `attr.ib` with marshaller metadata attached.

    Parameters
    ----------
    deserializer : typing.Callable[[...], typing.Any], optional
        The deserializer to use to deserialize raw elements.
        If `None` then this field will never be deserialized from a payload
        and will have to be attached to the object after generation or passed
        through to `deserialize` as a kwarg.
    raw_name : str, optional
        The raw name of the element in its raw serialized form. If not provided,
        then this will use the field's default name later.
    inherit_kwargs : bool
        If `True` then any fields passed to deserialize for the entity this
        attribute is attached to as kwargs will also be passed through to this
        entity's deserializer as kwargs. Defaults to `False`.
    if_none : typing.Union[typing.Callable[[], typing.Any], None]
        Either a default factory function called to get the default for when
        this field is `None` or one of `None`, `False` or `True` to specify that
        this should default to the given singleton. Will raise an exception when
        `None` is received for this field later if this isn't specified.
    if_undefined : typing.Union[typing.Callable[[], typing.Any], None]
        Either a default factory function called to get the default for when
        this field isn't defined or one of `None`, `False` or `True` to specify
        that this should default to the given singleton. Will raise an exception
        when this field is undefined later on if this isn't specified.
    serializer : typing.Callable[[typing.Any], typing.Any], optional
        The serializer to use. If not specified, then serializing the entire
        class that this attribute is in will trigger a `TypeError` later.
        If `None` then the field will not be serialized.
    **kwargs :
        Any kwargs to pass to `attr.ib`.

    Returns
    -------
    typing.Any
        The result of `attr.ib` internally being called with additional metadata.
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
    metadata[_INHERIT_KWARGS] = inherit_kwargs
    metadata[_MARSHALLER_ATTRIB] = True

    # Default to not repr-ing a field.
    kwargs.setdefault("repr", False)

    attribute = attr.ib(**kwargs, metadata=metadata)
    # Fool pylint into thinking this is any type.
    return typing.cast(typing.Any, attribute)


def _not_implemented(op, name):
    def error(*_, **__) -> typing.NoReturn:
        raise NotImplementedError(f"Field {name} does not support operation {op}")

    return error


def _default_validator(value: typing.Any):
    if value is not RAISE and value not in _PASSED_THROUGH_SINGLETONS and not callable(value):
        raise RuntimeError(
            "Invalid default factory passed for `if_undefined` or `if_none`; "
            f"expected a callable or one of the 'passed through singletons' but got {value}."
        )


class _AttributeDescriptor:
    __slots__ = (
        "raw_name",
        "field_name",
        "constructor_name",
        "if_none",
        "if_undefined",
        "is_inheriting_kwargs",
        "deserializer",
        "serializer",
    )

    def __init__(  # pylint: disable=too-many-arguments
        self,
        raw_name: str,
        field_name: str,
        constructor_name: str,
        if_none: typing.Union[typing.Callable[..., typing.Any], None, type(RAISE)],
        if_undefined: typing.Union[typing.Callable[..., typing.Any], None, type(RAISE)],
        is_inheriting_kwargs: bool,
        deserializer: typing.Callable[..., typing.Any],
        serializer: typing.Callable[[typing.Any], typing.Any],
    ) -> None:
        _default_validator(if_undefined)
        _default_validator(if_none)
        self.raw_name = raw_name
        self.field_name = field_name
        self.constructor_name = constructor_name
        self.if_none = if_none
        self.if_undefined = if_undefined
        self.is_inheriting_kwargs = is_inheriting_kwargs
        self.deserializer = deserializer
        self.serializer = serializer


class _EntityDescriptor:
    __slots__ = ("entity_type", "attribs")

    def __init__(self, entity_type: typing.Type, attribs: typing.Collection[_AttributeDescriptor]) -> None:
        self.entity_type = entity_type
        self.attribs = tuple(attribs)


def _construct_attribute_descriptor(field: attr.Attribute) -> _AttributeDescriptor:
    raw_name = typing.cast(str, field.metadata.get(_RAW_NAME_ATTR) or field.name)
    field_name = typing.cast(str, field.name)

    constructor_name = field_name

    # Attrs strips leading underscores for generated __init__ methods.
    while constructor_name.startswith("_"):
        constructor_name = constructor_name[1:]

    deserializer = field.metadata[_DESERIALIZER_ATTR]
    serializer = field.metadata[_SERIALIZER_ATTR]

    return _AttributeDescriptor(
        raw_name=raw_name,
        field_name=field_name,
        constructor_name=constructor_name,
        if_none=field.metadata[_IF_NONE],
        if_undefined=field.metadata[_IF_UNDEFINED],
        is_inheriting_kwargs=field.metadata[_INHERIT_KWARGS],
        deserializer=deserializer if deserializer is not RAISE else _not_implemented("deserialize", field_name),
        serializer=serializer if serializer is not RAISE else _not_implemented("serialize", field_name),
    )


def _construct_entity_descriptor(entity: typing.Any) -> _EntityDescriptor:
    if not hasattr(entity, "__attrs_attrs__"):
        raise TypeError(f"{entity.__module__}.{entity.__qualname__} is not an attr class")

    return _EntityDescriptor(
        entity,
        [
            _construct_attribute_descriptor(field)
            for field in attr.fields(entity)
            if field.metadata.get(_MARSHALLER_ATTRIB)
        ],
    )


class HikariEntityMarshaller:
    """Hikari's utility to manage automated serialization and deserialization.

    It can deserialize and serialize any internal components that that are
    decorated with the `marshallable` decorator, and that are
    `attr.s` classes using fields with the`attrib` function call descriptor.
    """

    __slots__ = ("_registered_entities",)

    def __init__(self) -> None:
        self._registered_entities: typing.MutableMapping[typing.Type, _EntityDescriptor] = {}

    def register(self, cls: typing.Type[EntityT]) -> typing.Type[EntityT]:
        """Register an attrs type for fast future deserialization.

        Parameters
        ----------
        cls : typing.Type[typing.Any]
            The type to register.

        Returns
        -------
        typing.Type[typing.Any]
            The input argument. This enables this to be used as a decorator if
            desired.

        Raises
        ------
        TypeError
            If the class is not an `attr.s` class.
        """
        entity_descriptor = _construct_entity_descriptor(cls)
        self._registered_entities[cls] = entity_descriptor
        return cls

    def deserialize(
        self, raw_data: more_typing.JSONObject, target_type: typing.Type[EntityT], **injected_kwargs: typing.Any
    ) -> EntityT:
        """Deserialize a given raw data item into the target type.

        Parameters
        ----------
        raw_data : typing.Mapping[str, typing.Any]
            The raw data to deserialize.
        target_type : typing.Type[typing.Any]
            The type to deserialize to.
        **injected_kwargs :
            Attributes to inject into the entity. These still need to be
            included in the model's slots and should normally be fields where
            both `deserializer` and `serializer` are set to `None`.

        Returns
        -------
        typing.Any
            The deserialized instance.

        Raises
        ------
        LookupError
            If the entity is not registered.
        AttributeError
            If the field is not optional, but the field was not present in the
            raw payload, or it was present, but it was assigned `None`.
        TypeError
            If the deserialization call failed for some reason.
        """
        try:
            descriptor = self._registered_entities[target_type]
        except KeyError:
            raise LookupError(f"No registered entity {target_type.__module__}.{target_type.__qualname__}")

        kwargs = {}

        for a in descriptor.attribs:
            if a.deserializer is None:
                continue
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
                kwargs[kwarg_name] = a.deserializer(
                    data, **(injected_kwargs if a.is_inheriting_kwargs else more_collections.EMPTY_DICT)
                )
            except Exception as exc:
                raise TypeError(
                    "Failed to deserialize data to instance of "
                    f"{target_type.__module__}.{target_type.__qualname__} because marshalling failed on "
                    f"attribute {a.field_name} (passed to constructor as {kwarg_name})"
                ) from exc

        return target_type(**kwargs, **injected_kwargs)

    def serialize(self, obj: typing.Optional[typing.Any]) -> more_typing.NullableJSONObject:
        """Serialize a given entity into a raw data item.

        Parameters
        ----------
        obj : typing.Any, optional
            The entity to serialize.

        Returns
        -------
        typing.Mapping[str, typing.Any], optional
            The serialized raw data item.

        Raises
        ------
        LookupError
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
            if a.serializer is None:
                continue
            if (value := getattr(obj, a.field_name)) is not None:
                raw_data[a.raw_name] = a.serializer(value)

        return raw_data


HIKARI_ENTITY_MARSHALLER = HikariEntityMarshaller()


def marshallable(*, marshaller: HikariEntityMarshaller = HIKARI_ENTITY_MARSHALLER) -> typing.Callable[[ClsT], ClsT]:
    """Create a decorator for a class to make it into an `attr.s` class.

    Parameters
    ----------
    marshaller : HikariEntityMarshaller
        If specified, this should be an instance of a marshaller to use. For
        most internal purposes, you want to not specify this, since it will
        then default to the hikari-global marshaller instead. This is
        useful, however, for testing and for external usage.

    !!! note
        The `auto_attribs` functionality provided by `attr.s` is not
        supported by this marshaller utility. Do not attempt to use it!

    Returns
    -------
    typing.Callable
        A decorator to decorate a class with.

    Examples
    --------
        @attrs()
        class MyEntity:
            id: int = attrib(deserializer=int, serializer=str)
            password: str = attrib(deserializer=int, transient=True)
            ...

    """

    def decorator(cls: ClsT) -> ClsT:
        marshaller.register(cls)
        return cls

    return decorator


class Deserializable:
    """Mixin that enables the class to be deserialized from a raw entity."""

    __slots__ = ()

    @classmethod
    def deserialize(
        cls: typing.Type[more_typing.T_contra], payload: more_typing.JSONType, **kwargs
    ) -> more_typing.T_contra:
        """Deserialize the given payload into the object.

        Parameters
        ----------
        payload
            The payload to deserialize into the object.
        """
        return HIKARI_ENTITY_MARSHALLER.deserialize(payload, cls, **kwargs)


class Serializable:
    """Mixin that enables an instance of the class to be serialized."""

    __slots__ = ()

    def serialize(self: more_typing.T_contra) -> more_typing.JSONType:
        """Serialize this instance into a naive value."""
        return HIKARI_ENTITY_MARSHALLER.serialize(self)
