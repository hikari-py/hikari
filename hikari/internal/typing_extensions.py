# This file might contain code under multiple licenses.
# This will be clearly outlined around each piece of code

"""A typing shim to provide parts of `typing_extensions` without depending on it."""

from __future__ import annotations

import typing

# https://github.com/python/typing_extensions/blob/478b2b366beb30d74d5dd0029848141bf911db7f/src/typing_extensions.py#L3085
# License: https://github.com/python/typing_extensions/blob/478b2b366beb30d74d5dd0029848141bf911db7f/LICENSE
if hasattr(typing, "override"):
    override = typing.override
else:
    _F = typing.TypeVar("_F", bound=typing.Callable[..., typing.Any])

    def override(arg: _F, /) -> _F:
        """Backport of `typing.override` for versions before 3.12."""
        try:
            arg.__override__ = True
        except (AttributeError, TypeError):
            # Skip the attribute silently if it is not writable.
            # AttributeError happens if the object has __slots__ or a
            # read-only property, TypeError if it's a builtin class.
            pass
        return arg
