# -*- coding: utf-8 -*-
"""``sitemap.xml`` Records
----------------------------

The :mod:`darc.model.web.sitemap` module defines the data model
representing ``sitemap.xml`` data, specifically from ``new_host``
submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_new_host` for more
   information.

"""

import peewee

import darc.typing as typing
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.web.hostname import HostnameModel

__all__ = ['SitemapModel']


class SitemapModel(BaseModel):
    """Data model for ``sitemap.xml`` data."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    host: HostnameModel = peewee.ForeignKeyField(HostnameModel, backref='sitemaps')
    #: Timestamp of the submission.
    timestamp: typing.Datetime = peewee.DateTimeField()

    #: Document data as :obj:`str`.
    document: str = peewee.TextField()
