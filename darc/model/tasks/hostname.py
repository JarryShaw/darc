# -*- coding: utf-8 -*-
"""Hostname Queue
--------------------

.. important::

   The hostname queue is a **set** named ``queue_hostname`` in
   a `Redis`_ based task queue.

   .. _Redis: https://redis.io

The :mod:`darc.model.tasks.hostname` model contains the data model
defined for the hostname queue.

"""

import peewee

import darc.typing as typing
from darc.model.abc import BaseModel

__all__ = ['HostnameQueueModel']


class HostnameQueueModel(BaseModel):
    """Hostname task queue."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: typing.Union[str, peewee.TextField] = peewee.TextField()
    #: Timestamp of last update.
    timestamp: typing.Union[typing.Datetime, peewee.DateTimeField] = peewee.DateTimeField()
