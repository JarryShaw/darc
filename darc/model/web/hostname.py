# -*- coding: utf-8 -*-
"""Hostname Records
----------------------

The :mod:`darc.model.web.hostname` module defines the data model
representing hostnames, specifically from ``new_host`` submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_new_host` for more
   information.

"""

import enum

import peewee

import darc.typing as typing
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import IntEnumField

__all__ = ['HostnameModel']


class HostnameModel(BaseModel):
    """Data model for a hostname record.

    Important:
        The *alive* of a hostname is toggled if :func:`~darc.crawl.crawler`
        successfully requested a URL with such hostname.

    """

    class Proxy(enum.IntEnum):
        """Proxy types supported by :mod:`darc`."""

        #: No proxy.
        NULL = enum.auto()
        #: Tor proxy.
        TOR = enum.auto()
        #: I2P proxy.
        I2P = enum.auto()
        #: ZeroNet proxy.
        ZERONET = enum.auto()
        #: Freenet proxy.
        FREENET = enum.auto()

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: str = peewee.TextField()
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: Proxy = IntEnumField(choices=Proxy)

    #: Timestamp of first ``new_host`` submission.
    discovery: typing.Datetime = peewee.DateTimeField()
    #: Timestamp of last related submission.
    last_seen: typing.Datetime = peewee.DateTimeField()

    #: If the hostname is still active.
    alive: bool = peewee.BooleanField()
    #: The hostname is active since this timestamp.
    since: typing.Datetime = peewee.DateTimeField()
