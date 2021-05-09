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

from typing import TYPE_CHECKING

from peewee import CharField, DateTimeField

from darc.model.abc import BaseModel

if TYPE_CHECKING:
    from darc._compat import datetime

__all__ = ['HostnameQueueModel']


class HostnameQueueModel(BaseModel):
    """Hostname task queue."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: str = CharField(max_length=255, unique=True)  # a valid FQDN is at most 255 characters
    #: Timestamp of last update.
    timestamp: 'datetime' = DateTimeField()
