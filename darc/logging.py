# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Logging System
====================



"""

import logging
from typing import TYPE_CHECKING

import stem.util.term as stem_term

if TYPE_CHECKING:
    from logging import LogRecord
    from typing import AnyStr

#: Dict[int, Tuple[str]]:
_LOG_COLOR = {
    logging.NOTSET: (stem_term.Color.BLUE),  # pylint: disable=no-member
    logging.DEBUG: (stem_term.Color.MAGENTA,),  # pylint: disable=no-member
    logging.INFO: (stem_term.Color.CYAN,),  # pylint: disable=no-member
    logging.WARNING: (stem_term.Color.YELLOW,),  # pylint: disable=no-member
    logging.ERROR: (stem_term.Color.RED,),  # pylint: disable=no-member
    logging.CRITICAL: (stem_term.Color.RED, stem_term.Attr.UNDERLINE),  # pylint: disable=no-member
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
    """Color formatter based on levels.

    """

    def format(self, record: 'LogRecord') -> str:
        """Format the specific record as text.

        """
        msg = super().format(record)
        attr = _LOG_COLOR.get(record.levelno)
        if attr is None:
            return msg
        return render_message(msg, *attr)  # pylint: disable=no-member
