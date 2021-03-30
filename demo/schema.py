# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports,no-name-in-module
"""JSON schema generator."""

from typing import TYPE_CHECKING

import pydantic.schema
from pydantic import BaseModel, Field

__all__ = ['NewHostModel', 'RequestsModel', 'SeleniumModel']

if TYPE_CHECKING:
    from datetime import datetime
    from enum import Enum
    from typing import Any, Dict, List, Optional

    from pydantic import AnyUrl, PositiveInt

    CookiesType = List[Dict[str, Any]]
    HeadersType = Dict[str, str]

    class Proxy(str, Enum):
        """Proxy type."""

        null = 'null'
        tor = 'tor'
        i2p = 'i2p'
        zeronet = 'zeronet'
        freenet = 'freenet'

###############################################################################
# Miscellaneous auxiliaries
###############################################################################


class Metadata(BaseModel):
    """Metadata of URL."""

    url: 'AnyUrl' = Field(
        description='original URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>')
    proxy: 'Proxy' = Field(
        description='proxy type - null / tor / i2p / zeronet / freenet')
    host: str = Field(
        description='hostname / netloc, c.f. ``urllib.parse.urlparse``')
    base: str = Field(
        description=('base folder, relative path (to data root path ``PATH_DATA``) in containter '
                     '- <proxy>/<scheme>/<host>'))
    name: str = Field(
        description=('sha256 of URL as name for saved files (timestamp is in ISO format) '
                     '- JSON log as this one: <base>/<name>_<timestamp>.json; '
                     '- HTML from requests: <base>/<name>_<timestamp>_raw.html; '
                     '- HTML from selenium: <base>/<name>_<timestamp>.html; '
                     '- generic data files: <base>/<name>_<timestamp>.dat'))
    backref: str = Field(
        description='originate URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>')

    class Config:
        title = 'metadata'


class RobotsDocument(BaseModel):
    """``robots.txt`` document data."""

    path: str = Field(
        description=('path of the file, relative path (to data root path ``PATH_DATA``) in container '
                     '- <proxy>/<scheme>/<host>/robots.txt'))
    data: str = Field(
        description='content of the file (**base64** encoded)')


class SitemapDocument(BaseModel):
    """Sitemaps document data."""

    path: str = Field(
        description=('path of the file, relative path (to data root path ``PATH_DATA``) in container '
                     '- <proxy>/<scheme>/<host>/sitemap_<name>.xml'))
    data: str = Field(
        description='content of the file (**base64** encoded)')


class HostsDocument(BaseModel):
    """``hosts.txt`` document data."""

    path: str = Field(
        description=('path of the file, relative path (to data root path ``PATH_DATA``) in container '
                     '- <proxy>/<scheme>/<host>/hosts.txt'))
    data: str = Field(
        description='content of the file (**base64** encoded)')


class RequestsDocument(BaseModel):
    """:mod:`requests` document data."""

    path: str = Field(
        description=('path of the file, relative path (to data root path ``PATH_DATA``) in container '
                     '- <proxy>/<scheme>/<host>/<name>_<timestamp>_raw.html; '
                     'or if the document is of generic content type, i.e. not HTML '
                     '- <proxy>/<scheme>/<host>/<name>_<timestamp>.dat'))
    data: str = Field(
        description='content of the file (**base64** encoded)')


class HistoryModel(BaseModel):
    """:mod:`requests` history data."""

    URL: 'AnyUrl' = Field(
        description='original URL')

    Method: str = Field(
        description='request method')
    status_code: 'PositiveInt' = Field(
        alias='Status-Code',
        description='response status code')
    Reason: str = Field(
        description='response reason')

    Cookies: 'CookiesType' = Field(
        description='response cookies (if any)')
    Session: 'CookiesType' = Field(
        description='session cookies (if any)')

    Request: 'HeadersType' = Field(
        description='request headers (if any)')
    Response: 'HeadersType' = Field(
        description='response headers (if any)')

    Document: str = Field(
        description='content of the file (**base64** encoded)')


class SeleniumDocument(BaseModel):
    """:mod:`selenium` document data."""

    path: str = Field(
        description=('path of the file, relative path (to data root path ``PATH_DATA``) in container '
                     '- <proxy>/<scheme>/<host>/<name>_<timestamp>.html'))
    data: str = Field(
        description='content of the file (**base64** encoded)')


