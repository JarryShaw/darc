# -*- coding: utf-8 -*-
"""URL Records
-----------------

The :mod:`darc.model.web.url` module defines the data model
representing URLs, specifically from ``requests`` and
``selenium`` submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_requests` and
   :func:`darc.submit.submit_selenium` for more information.

"""

import enum

import peewee

import darc.typing as typing
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import IntEnumField
from darc.model.web.hostname import HostnameModel

__all__ = ['URLModel']


class URLModel(BaseModel):
    """Data model for a requested URL.

    Important:
        The *alive* of a URL is toggled if :func:`~darc.crawl.crawler`
        successfully requested such URL and the status code is
        :attr:`~flask.Response.ok`.

    """

    class Proxy(enum.IntEnum):
        """Supported proxy type enumeration."""

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

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: str = peewee.TextField()
    #: Sha256 hash value (c.f. :attr:`Link.name <darc.link.Link.name>`).
    hash: str = peewee.CharField(max_length=256, unique=True)

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: HostnameModel = peewee.ForeignKeyField(HostnameModel, backref='urls')
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: Proxy = IntEnumField(choices=Proxy)

    #: Timestamp of first submission.
    discovery: typing.Datetime = peewee.DateTimeField()
    #: Timestamp of last submission.
    last_seen: typing.Datetime = peewee.DateTimeField()

    #: If the hostname is still active.
    alive: bool = peewee.BooleanField()
    #: The hostname is active since this timestamp.
    since: typing.Datetime = peewee.DateTimeField()
