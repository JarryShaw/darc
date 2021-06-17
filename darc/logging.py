# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Logging System
====================

The module extended the builtin :mod:`logging` module and provides
a coloured version of :class:`~logging.Logger` to better demonstrate
the logging information of :mod:`darc`.

"""

import inspect
import logging
import pprint as pp
import shutil
import sys
from typing import TYPE_CHECKING, cast

import stem.util.term as stem_term

__all__ = ['get_logger']

if TYPE_CHECKING:
    from logging import LogRecord
    from typing import Any, AnyStr, Optional, Type
    from types import TracebackType

#: ``VERBOSE`` logging level.
VERBOSE = 5
#: ``DEBUG`` logging level, c.f., :data:`logging.DEBUG`.
DEBUG = logging.DEBUG
#: ``INFO`` logging level, c.f., :data:`logging.INFO`.
INFO = logging.INFO
#: ``WARNING`` logging level, c.f., :data:`logging.WARNING`.
WARNING = logging.WARNING
#: ``ERROR`` logging level, c.f., :data:`logging.ERROR`.
ERROR = logging.ERROR
#: ``CRITICAL`` logging level, c.f., :data:`logging.CRITICAL`.
CRITICAL = logging.CRITICAL

#: Dict[int, Tuple[str]]: Mapping of logging levels with corresponding color format.
_LOG_ATTR = {
    VERBOSE: (stem_term.Color.BLUE,),  # pylint: disable=no-member
    DEBUG: (stem_term.Color.MAGENTA,),  # pylint: disable=no-member
    INFO: (stem_term.Color.CYAN,),  # pylint: disable=no-member
    WARNING: (stem_term.Color.YELLOW,),  # pylint: disable=no-member
    ERROR: (stem_term.Color.RED,),  # pylint: disable=no-member
    CRITICAL: (stem_term.Color.RED, stem_term.Attr.UNDERLINE),  # pylint: disable=no-member
}


def render_message(message: 'AnyStr', *attr: 'str') -> str:
    """Render message.

    The function wraps the :func:`stem.util.term.format` function to
    provide multi-line formatting support.

    Args:
        message: Multi-line message to be rendered with ``colour``.
        *attr: Formatting attributes of text, c.f. :mod:`stem.util.term`.

    Returns:
        The rendered message.

    See Also:
        The message formatting is done by :func:`stem.util.term.format`
        with its various predefined formatting attributes.

    """
    return ''.join(
        stem_term.format(line, *attr) for line in message.splitlines(True)
    )


class ColorFormatter(logging.Formatter):
    """Color formatter based on record levels."""

    def format(self, record: 'LogRecord') -> str:
        """Format the specific record as text.

        Args:
            record: logging record

        Returns:
            Formatted logging message.

        See Also:
            :data:`~darc.logging._LOG_ATTR` contains the color mapping
            for each logging level.

        """
        msg = super().format(record)
        attr = _LOG_ATTR.get(record.levelno)
        if attr is None:
            return msg
        return render_message(msg, *attr)  # pylint: disable=no-member


class DarcLogger(logging.Logger):
    """The tailored logger for :mod:`darc` module."""

    @property
    def horizon(self) -> str:
        """Horizon line.

        See Also:
            The property uses :func:`shutil.get_terminal_size` to calculate the desired
            length of the ``-`` horizon line.

        """
        return '-' * shutil.get_terminal_size().columns

    def verbose(self, msg: 'Any', *args: 'Any', **kwargs: 'Any') -> None:
        """Log ``msg % args`` with severity :data:`~darc.logging.VERBOSE`.

        Args:
            msg: Message to be logged.
            *args: Arbitrary positional arguments for interploration.
            **kwargs: Arbitrary keyword arguments for log information.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.verbose("Houston, we have a %s", "thorny problem", exc_info=1)

        """
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kwargs)

    def plog(self, level: int, msg: 'Any', *args: 'Any', object: 'Any',  # pylint: disable=redefined-builtin
             pprint: 'Optional[dict[str, Any]]' = None, **kwargs: 'Any') -> None:
        """Log ``msg % args`` into a pretty-printed representation with severity ``level``.

        Args:
            level: Log severity level.
            msg: Message to be logged.
            *args: Arbitrary positional arguments for interploration.

        Keyword Args:
            object: Object to be pretty printed.
            pprint: Arbitrary arguments for :func:`pprint.pformat`.
            **kwargs: Arbitrary keyword arguments for log information.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.plog(level, "Houston, we have a %s", "thorny problem", object=object, exc_info=1)

        See Also:
            The method uses :func:`pprint.pformat` to format the target ``object``
            with ``pprint`` arguments.

        """
        if self.isEnabledFor(level):
            pformat = pp.pformat(object, **pprint or {})
            horizon = '-' * shutil.get_terminal_size().columns

            message = '%s\n%%s\n%%s' % msg
            msgargs = (*args, pformat, horizon)
            self._log(level, message, msgargs, **kwargs)

    def pwarning(self, line: str, type: 'Type[Warning]', **kwargs: 'Any') -> None:  # pylint: disable=redefined-builtin
        """Log ``msg % args`` with severity :data:`~darc.logging.WARNING`.

        Args:
            line: Original warning message.
            type: Warning category.

        Keyword Args:
            **kwargs: Arbitrary keyword arguments for log information.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.pwarning("Houston, we have a %s", "thorny problem", object=object, exc_info=1)

        See Also:
            The method mocks the output of :func:`warnings.warn` for the log message.

        """
        if self.isEnabledFor(WARNING):
            exc_info = cast('tuple[Type[BaseException], BaseException, TracebackType]',
                            sys.exc_info())
            exc_class = exc_info[0]
            message = exc_info[1]
            traceback = exc_info[2]

            category = f'{type}: {exc_class.__name__}'
            filename = inspect.getfile(traceback)
            lineno = traceback.tb_lineno

            source_lines, source_lineno = inspect.getsourcelines(traceback)
            if source_lineno <= 0:
                source_lineno = 1
            source = source_lines[lineno-source_lineno].strip()

            self._log(WARNING, '%s:%d: %s: %s: %s\n  %s',
                      (filename, lineno, category, line, message, source), **kwargs)

    def perror(self, line: 'Optional[str]' = None, type: 'Optional[Type[Warning]]' = None, **kwargs: 'Any') -> None:  # pylint: disable=redefined-builtin
        """Log ``msg % args`` with severity :data:`~darc.logging.ERROR`.

        Args:
            line: Optional source line of code (as comments).
            type: Warning category.

        Keyword Args:
            **kwargs: Arbitrary keyword arguments for log information.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.perror("Houston, we have a %s", "thorny problem", object=object, exc_info=1)

        See Also:
            The method mocks the output of :func:`warnings.warn` for the log message.

        """
        if self.isEnabledFor(ERROR):
            exc_info = cast('tuple[Type[BaseException], BaseException, TracebackType]',
                            sys.exc_info())
            exc_class = exc_info[0]
            message = exc_info[1]
            traceback = exc_info[2]

            if type is None:
                category = exc_class.__name__
            else:
                category = f'{type}: {exc_class.__name__}'

            filename = inspect.getfile(traceback)
            lineno = traceback.tb_lineno

            source_lines, source_lineno = inspect.getsourcelines(traceback)
            if source_lineno <= 0:
                source_lineno = 1
            source = source_lines[lineno-source_lineno].strip()

            if line is None:
                self._log(ERROR, '%s:%d: %s: %s\n  %s',
                          (filename, lineno, category, message, source), **kwargs)
            else:
                self._log(ERROR, '%s:%d: %s: %s\n  # %s\n  %s',
                          (filename, lineno, category, message, line.strip(), source), **kwargs)


def get_logger() -> 'DarcLogger':
    """Create a logger.

    Returns:
        :class:`~logging.Logger` instance with pre-defined
        formats, handlers, etc.

    """
    logging.setLoggerClass(DarcLogger)

    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter(
        fmt='[%(levelname)s] %(asctime)s - %(message)s',
        datefmt=r'%m/%d/%Y %I:%M:%S %p'
    ))

    logger = cast('DarcLogger', logging.getLogger('darc'))
    logger.addHandler(handler)
    logger.setLevel(INFO)
    return logger
