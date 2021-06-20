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
import os
import pprint as pp
import shutil
import sys
import traceback
from typing import TYPE_CHECKING, cast

import stem.util.term as stem_term

__all__ = ['logger']

if TYPE_CHECKING:
    from logging import LogRecord
    from types import TracebackType
    from typing import Any, AnyStr, Optional, Type

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
    DEBUG: (stem_term.Color.CYAN,),  # pylint: disable=no-member
    INFO: (stem_term.Color.GREEN,),  # pylint: disable=no-member
    WARNING: (stem_term.Color.YELLOW,),  # pylint: disable=no-member
    ERROR: (stem_term.Color.RED,),  # pylint: disable=no-member
    CRITICAL: (stem_term.BgColor.BG_RED, stem_term.Attr.HIGHLIGHT),  # pylint: disable=no-member
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
    return os.linesep.join(
        stem_term.format(line, *attr) for line in message.splitlines()
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


# class LineColorFormatter(ColorFormatter):
#     """Color formatter based on record levels for horizon lines."""
#
#     def format(self, record: 'LogRecord') -> str:
#         """Format the specific record as text.
#
#         Args:
#             record: logging record
#
#         Returns:
#             Formatted logging message.
#
#         See Also:
#             :data:`~darc.logging._LOG_ATTR` contains the color mapping
#             for each logging level.
#
#         """
#         msg = super().format(record)
#         attr = _LOG_ATTR.get(record.levelno)
#
#         columns = shutil.get_terminal_size().columns
#         msg_len = len(msg)
#
#         if columns > msg_len:
#             msg = '%s%s' % (msg, '-' * (columns - msg_len))
#         else:
#             msg = '%s%s' % (msg, '-' * (columns - msg_len % columns))
#
#         if attr is None:
#             return msg
#         return render_message(msg, *attr)  # pylint: disable=no-member


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

    def pexc(self, level: 'int' = ERROR, message: 'Optional[str]' = None,
             category: 'Optional[Type[Warning]]' = None,
             line: 'Optional[str]' = None, **kwargs: 'Any') -> None:  # pylint: disable=redefined-builtin
        """Log ``msg % args`` with severity ``level``.

        Args:
            level: Log severity level.
            message: Optional log message in additional to the error message.
            line: Optional source line of code (as comments).
            category: Warning category.

        Keyword Args:
            **kwargs: Arbitrary keyword arguments for log information.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.pexc("Houston, we have a thorny problem", type, exc_info=1)

        See Also:
            The method mocks the output of :func:`warnings.warn` for the log message.

        """
        if self.isEnabledFor(level):
            exc_info = cast('tuple[Type[BaseException], BaseException, TracebackType]',
                            sys.exc_info())
            exc_class = exc_info[0]
            exception = exc_info[1]
            traceback = exc_info[2]  # pylint: disable=redefined-outer-name

            if category is None:
                exc_type = exc_class.__name__
            else:
                exc_type = f'{category.__name__} <{exc_class.__name__}>'

            if message is None:
                msg = str(exception)
            else:
                msg = f'{message} <{exception}>'

            filename = inspect.getfile(traceback)
            lineno = traceback.tb_lineno

            source_lines, source_lineno = inspect.getsourcelines(traceback)
            if source_lineno <= 0:
                source_lineno = 1
            source = source_lines[lineno-source_lineno].strip()

            if line is not None:
                source = f'# {line}\n  {source}'
            self._log(level, '%s:%d: %s: %s\n  %s',
                      (filename, lineno, exc_type, msg, source), **kwargs)

    def ptb(self, msg: 'str', *args: 'Any', level: 'int' = CRITICAL, **kwargs: 'Any') -> None:
        """Log ``msg % args`` with severity ``level``.

        Args:
            msg: Message to be logged.
            *args: Arbitrary positional arguments for interploration.

        Keyword Args:
            level: Log severity level.
            **kwargs: Arbitrary keyword arguments for log information.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.ptb(level, "Houston, we have a %s", "thorny problem", exc_info=1)

        Note:
            The method logs the full traceback stack from :func:`traceback.format_exc`.

        """
        if self.isEnabledFor(level):
            msg = f'{msg}\n{traceback.format_exc()}{self.horizon}'
            self._log(level, msg, args, **kwargs)

    def pline(self, level: int, msg: str, *args: 'Any', **kwargs: 'Any') -> None:
        """Log ``msg % args`` with severity ``level``.

        Args:
            level: Log severity level.
            msg: Message to be logged.
            *args: Arbitrary positional arguments for interploration.

        Keyword Args:
            **kwargs: Arbitrary keyword arguments for log information.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.pline(level, "Houston, we have a %s", "thorny problem", exc_info=1)

        Note:
            The method replaces :data:`~darc.logging.formatter` with
            :data:`~darc.logging.line_formatter`, which has not prefixing
            contents in the log line.

        """
        if self.isEnabledFor(level):
            logging._acquireLock()  # type: ignore[attr-defined] # pylint: disable=protected-access
            try:
                handler.setFormatter(line_formatter)
                self._log(level, msg, args, **kwargs)
            finally:
                handler.setFormatter(formatter)
                logging._releaseLock()  # type: ignore[attr-defined] # pylint: disable=protected-access


# change logger factory
logging.setLoggerClass(DarcLogger)
logging.addLevelName(VERBOSE, 'VERBOSE')

#: Generic log formatter instance for :data:`~darc.logging.handler`.
formatter = ColorFormatter(
    fmt='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt=r'%m/%d/%Y %I:%M:%S %p',
)
#: Line-only log formmater instance for :meth:`~darc.logging.DarcLogger.pline`.
line_formatter = ColorFormatter(fmt='%(message)s')

#: Log handler instance for :data:`~darc.logging.logger`.
handler = logging.StreamHandler()
handler.setFormatter(formatter)

#: darc.logging.DarcLogger: Logger instance for :mod:`darc`.
logger = cast('DarcLogger', logging.getLogger('darc'))
logger.addHandler(handler)
logger.setLevel(INFO)
