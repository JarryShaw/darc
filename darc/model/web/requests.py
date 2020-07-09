# -*- coding: utf-8 -*-
"""Crawler Records
---------------------

The :mod:`darc.model.web.requests` module defines the data model
representing :obj:`crawler <darc.crawl.crawler>`, specifically
from ``requests`` submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_requests` for more
   information.

"""

import peewee

import darc.typing as typing
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import JSONField
from darc.model.web.url import URLModel

__all__ = ['RequestsModel']


class RequestsModel(BaseModel):
    """Data model for documents from ``requests`` submission."""

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: URLModel = peewee.ForeignKeyField(URLModel, backref='requests')
    #: Timestamp of the submission.
    timestamp: typing.Datetime = peewee.DateTimeField()

    #: Request method (normally ``GET``).
    method: str = peewee.CharField()
    #: Document data as :obj:`bytes`.
    document: bytes = peewee.BlobField()

    #: Conetent type.
    mime_type: str = peewee.CharField()
    #: If document is HTML or miscellaneous data.
    is_html: bool = peewee.BooleanField()

    #: Status code.
    status_code: int = peewee.IntegerField()
    #: Response reason string.
    reason: str = peewee.TextField()

    #: Response cookies.
    cookies: typing.Cookies = JSONField()
    #: Session cookies.
    session: typing.Cookies = JSONField()

    #: Request headers.
    request: typing.Headers = JSONField()
    #: Response headers.
    response: typing.Headers = JSONField()


class RequestsHistoryModel(BaseModel):
    """Data model for history records from ``requests`` submission."""

    #: History index number.
    index: int = peewee.IntegerField()
    #: Original record.
    model: RequestsModel = peewee.ForeignKeyField(RequestsModel, backref='history')

    #: Request URL.
    url: str = peewee.TextField()
    #: Timestamp of the submission.
    timestamp: typing.Datetime = peewee.DateTimeField()

    #: Request method (normally ``GET``).
    method: str = peewee.CharField()
    #: Document data as :obj:`bytes`.
    document: bytes = peewee.BlobField()

    #: Status code.
    status_code: int = peewee.IntegerField()
    #: Response reason string.
    reason: str = peewee.TextField()

    #: Response cookies.
    cookies: typing.Cookies = JSONField()

    #: Request headers.
    request: typing.Headers = JSONField()
    #: Response headers.
    response: typing.Headers = JSONField()
