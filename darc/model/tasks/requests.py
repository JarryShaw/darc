# -*- coding: utf-8 -*-
"""Crawler Queue
-------------------

.. important::

   The :obj:`crawler <darc.crawl.crawler>` queue is a **sorted set**
   named ``queue_requests`` in a `Redis`_ based task queue.

   .. _Redis: https://redis.io

The :mod:`darc.model.tasks.requests` model contains the data model
defined for the :obj:`crawler <darc.crawl.crawler>` queue.

"""

from typing import TYPE_CHECKING

from peewee import CharField, DateTimeField, TextField

from darc.model.abc import BaseModel
from darc.model.utils import PickleField

if TYPE_CHECKING:
    import darc.link as darc_link  # Link
    from darc._compat import datetime

__all__ = ['RequestsQueueModel']


class RequestsQueueModel(BaseModel):
    """Task queue for :func:`~darc.crawl.crawler`."""

    #: URL as raw text (c.f. :attr:`Link.url <darc.link.Link.url>`).
    text: str = TextField()
    #: Sha256 hash value (c.f. :attr:`Link.name <darc.link.Link.name>`).
    hash: str = CharField(max_length=256, unique=True)

    #: Pickled target :class:`~darc.link.Link` instance.
    link: 'darc_link.Link' = PickleField()
    #: Timestamp of last update.
    timestamp: 'datetime' = DateTimeField()
