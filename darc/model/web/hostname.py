# -*- coding: utf-8 -*-
"""Hostname Records
----------------------

The :mod:`darc.model.web.hostname` module defines the data model
representing hostnames, specifically from ``new_host`` submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_new_host` for more
   information.

"""

import peewee

import darc.typing as typing
from darc._compat import cached_property
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import IntEnumField, Proxy

__all__ = ['HostnameModel']


class HostnameModel(BaseModel):
    """Data model for a hostname record.

    Important:
        The *alive* of a hostname is toggled if :func:`~darc.crawl.crawler`
        successfully requested a URL with such hostname.

    """

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: str = peewee.TextField()
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: Proxy = IntEnumField(choices=Proxy)

    #: Timestamp of first ``new_host`` submission.
    discovery: typing.Datetime = peewee.DateTimeField()
    #: Timestamp of last related submission.
    last_seen: typing.Datetime = peewee.DateTimeField()

    @cached_property
    def alive(self) -> bool:
        """If the hostname is still active.

        We consider the hostname as *inactive*, only if all
        subsidiary URLs are *inactive*.

        """
        return any(map(lambda url: url.alive, self.urls))  # pylint: disable=no-member

    @cached_property
    def since(self) -> typing.Datetime:
        """The hostname is active/inactive since such timestamp.

        We confider the timestamp by the earlies timestamp
        of related subsidiary *active/inactive* URLs.

        """
        if self.alive:
            filtering = lambda url: url.alive
        else:
            filtering = lambda url: not url.alive

        return min(*filter(
            filtering, self.urls  # pylint: disable=no-member
        ), key=lambda url: url.since)
