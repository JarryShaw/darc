# -*- coding: utf-8 -*-
"""``hosts.txt`` Records
---------------------------

The :mod:`darc.model.web.hosts` module defines the data model
representing ``hosts.txt`` data, specifically from ``new_host``
submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_new_host` for more
   information.

"""

import peewee

import darc.typing as typing
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.web.hostname import HostnameModel

__all__ = ['HostsModel']


class HostsModel(BaseModel):
    """Data model for ``hosts.txt`` data."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    host: HostnameModel = peewee.ForeignKeyField(HostnameModel, backref='hosts')
    #: Timestamp of the submission.
    timestamp: typing.Datetime = peewee.DateTimeField()

    #: Document data as :obj:`str`.
    document: str = peewee.TextField()
