# -*- coding: utf-8 -*-
"""Loader Queue
------------------

.. important::

   The :obj:`loader <darc.crawl.loader>` queue is a **sorted set**
   named ``queue_selenium`` in a `Redis`_ based task queue.

   .. _Redis: https://redis.io

The :mod:`darc.model.tasks.selenium` model contains the data model
defined for the :obj:`loader <darc.crawl.loader>` queue.

"""

import peewee

import darc.typing as typing
from darc.link import Link
from darc.model.abc import BaseModel
from darc.model.utils import PickleField

__all__ = ['SeleniumQueueModel']


class SeleniumQueueModel(BaseModel):
    """Task queue for :func:`~darc.crawl.loader`."""

    #: URL as raw text (c.f. :attr:`Link.url <darc.link.Link.url>`).
    text: typing.Union[str, peewee.TextField] = peewee.TextField()
    #: Sha256 hash value (c.f. :attr:`Link.name <darc.link.Link.name>`).
    hash: typing.Union[str, peewee.CharField] = peewee.CharField(max_length=256, unique=True)

    #: Pickled target :class:`~darc.link.Link` instance.
    link: typing.Union[Link, PickleField] = PickleField()
    #: Timestamp of last update.
    timestamp: typing.Union[typing.Datetime, peewee.DateTimeField] = peewee.DateTimeField()
