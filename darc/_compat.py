# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Version compatibility."""

import sys
from typing import TYPE_CHECKING

__all__ = [
    'nullcontext',
    'RobotFileParser',
    'datetime',
    'strsignal',
    'cached_property',
]

if TYPE_CHECKING:
    from types import TracebackType  # isort: split
    from signal import Signals  # isort: split # pylint: disable=no-name-in-module
    from typing import Any, Callable, Optional, Type, Union

version = sys.version_info[:2]

# contextlib.nullcontext added in 3.7
if version >= (3, 7):
    from contextlib import nullcontext
else:
    from contextlib import AbstractContextManager

    class nullcontext(AbstractContextManager):  # type: ignore[no-redef]
        """Context manager that does no additional processing.

        Used as a stand-in for a normal context manager, when a particular
        block of code is only sometimes used with a normal context manager:

        cm = optional_cm if condition else nullcontext()
        with cm:
            # Perform operation, using optional_cm if condition is True
        """

        def __init__(self, enter_result: 'Any' = None) -> None:
            self.enter_result = enter_result

        def __enter__(self) -> 'Any':
            return self.enter_result

        def __exit__(self, exc_type: 'Optional[Type[BaseException]]', exc_value: 'Optional[BaseException]',
                     traceback: 'Optional[TracebackType]') -> None:
            pass

# urllib.robotparser.RobotFileParser.site_maps added in 3.8
if version >= (3, 8):
    from urllib.robotparser import RobotFileParser
else:
    from ._robotparser import RobotFileParser  # type: ignore[misc]

# datetime.datetime.fromisoformat added in 3.7
if version >= (3, 7):
    from datetime import datetime
else:
    from ._datetime import datetime

# signal.strsignal added in 3.8
if version >= (3, 8):
    from signal import strsignal
else:
    import contextlib
    import signal

    def strsignal(__signalnum: 'Union[int, Signals]') -> 'Optional[str]':
        """Return the system description of the given signal."""
        with contextlib.suppress(ValueError):
            sig = signal.Signals(__signalnum)  # pylint: disable=no-member
            return f'{sig.name}: {sig.value}'
        return None

# functools.cached_property added in 3.8
if version >= (3, 8):
    from functools import cached_property
else:
    from _thread import RLock  # type: ignore[attr-defined]
    from typing import Generic, TypeVar  # isort: split

    _T = TypeVar("_T")
    _S = TypeVar("_S")

    _NOT_FOUND = object()

    class cached_property(Generic[_T]):  # type: ignore[no-redef]
        def __init__(self, func: 'Callable[[Any], _T]') -> None:
            self.func = func  # type: Callable[[Any], _T]
            self.attrname = None  # type: Optional[str]
            self.__doc__ = func.__doc__
            self.lock = RLock()

        def __set_name__(self, owner: 'Type[Any]', name: str) -> None:
            if self.attrname is None:
                self.attrname = name
            elif name != self.attrname:
                raise TypeError(
                    "Cannot assign the same cached_property to two different names "
                    f"({self.attrname!r} and {name!r})."
                )

        def __get__(self, instance: 'Optional[_S]',
                    owner: 'Optional[Type[Any]]' = None) -> 'Union[cached_property[_T], _T]':
            if instance is None:
                return self  # type: ignore[return-value]
            if self.attrname is None:
                raise TypeError(
                    "Cannot use cached_property instance without calling __set_name__ on it.")
            try:
                cache = instance.__dict__
            except AttributeError:  # not all objects have __dict__ (e.g. class defines slots)
                msg = (
                    f"No '__dict__' attribute on {type(instance).__name__!r} "
                    f"instance to cache {self.attrname!r} property."
                )
                raise TypeError(msg) from None
            val = cache.get(self.attrname, _NOT_FOUND)
            if val is _NOT_FOUND:
                with self.lock:
                    # check if another thread filled cache while we awaited lock
                    val = cache.get(self.attrname, _NOT_FOUND)
                    if val is _NOT_FOUND:
                        val = self.func(instance)
                        try:
                            cache[self.attrname] = val
                        except TypeError:
                            msg = (
                                f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                                f"does not support item assignment for caching {self.attrname!r} property."
                            )
                            raise TypeError(msg) from None
            return val
