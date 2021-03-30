# -*- coding: utf-8 -*-
"""Submission Data Models
============================

The :mod:`darc.model.web` module defines the data models
to store the data crawled from the :mod:`darc` project.

.. seealso::

   Please refer to :mod:`darc.submit` module for more information
   about data submission.

"""

from darc.model.web.hostname import HostnameModel
from darc.model.web.hosts import HostsModel
from darc.model.web.requests import RequestsHistoryModel, RequestsModel
from darc.model.web.robots import RobotsModel
from darc.model.web.selenium import SeleniumModel
from darc.model.web.sitemap import SitemapModel
from darc.model.web.url import URLModel, URLThroughModel

__all__ = [
    'HostnameModel', 'URLModel', 'URLThroughModel',
    'RobotsModel', 'SitemapModel', 'HostsModel',
    'RequestsModel', 'RequestsHistoryModel', 'SeleniumModel',
]
