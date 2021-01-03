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

from typing import TYPE_CHECKING

from peewee import DateTimeField, ForeignKeyField, TextField

from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.web.hostname import HostnameModel

if TYPE_CHECKING:
    from darc._compat import datetime

__all__ = ['HostsModel']


class HostsModel(BaseModel):
    """Data model for ``hosts.txt`` data."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    host: 'HostnameModel' = ForeignKeyField(HostnameModel, backref='hosts')
    #: Timestamp of the submission.
    timestamp: 'datetime' = DateTimeField()

    #: Document data as :obj:`str`.
    document: str = TextField()
