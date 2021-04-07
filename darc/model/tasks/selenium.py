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

from typing import TYPE_CHECKING

from peewee import CharField, DateTimeField, TextField

from darc.model.abc import BaseModel
from darc.model.utils import PickleField

if TYPE_CHECKING:
    import darc.link as darc_link  # Link
    from darc._compat import datetime

__all__ = ['SeleniumQueueModel']


class SeleniumQueueModel(BaseModel):
    """Task queue for :func:`~darc.crawl.loader`."""

    #: URL as raw text (c.f. :attr:`Link.url <darc.link.Link.url>`).
    text: str = TextField()
    #: Sha256 hash value (c.f. :attr:`Link.name <darc.link.Link.name>`).
    hash: str = CharField(max_length=256, unique=True)

    #: Pickled target :class:`~darc.link.Link` instance.
    link: 'darc_link.Link' = PickleField()
    #: Timestamp of last update.
    timestamp: 'datetime' = DateTimeField()
