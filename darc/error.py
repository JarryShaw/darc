# -*- coding: utf-8 -*-
"""Custom Exceptions
=======================

The :func:`~darc.error.render_error` function can be used to render
multi-line error messages with :mod:`stem.util.term` colours.

The :mod:`darc` project provides following custom exceptions:

* :exc:`~darc.error.LinkNoReturn`
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
* :exc:`~darc.error.LockWarning`
* :exc:`~darc.error.TorRenewFailed`
* :exc:`~darc.error.RedisCommandFailed`

"""

import stem.util.term

import darc.typing as typing


class LinkNoReturn(Exception):
    """The link has no return value from the hooks."""


class UnsupportedLink(Exception):
    """The link is not supported."""


class UnsupportedPlatform(Exception):
    """The platform is not supported."""


class UnsupportedProxy(Exception):
    """The proxy is not supported."""


class TorBootstrapFailed(Warning):
    """Tor bootstrap process failed."""


class TorRenewFailed(Warning):
    """Tor renew request failed."""


class I2PBootstrapFailed(Warning):
    """I2P bootstrap process failed."""


class ZeroNetBootstrapFailed(Warning):
    """ZeroNet bootstrap process failed."""


class FreenetBootstrapFailed(Warning):
    """Freenet bootstrap process failed."""


class RedisCommandFailed(Warning):
    """Redis command execution failed."""


class DatabaseOperaionFailed(Warning):
    """Database operation execution failed."""


class APIRequestFailed(Warning):
    """API submit failed."""


class SiteNotFoundWarning(ImportWarning):
    """Site customisation not found."""


class LockWarning(Warning):
    """Failed to acquire Redis lock."""


def render_error(message: str, colour: typing.Color) -> str:
    """Render error message.

    The function wraps the :func:`stem.util.term.format` function to
    provide multi-line formatting support.

    Args:
        message: Multi-line message to be rendered with ``colour``.
        colour (stem.util.term.Color): Front colour of text, c.f.
            :class:`stem.util.term.Color`.

    Returns:
        The rendered error message.

    """
    return ''.join(
        stem.util.term.format(line, colour) for line in message.splitlines(True)
    )
