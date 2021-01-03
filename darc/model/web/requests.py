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

from typing import TYPE_CHECKING

from peewee import (BlobField, BooleanField, CharField, DateTimeField, ForeignKeyField,
                    IntegerField, TextField)

from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import JSONField
from darc.model.web.url import URLModel

if TYPE_CHECKING:
    from typing import Any, Dict, List

    from darc._compat import datetime

    Cookies = List[Dict[str, Any]]
    Headers = Dict[str, str]

__all__ = ['RequestsModel']


class RequestsModel(BaseModel):
    """Data model for documents from ``requests`` submission."""

    #: List of redirect history, back reference from
    #: :attr:`RequestsHistoryModel.model <darc.model.web.requests.RequestsHistoryModel.model>`.
    history: 'List[RequestsHistoryModel]'

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: 'URLModel' = ForeignKeyField(URLModel, backref='requests')
    #: Timestamp of the submission.
    timestamp: 'datetime' = DateTimeField()

    #: Request method (normally ``GET``).
    method: str = CharField()
    #: Document data as :obj:`bytes`.
    document: bytes = BlobField()

    #: Conetent type.
    mime_type: str = CharField()
    #: If document is HTML or miscellaneous data.
    is_html: bool = BooleanField()

    #: Status code.
    status_code: int = IntegerField()
    #: Response reason string.
    reason: str = TextField()

    #: Response cookies.
    cookies: 'Cookies' = JSONField()
    #: Session cookies.
    session: 'Cookies' = JSONField()

    #: Request headers.
    request: 'Headers' = JSONField()
    #: Response headers.
    response: 'Headers' = JSONField()


class RequestsHistoryModel(BaseModel):
    """Data model for history records from ``requests`` submission."""

    #: History index number.
    index: int = IntegerField()
    #: Original record.
    model: RequestsModel = ForeignKeyField(RequestsModel, backref='history')

    #: Request URL.
    url: str = TextField()
    #: Timestamp of the submission.
    timestamp: 'datetime' = DateTimeField()

    #: Request method (normally ``GET``).
    method: str = CharField()
    #: Document data as :obj:`bytes`.
    document: bytes = BlobField()

    #: Status code.
    status_code: int = IntegerField()
    #: Response reason string.
    reason: str = TextField()

    #: Response cookies.
    cookies: 'Cookies' = JSONField()

    #: Request headers.
    request: 'Headers' = JSONField()
    #: Response headers.
    response: 'Headers' = JSONField()
