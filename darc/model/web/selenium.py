# -*- coding: utf-8 -*-
"""Loader Records
--------------------

The :mod:`darc.model.web.selenium` module defines the data model
representing :obj:`loader <darc.crawl.loader>`, specifically
from ``selenium`` submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_selenium` for more
   information.

"""

import peewee

import darc.typing as typing
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.web.url import URLModel

__all__ = ['SeleniumModel']


class SeleniumModel(BaseModel):
    """Data model for documents from ``selenium`` submission."""

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: URLModel = peewee.ForeignKeyField(URLModel, backref='selenium')
    #: Timestamp of the submission.
    timestamp: typing.Datetime = peewee.DateTimeField()

    #: Document data as :obj:`str`.
    document: str = peewee.TextField()
    #: Screenshot in PNG format as :obj:`bytes`.
    screenshot: typing.Optional[bytes] = peewee.BlobField(null=True)
