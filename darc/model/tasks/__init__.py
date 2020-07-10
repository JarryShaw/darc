# -*- coding: utf-8 -*-
"""Task Queues
=================

The :mod:`darc.model.tasks` module defines the data models
required for the task queue of :mod:`darc`.

.. seealso::

   Please refer to :mod:`darc.db` module for more information
   about the task queues.

"""

from darc.model.tasks.hostname import HostnameQueueModel
from darc.model.tasks.requests import RequestsQueueModel
from darc.model.tasks.selenium import SeleniumQueueModel

__all__ = [
    'HostnameQueueModel', 'RequestsQueueModel', 'SeleniumQueueModel',
]
