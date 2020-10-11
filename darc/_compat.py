# -*- coding: utf-8 -*-
"""Version compatibility."""

import sys

__all__ = [
    'nullcontext',
    'RobotFileParser',
    'datetime',
    'strsignal',
    'cached_property',
]

version = sys.version_info[:2]

# contextlib.nullcontext added in 3.7
if version >= (3, 7):
    from contextlib import nullcontext
else:
    from contextlib import AbstractContextManager

    class nullcontext(AbstractContextManager):  # type: ignore
        """Context manager that does no additional processing.

        Used as a stand-in for a normal context manager, when a particular
        block of code is only sometimes used with a normal context manager:

        cm = optional_cm if condition else nullcontext()
        with cm:
            # Perform operation, using optional_cm if condition is True
        """

        def __init__(self, enter_result=None):  # type: ignore
            self.enter_result = enter_result

        def __enter__(self):  # type: ignore
            return self.enter_result

        def __exit__(self, *excinfo):  # type: ignore # pylint: disable=arguments-differ
            pass

# urllib.robotparser.RobotFileParser.site_maps added in 3.8
if version >= (3, 8):
    from urllib.robotparser import RobotFileParser
else:
    from darc._robotparser import RobotFileParser  # type: ignore

# datetime.datetime.fromisoformat added in 3.7
if version >= (3, 7):
    from datetime import datetime
else:
    from _datetime import datetime  # type: ignore

# signal.strsignal added in 3.8
if version >= (3, 8):
    from signal import strsignal
else:
    import contextlib
    import signal

    def strsignal(signalnum):  # type: ignore
        """Return the system description of the given signal."""
        with contextlib.suppress(ValueError):
            sig = signal.Signals(signalnum)  # pylint: disable=no-member
            return f'{sig.name}: {sig.value}'

# functools.cached_property added in 3.8
if version >= (3, 8):
    from functools import cached_property
else:
    from _thread import RLock  # type: ignore

    _NOT_FOUND = object()

    class cached_property:  # type: ignore
        def __init__(self, func):  # type: ignore
            self.func = func
            self.attrname = None
            self.__doc__ = func.__doc__
            self.lock = RLock()

        def __set_name__(self, owner, name):  # type: ignore
            if self.attrname is None:
                self.attrname = name
            elif name != self.attrname:
                raise TypeError(
                    "Cannot assign the same cached_property to two different names "
                    f"({self.attrname!r} and {name!r})."
                )

        def __get__(self, instance, owner=None):  # type: ignore
            if instance is None:
                return self
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
