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

import peewee

import darc.typing as typing
from darc.link import Link
from darc.model.abc import BaseModel
from darc.model.utils import PickleField

__all__ = ['RequestsQueueModel']


class RequestsQueueModel(BaseModel):
    """Task queue for :func:`~darc.crawl.crawler`."""

    #: URL as raw text (c.f. :attr:`Link.url <darc.link.Link.url>`).
    text: typing.Union[str, peewee.TextField] = peewee.TextField()
    #: Sha256 hash value (c.f. :attr:`Link.name <darc.link.Link.name>`).
    hash: typing.Union[str, peewee.CharField] = peewee.CharField(max_length=256, unique=True)

    #: Pickled target :class:`~darc.link.Link` instance.
    link: typing.Union[Link, PickleField] = PickleField()
    #: Timestamp of last update.
    timestamp: typing.Union[typing.Datetime, peewee.DateTimeField] = peewee.DateTimeField()
