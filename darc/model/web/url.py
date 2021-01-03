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

from typing import TYPE_CHECKING

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import IntEnumField, Proxy
from darc.model.web.hostname import HostnameModel

if TYPE_CHECKING:
    from typing import List

    from darc._compat import datetime
    from darc.model.web.requests import RequestsModel
    from darc.model.web.selenium import SeleniumModel

__all__ = ['URLModel']


class URLModel(BaseModel):
    """Data model for a requested URL.

    Important:
        The *alive* of a URL is toggled if :func:`~darc.crawl.crawler`
        successfully requested such URL and the status code is
        :attr:`~flask.Response.ok`.

    """

    #: ``requests`` submission record, back reference from
    #: :attr:`RequestsModel.url <darc.models.web.requests.RequestsModel.url>`.
    requests: 'List[RequestsModel]'

    #: ``selenium`` submission record, back reference from
    #: :attr:`SeleniumModel.url <darc.models.web.selenium.SeleniumModel.url>`.
    selenium: 'List[SeleniumModel]'

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: str = TextField()
    #: Sha256 hash value (c.f. :attr:`Link.name <darc.link.Link.name>`).
    hash: str = CharField(max_length=256, unique=True)

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: 'HostnameModel' = ForeignKeyField(HostnameModel, backref='urls')
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: 'Proxy' = IntEnumField(choices=Proxy)

    #: Timestamp of first submission.
    discovery: 'datetime' = DateTimeField()
    #: Timestamp of last submission.
    last_seen: 'datetime' = DateTimeField()

    #: If the hostname is still active.
    alive: bool = BooleanField()
    #: The hostname is active/inactive since this timestamp.
    since: 'datetime' = DateTimeField()
