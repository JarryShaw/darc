# -*- coding: utf-8 -*-
"""Hostname Records
----------------------

The :mod:`darc.model.web.hostname` module defines the data model
representing hostnames, specifically from ``new_host`` submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_new_host` for more
   information.

"""

from typing import TYPE_CHECKING, cast

from peewee import DateTimeField, TextField

from darc._compat import cached_property
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import IntEnumField, Proxy

if TYPE_CHECKING:
    from typing import List

    from darc._compat import datetime
    from darc.model.web.hosts import HostsModel
    from darc.model.web.robots import RobotsModel
    from darc.model.web.sitemap import SitemapModel
    from darc.model.web.url import URLModel

__all__ = ['HostnameModel']


class HostnameModel(BaseModel):
    """Data model for a hostname record.

    Important:
        The *alive* of a hostname is toggled if :func:`~darc.crawl.crawler`
        successfully requested a URL with such hostname.

    """

    #: ``hosts.txt`` for the hostname, back reference from
    #: :attr:`HostsModel.host <darc.model.web.hosts.HostsModel.host>`.
    hosts: 'List[HostsModel]'

    #: ``robots.txt`` for the hostname, back reference from
    #: :attr:`RobotsModel.host <darc.model.web.robots.RobotsModel.host>`.
    robots: 'List[RobotsModel]'

    #: ``sitemap.xml`` for the hostname, back reference from
    #: :attr:`SitemapModel.sitemaps <darc.model.web.robots.SitemapModel.sitemaps>`.
    sitemaps: 'List[SitemapModel]'

    #: URLs with the same hostname, back reference from
    #: :attr:`URLModel.hostname <darc.model.web.url.URLModel.hostname>`.
    urls: 'List[URLModel]'

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: str = TextField()
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: Proxy = IntEnumField(choices=Proxy)

    #: Timestamp of first ``new_host`` submission.
    discovery: 'datetime' = DateTimeField()
    #: Timestamp of last related submission.
    last_seen: 'datetime' = DateTimeField()

    @cached_property
    def alive(self) -> bool:
        """If the hostname is still active.

        We consider the hostname as *inactive*, only if all
        subsidiary URLs are *inactive*.

        """
        return any(map(lambda url: url.alive, self.urls))

    @cached_property
    def since(self) -> 'datetime':
        """The hostname is active/inactive since such timestamp.

        We confider the timestamp by the earlies timestamp
        of related subsidiary *active/inactive* URLs.

        """
        if self.alive:
            filtering = lambda url: cast('HostnameModel', url).alive
        else:
            filtering = lambda url: not cast('HostnameModel', url).alive

        return min(*filter(
            filtering, self.urls
        ), key=lambda url: url.since)
