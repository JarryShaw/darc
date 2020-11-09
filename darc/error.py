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
* :exc:`~darc.error.WorkerBreak`

.. note::

   All exceptions are inherited from :exc:`~darc.error._BaseException`.

The :mod:`darc` project provides following custom warnings:

* :exc:`~darc.error.TorBootstrapFailed`
* :exc:`~darc.error.I2PBootstrapFailed`
* :exc:`~darc.error.ZeroNetBootstrapFailed`
* :exc:`~darc.error.FreenetBootstrapFailed`
* :exc:`~darc.error.APIRequestFailed`
* :exc:`~darc.error.SiteNotFoundWarning`
* :exc:`~darc.error.LockWarning`
* :exc:`~darc.error.TorRenewFailed`
* :exc:`~darc.error.RedisCommandFailed`
* :exc:`~darc.error.HookExecutionFailed`

.. note::

   All warnings are inherited from :exc:`~darc.error._BaseWarning`.

"""

import stem.util.term

import darc.typing as typing


class _BaseException(Exception):
    """Base exception class for :mod:`darc` module."""


class LinkNoReturn(_BaseException):
    """The link has no return value from the hooks.

    Args:
        link (darc.link.Link): Original link object.

    Keyword Args:
        drop: If drops the ``link`` from task queues.

    """

    def __init__(self, link=None, *, drop: bool = True) -> None:  # type: ignore[no-untyped-def]
        self.link = link
        self.drop = drop
        super().__init__()


class UnsupportedLink(_BaseException):
    """The link is not supported."""


class UnsupportedPlatform(_BaseException):
    """The platform is not supported."""


class UnsupportedProxy(_BaseException):
    """The proxy is not supported."""


class WorkerBreak(_BaseException):
    """Break from the worker loop."""


class _BaseWarning(Warning):
    """Base warning for :mod:`darc` module."""


class TorBootstrapFailed(_BaseWarning):
    """Tor bootstrap process failed."""


class TorRenewFailed(_BaseWarning):
    """Tor renew request failed."""


class I2PBootstrapFailed(_BaseWarning):
    """I2P bootstrap process failed."""


class ZeroNetBootstrapFailed(_BaseWarning):
    """ZeroNet bootstrap process failed."""


class FreenetBootstrapFailed(_BaseWarning):
    """Freenet bootstrap process failed."""


class RedisCommandFailed(_BaseWarning):
    """Redis command execution failed."""


class DatabaseOperaionFailed(_BaseWarning):
    """Database operation execution failed."""


class APIRequestFailed(_BaseWarning):
    """API submit failed."""


class SiteNotFoundWarning(_BaseWarning, ImportWarning):
    """Site customisation not found."""


class LockWarning(_BaseWarning):
    """Failed to acquire Redis lock."""


class HookExecutionFailed(_BaseWarning):
    """Failed to execute hook function."""


def render_error(message: typing.AnyStr, colour: typing.Color) -> str:
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
