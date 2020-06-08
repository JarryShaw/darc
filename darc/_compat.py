# -*- coding: utf-8 -*-
"""Version compatibility."""

import sys

__all__ = [
    'nullcontext',
    'RobotFileParser',
    'datetime',
    'strsignal',
]

version = sys.version_info[:2]

# contextlib.nullcontext added in 3.7
if version >= (3, 7):
    from contextlib import nullcontext
else:
    from contextlib import AbstractContextManager

    class nullcontext(AbstractContextManager):
        """Context manager that does no additional processing.

        Used as a stand-in for a normal context manager, when a particular
        block of code is only sometimes used with a normal context manager:

        cm = optional_cm if condition else nullcontext()
        with cm:
            # Perform operation, using optional_cm if condition is True
        """

        def __init__(self, enter_result=None):
            self.enter_result = enter_result

        def __enter__(self):
            return self.enter_result

        def __exit__(self, *excinfo):  # pylint: disable=arguments-differ
            pass

# urllib.robotparser.RobotFileParser.site_maps added in 3.8
if version >= (3, 8):
    from urllib.robotparser import RobotFileParser
else:
    from darc._robotparser import RobotFileParser

# datetime.datetime.fromisoformat added in 3.7
if version >= (3, 7):
    from datetime import datetime
else:
    from _datetime import datetime

# signal.strsignal added in 3.8
if version >= (3, 8):
    from signal import strsignal
else:
    import contextlib
    import signal

    def strsignal(signalnum):
        """Return the system description of the given signal."""
        with contextlib.suppress(ValueError):
            sig = signal.Signals(signalnum)  # pylint: disable=no-member
            return f'{sig.name}: {sig.value}'
