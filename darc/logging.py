# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Logging System
====================



"""

import logging
from typing import TYPE_CHECKING

import stem.util.term as stem_term

__all__ = ['get_logger']

if TYPE_CHECKING:
    from logging import LogRecord, Logger
    from typing import AnyStr, Any

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

    def verbose(self, msg: 'Any', *args: 'Any', **kwargs: 'Any') -> None:
        """Log 'msg % args' with severity :data:`~darc.logging.VERBOSE`.

        To pass exception information, use the keyword argument ``exc_info`` with
        a true value, e.g.

        .. code-block:: python

           logger.verbose("Houston, we have a %s", "thorny problem", exc_info=1)

        """
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kwargs)


def get_logger() -> 'Logger':
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

    logger = logging.getLogger('darc')
    logger.addHandler(handler)
    logger.setLevel(VERBOSE)
    return logger
