# -*- coding: utf-8 -*-
"""Custom Exceptions
=======================

The :func:`~darc.error.render_error` function can be used to render
multi-line error messages with |term|_ colours.

The :mod:`darc` project provides following custom exceptions:

* :exc:`~darc.error.UnsupportedLink`
* :exc:`~darc.error.UnsupportedPlatform`
* :exc:`~darc.error.UnsupportedProxy`

The :mod:`darc` project provides following custom exceptions:

* :exc:`~darc.error.TorBootstrapFailed`
* :exc:`~darc.error.I2PBootstrapFailed`
* :exc:`~darc.error.ZeroNetBootstrapFailed`
* :exc:`~darc.error.FreenetBootstrapFailed`
* :exc:`~darc.error.APIRequestFailed`
* :exc:`~darc.error.SiteNotFoundWarning`

"""

import stem.util.term

import darc.typing as typing


class UnsupportedLink(Exception):
    """The link is not supported."""


class UnsupportedPlatform(Exception):
    """The platform is not supported."""


class UnsupportedProxy(Exception):
    """The proxy is not supported."""


class TorBootstrapFailed(Warning):
    """Tor bootstrap process failed."""


class I2PBootstrapFailed(Warning):
    """I2P bootstrap process failed."""


class ZeroNetBootstrapFailed(Warning):
    """ZeroNet bootstrap process failed."""


class FreenetBootstrapFailed(Warning):
    """Freenet bootstrap process failed."""


class APIRequestFailed(Warning):
    """API submit failed."""


class SiteNotFoundWarning(ImportWarning):
    """Site customisation not found."""


def render_error(message: str, colour: typing.Color) -> str:
    """Render error message.

    The function wraps the |format|_ function to provide multi-line
    formatting support.

    Args:
        message: Multi-line message to be rendered with ``colour``.
        colour (stem.util.term.Color): Front colour of text, c.f.
            |color|_.

    Returns:
        The rendered error message.

    """
    return ''.join(
        stem.util.term.format(line, colour) for line in message.splitlines(True)
    )
