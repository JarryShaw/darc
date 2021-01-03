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

from typing import TYPE_CHECKING

from peewee import BlobField, DateTimeField, ForeignKeyField, TextField

from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.web.url import URLModel

if TYPE_CHECKING:
    from typing import Optional

    from darc._compat import datetime

__all__ = ['SeleniumModel']


class SeleniumModel(BaseModel):
    """Data model for documents from ``selenium`` submission."""

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: 'URLModel' = ForeignKeyField(URLModel, backref='selenium')
    #: Timestamp of the submission.
    timestamp: 'datetime' = DateTimeField()

    #: Document data as :obj:`str`.
    document: str = TextField()
    #: Screenshot in PNG format as :obj:`bytes`.
    screenshot: 'Optional[bytes]' = BlobField(null=True)