class ScreenshotDocument(BaseModel):
    """Screenshot document data."""

    path: str = Field(
        description=('path of the file, relative path (to data root path ``PATH_DATA``) in container '
                     '- <proxy>/<scheme>/<host>/<name>_<timestamp>.png'))
    data: str = Field(
        description='content of the file (**base64** encoded)')


###############################################################################
# JSON schema definitions
###############################################################################


class NewHostModel(BaseModel):
    """Data submission from :func:`darc.submit.submit_new_host`."""

    partial: bool = Field(
        alias='$PARTIAL$',
        description='partial flag - true / false')
    reload: bool = Field(
        alias='$RELOAD$',
        description='reload flag - true / false')
    metadata: 'Metadata' = Field(
        alias='[metadata]',
        description='metadata of URL')

    Timestamp: 'datetime' = Field(
        description='requested timestamp in ISO format as in name of saved file')
    URL: 'AnyUrl' = Field(
        description='original URL')

    Robots: 'Optional[RobotsDocument]' = Field(
        description='robots.txt from the host (if not exists, then ``null``)')
    Sitemaps: 'Optional[List[SitemapDocument]]' = Field(
        description='sitemaps from the host (if none, then ``null``)')
    Hosts: 'Optional[HostsDocument]' = Field(
        description='hosts.txt from the host (if proxy type is ``i2p``; if not exists, then ``null``)')


    class Config:
        title = 'new_host'


class RequestsModel(BaseModel):
    """Data submission from :func:`darc.submit.submit_requests`."""

    partial: bool = Field(
        alias='$PARTIAL$',
        description='partial flag - true / false')
    metadata: 'Metadata' = Field(
        alias='[metadata]',
        description='metadata of URL')

    Timestamp: 'datetime' = Field(
        description='requested timestamp in ISO format as in name of saved file')
    URL: 'AnyUrl' = Field(
        description='original URL')

    Method: str = Field(
        description='request method')
    status_code: 'PositiveInt' = Field(
        alias='Status-Code',
        description='response status code')
    Reason: str = Field(
        description='response reason')

    Cookies: 'CookiesType' = Field(
        description='response cookies (if any)')
    Session: 'CookiesType' = Field(
        description='session cookies (if any)')

    Request: 'HeadersType' = Field(
        description='request headers (if any)')
    Response: 'HeadersType' = Field(
        description='response headers (if any)')
    content_type: str = Field(
        alias='Content-Type',
        regex='[a-zA-Z0-9.-]+/[a-zA-Z0-9.-]+',
        description='content type')

    Document: 'Optional[RequestsDocument]' = Field(
        description='requested file (if not exists, then ``null``)')
    History: 'List[HistoryModel]' = Field(
        description='redirection history (if any)')

    class Config:
        title = 'requests'


class SeleniumModel(BaseModel):
    """Data submission from :func:`darc.submit.submit_requests`."""

    partial: bool = Field(
        alias='$PARTIAL$',
        description='partial flag - true / false')
    metadata: 'Metadata' = Field(
        alias='[metadata]',
        description='metadata of URL')

    Timestamp: 'datetime' = Field(
        description='requested timestamp in ISO format as in name of saved file')
    URL: 'AnyUrl' = Field(
        description='original URL')

    Document: 'Optional[SeleniumDocument]' = Field(
        description='rendered HTML document (if not exists, then ``null``)')
    Screenshot: 'Optional[ScreenshotDocument]' = Field(
        description='web page screenshot (if not exists, then ``null``)')

    class Config:
        title = 'selenium'


if __name__ == "__main__":
    import json
    import os

    os.makedirs('schema', exist_ok=True)

    with open('schema/new_host.schema.json', 'w') as file:
        print(NewHostModel.schema_json(indent=2), file=file)
    with open('schema/requests.schema.json', 'w') as file:
        print(RequestsModel.schema_json(indent=2), file=file)
    with open('schema/selenium.schema.json', 'w') as file:
        print(SeleniumModel.schema_json(indent=2), file=file)

    schema = pydantic.schema.schema([NewHostModel, RequestsModel, SeleniumModel],
                                    title='DARC Data Submission JSON Schema')
    with open('schema/darc.schema.json', 'w') as file:
        json.dump(schema, file, indent=2)
