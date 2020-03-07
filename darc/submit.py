# -*- coding: utf-8 -*-
"""Data Submission
=====================

The :mod:`darc` project integrates the capability of submitting
fetched data and information to a web server, to support real-time
cross-analysis and status display.

There are three submission events:

1. New Host Submission -- :data:`~darc.submit.API_NEW_HOST`

   Submitted in :func:`~darc.crawl.crawler` function call, when the
   crawling URL is marked as a new host.

2. Requests Submission -- :data:`~darc.submit.API_REQUESTS`

   Submitted in :func:`~darc.crawl.crawler` function call, after the
   crawling process of the URL using |requests|_.

3. Selenium Submission -- :data:`~darc.submit.API_SELENIUM`

   Submitted in :func:`~darc.crawl.loader` function call, after the
   loading process of the URL using |selenium|_.

"""

import base64
import dataclasses
import glob
import json
import os
import pprint
import shutil
import sys
import warnings

import requests
import stem.util.term

import darc.typing as typing
from darc.const import DEBUG, PATH_DB
from darc.error import APIRequestFailed, render_error
from darc.link import Link
from darc.proxy.i2p import get_hosts
from darc.requests import null_session

# type alias
File = typing.Dict[str, typing.Union[str, typing.ByteString]]
Domain = typing.Union[typing.Literal['new_host'], typing.Literal['requests'], typing.Literal['selenium']]

# retry times
API_RETRY = int(os.getenv('API_RETRY', '3'))

# API request storage
PATH_API = os.path.join(PATH_DB, 'api')
os.makedirs(PATH_API, exist_ok=True)

# API URLs
API_NEW_HOST = os.getenv('API_NEW_HOST')
API_REQUESTS = os.getenv('API_REQUESTS')
API_SELENIUM = os.getenv('API_SELENIUM')

if DEBUG:
    print(stem.util.term.format('-*- SUBMIT API -*-', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format(f'NEW HOST: {API_NEW_HOST}', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format(f'REQUESTS: {API_REQUESTS}', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format(f'SELENIUM: {API_SELENIUM}', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns, stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def get_metadata(link: Link) -> typing.Dict[str, str]:
    """Generate metadata field.

    Args:
        link: Link object to generate metadata.

    Returns:
        The metadata from ``link``.

        * ``url`` -- original URL, :attr:`link.url <darc.link.Link.url>`
        * ``proxy`` -- proxy type, :attr:`link.proxy <darc.link.Link.proxy>`
        * ``host`` -- hostname, :attr:`link.host <darc.link.Link.host>`
        * ``base`` -- base path, :attr:`link.base <darc.link.Link.base>`
        * ``name`` -- link hash, :attr:`link.name <darc.link.Link.name>`

    """
    metadata = dataclasses.asdict(link)
    metadata['base'] = os.path.relpath(link.base, PATH_DB)
    del metadata['url_parse']
    return metadata


def get_robots(link: Link) -> typing.Optional[File]:  # pylint: disable=inconsistent-return-statements
    """Read ``robots.txt``.

    Args:
        link: Link object to read ``robots.txt``.

    Returns:
        * If ``robots.txt`` exists, return the data from ``robots.txt``.

          * ``path`` -- relative path from ``robots.txt`` to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/robots.txt``
          * ``data`` -- *base64* encoded content of ``robots.txt``

        * If not, return ``None``.

    See Also:
        * :func:`darc.crawl.crawler`
        * :func:`darc.save.save_robots`

    """
    path = os.path.join(link.base, 'robots.txt')
    if not os.path.isfile(path):
        return
    with open(path, 'rb') as file:
        content = file.read()
    data = dict(
        path=os.path.relpath(path, PATH_DB),
        data=base64.b64encode(content).decode(),
    )
    return data


def get_sitemap(link: Link) -> typing.Optional[typing.List[File]]:  # pylint: disable=inconsistent-return-statements
    """Read sitemaps.

    Args:
        link: Link object to read sitemaps.

    Returns:
        * If sitemaps exist, return list of the data from sitemaps.

          * ``path`` -- relative path from sitemap to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/sitemap_<hash>.xml``
          * ``data`` -- *base64* encoded content of sitemap

        * If not, return ``None``.

    See Also:
        * :func:`darc.crawl.crawler`
        * :func:`darc.save.save_sitemap`

    """
    path_list = glob.glob(os.path.join(link.base, 'sitemap_*.xml'))
    if not path_list:
        return

    data_list = list()
    for path in path_list:
        with open(path, 'rb') as file:
            content = file.read()
        data = dict(
            path=os.path.relpath(path, PATH_DB),
            data=base64.b64encode(content).decode(),
        )
        data_list.append(data)
    return data_list


def get_raw(link: Link, time: str) -> typing.Optional[File]:  # pylint: disable=inconsistent-return-statements
    """Read raw document.

    Args:
        link: Link object to read document from |requests|_.

    Returns:
        * If document exists, return the data from document.

          * ``path`` -- relative path from document to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/<hash>_<timestamp>_raw.html``
            or ``<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.dat``

          * ``data`` -- *base64* encoded content of document
        * If not, return ``None``.

    See Also:
        * :func:`darc.crawl.crawler`
        * :func:`darc.save.save_html`
        * :func:`darc.save.save_file`

    """
    path = os.path.join(link.base, f'{link.name}_{time}_raw.html')
    if not os.path.isfile(path):
        path = os.path.join(link.base, f'{link.name}_{time}.dat')
    if not os.path.isfile(path):
        return
    with open(path, 'rb') as file:
        content = file.read()
    data = dict(
        path=os.path.relpath(path, PATH_DB),
        data=base64.b64encode(content).decode(),
    )
    return data


def get_html(link: Link, time: str) -> typing.Optional[File]:  # pylint: disable=inconsistent-return-statements
    """Read HTML document.

    Args:
        link: Link object to read document from |selenium|_.

    Returns:
        * If document exists, return the data from document.

          * ``path`` -- relative path from document to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.html``
          * ``data`` -- *base64* encoded content of document

        * If not, return ``None``.

    See Also:
        * :func:`darc.crawl.loader`
        * :func:`darc.save.save_html`

    """
    path = os.path.join(link.base, f'{link.name}_{time}.html')
    if not os.path.isfile(path):
        return
    with open(path, 'rb') as file:
        content = file.read()
    data = dict(
        path=os.path.relpath(path, PATH_DB),
        data=base64.b64encode(content).decode(),
    )
    return data


def get_screenshot(link: Link, time: str) -> typing.Optional[File]:  # pylint: disable=inconsistent-return-statements
    """Read screenshot picture.

    Args:
        link: Link object to read screenshot from |selenium|_.

    Returns:
        * If screenshot exists, return the data from screenshot.

          * ``path`` -- relative path from screenshot to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.png``
          * ``data`` -- *base64* encoded content of screenshot

        * If not, return ``None``.

    See Also:
        * :func:`darc.crawl.loader`

    """
    path = os.path.join(link.base, f'{link.name}_{time}.png')
    if not os.path.isfile(path):
        return
    with open(path, 'rb') as file:
        content = file.read()
    data = dict(
        path=os.path.relpath(path, PATH_DB),
        data=base64.b64encode(content).decode(),
    )
    return data


def save_submit(domain: Domain, data: typing.Dict[str, typing.Any]):
    """Save failed submit data.

    Args:
        domain (``'new_host'``, ``'requests'`` or ``'selenium'``): Domain of the submit data.
        data: Submit data.

    See Also:
        * :data:`darc.submit.PATH_API`
        * :func:`darc.submit.submit`
        * :func:`darc.submit.submit_new_host`
        * :func:`darc.submit.submit_requests`
        * :func:`darc.submit.submit_selenium`

    """
    metadata = data['[metadata]']
    name = metadata['name']
    ts = data['Timestamp']

    root = os.path.join(PATH_API, metadata['base'], domain)
    os.makedirs(root, exist_ok=True)

    with open(os.path.join(root, f'{name}_{ts}.json'), 'w') as file:
        json.dump(data, file, indent=2)


def submit(api: str, domain: Domain, data: typing.Dict[str, typing.Any]):
    """Submit data.

    Args:
        api: API URL.
        domain (``'new_host'``, ``'requests'`` or ``'selenium'``): Domain of the submit data.
        data: Submit data.

    See Also:
        * :data:`darc.submit.API_RETRY`
        * :func:`darc.submit.save_submit`
        * :func:`darc.submit.submit_new_host`
        * :func:`darc.submit.submit_requests`
        * :func:`darc.submit.submit_selenium`

    """
    with null_session() as session:
        for _ in range(API_RETRY+1):
            try:
                response = session.post(api, json=data)
                if response.ok:
                    return
            except requests.RequestException as error:
                warning = warnings.formatwarning(error, APIRequestFailed, __file__, 150,
                                                 f'[{domain.upper()}] response = requests.post(api, json=data)')
                print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
    save_submit(domain, data)


def submit_new_host(time: typing.Datetime, link: Link):
    """Submit new host.

    When a new host is discovered, the :mod:`darc` crawler will submit the
    host information. Such includes ``robots.txt`` (if exists) and
    ``sitemap.xml`` (if any).

    Args:
        time (datetime.datetime): Timestamp of submission.
        link: Link object of submission.

    If :data:`~darc.submit.API_NEW_HOST` is ``None``, the data for submission
    will directly be save through :func:`~darc.submit.save_submit`.

    The data submitted should have following format::

        {
            // metadata of URL
            "[metadata]": {
                // original URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
                "url": ...,
                // proxy type - null / tor / i2p / zeronet / freenet
                "proxy": ...,
                // hostname / netloc, c.f. ``urllib.parse.urlparse``
                "host": ...,
                // base folder, relative path (to data root path ``PATH_DATA``) in containter - <proxy>/<scheme>/<host>
                "base": ...,
                // sha256 of URL as name for saved files (timestamp is in ISO format)
                //   JSON log as this one - <base>/<name>_<timestamp>.json
                //   HTML from requests - <base>/<name>_<timestamp>_raw.html
                //   HTML from selenium - <base>/<name>_<timestamp>.html
                //   generic data files - <base>/<name>_<timestamp>.dat
                "name": ...
            },
            // requested timestamp in ISO format as in name of saved file
            "Timestamp": ...,
            // original URL
            "URL": ...,
            // robots.txt from the host (if not exists, then ``null``)
            "Robots": {
                // path of the file, relative path (to data root path ``PATH_DATA``) in container
                //   - <proxy>/<scheme>/<host>/robots.txt
                "path": ...,
                // content of the file (**base64** encoded)
                "data": ...,
            },
            // sitemaps from the host (if none, then ``null``)
            "Sitemaps": [
                {
                    // path of the file, relative path (to data root path ``PATH_DATA``) in container
                    //   - <proxy>/<scheme>/<host>/sitemap_<name>.txt
                    "path": ...,
                    // content of the file (**base64** encoded)
                    "data": ...,
                },
                ...
            ],
            // hosts.txt from the host (if proxy type is ``i2p``; if not exists, then ``null``)
            "Hosts": {
                // path of the file, relative path (to data root path ``PATH_DATA``) in container
                //   - <proxy>/<scheme>/<host>/hosts.txt
                "path": ...,
                // content of the file (**base64** encoded)
                "data": ...,
            }
        }

    See Also:
        * :data:`darc.submit.API_NEW_HOST`
        * :func:`darc.submit.submit`
        * :func:`darc.submit.save_submit`
        * :func:`darc.submit.get_metadata`
        * :func:`darc.submit.get_robots`
        * :func:`darc.proxy.i2p.get_hosts`

    """
    metadata = get_metadata(link)
    ts = time.isoformat()

    data = {
        '[metadata]': metadata,
        'Timestamp': ts,
        'URL': link.url,
        'Robots': get_robots(link),
        'Sitemaps': get_sitemap(link),
        'Hosts': get_hosts(link),
    }

    if DEBUG:
        print(stem.util.term.format('-*- NEW HOST DATA -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(data), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    if API_NEW_HOST is None:
        save_submit('new_host', data)
        return

    # submit data
    submit(API_NEW_HOST, 'new_host', data)


def submit_requests(time: typing.Datetime, link: Link,
                    response: typing.Response, session: typing.Session):
    """Submit requests data.

    When crawling, we'll first fetch the URl using |requests|_, to check
    its availability and to save its HTTP headers information. Such information
    will be submitted to the web UI.

    Args:
        time (datetime.datetime): Timestamp of submission.
        link: Link object of submission.
        response (|Response|_): Response object of submission.
        session (|Session|_): Session object of submission.

    If :data:`~darc.submit.API_REQUESTS` is ``None``, the data for submission
    will directly be save through :func:`~darc.submit.save_submit`.

    The data submitted should have following format::

        {
            // metadata of URL
            "[metadata]": {
                // original URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
                "url": ...,
                // proxy type - null / tor / i2p / zeronet / freenet
                "proxy": ...,
                // hostname / netloc, c.f. ``urllib.parse.urlparse``
                "host": ...,
                // base folder, relative path (to data root path ``PATH_DATA``) in containter - <proxy>/<scheme>/<host>
                "base": ...,
                // sha256 of URL as name for saved files (timestamp is in ISO format)
                //   JSON log as this one - <base>/<name>_<timestamp>.json
                //   HTML from requests - <base>/<name>_<timestamp>_raw.html
                //   HTML from selenium - <base>/<name>_<timestamp>.html
                //   generic data files - <base>/<name>_<timestamp>.dat
                "name": ...
            },
            // requested timestamp in ISO format as in name of saved file
            "Timestamp": ...,
            // original URL
            "URL": ...,
            // request method
            "Method": "GET",
            // response status code
            "Status-Code": ...,
            // response reason
            "Reason": ...,
            // response cookies (if any)
            "Cookies": {
                ...
            },
            // session cookies (if any)
            "Session": {
                ...
            },
            // request headers (if any)
            "Request": {
                ...
            },
            // response headers (if any)
            "Response": {
                ...
            },
            // requested file (if not exists, then ``null``)
            "Document": {
                // path of the file, relative path (to data root path ``PATH_DATA``) in container
                //   - <proxy>/<scheme>/<host>/<name>_<timestamp>_raw.html
                // or if the document is of generic content type, i.e. not HTML
                //   - <proxy>/<scheme>/<host>/<name>_<timestamp>.dat
                "path": ...,
                // content of the file (**base64** encoded)
                "data": ...,
            }
        }

    See Also:
        * :data:`darc.submit.API_REQUESTS`
        * :func:`darc.submit.submit`
        * :func:`darc.submit.save_submit`
        * :func:`darc.submit.get_metadata`
        * :func:`darc.submit.get_raw`
        * :func:`darc.crawl.crawler`

    """
    metadata = get_metadata(link)
    ts = time.isoformat()

    data = {
        '[metadata]': metadata,
        'Timestamp': ts,
        'URL': link.url,
        'Method': response.request.method,
        'Status-Code': response.status_code,
        'Reason': response.reason,
        'Cookies': response.cookies.get_dict(),
        'Session': session.cookies.get_dict(),
        'Request': dict(response.request.headers),
        'Response': dict(response.headers),
        'Document': get_raw(link, ts),
    }

    if DEBUG:
        print(stem.util.term.format('-*- REQUESTS DATA -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(data), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    if API_REQUESTS is None:
        save_submit('requests', data)
        return

    # submit data
    submit(API_REQUESTS, 'requests', data)


def submit_selenium(time: typing.Datetime, link: Link):
    """Submit selenium data.

    After crawling with |requests|_, we'll then render the URl using
    |selenium|_ with Google Chrome and its web driver, to provide a fully
    rendered web page. Such information will be submitted to the web UI.

    Args:
        time (datetime.datetime): Timestamp of submission.
        link: Link object of submission.

    If :data:`~darc.submit.API_SELENIUM` is ``None``, the data for submission
    will directly be save through :func:`~darc.submit.save_submit`.

    Note:
        This information is optional, only provided if the content type from
        |requests|_ is HTML, status code not between ``400`` and ``600``, and
        HTML data not empty.

    The data submitted should have following format::

        {
            // metadata of URL
            "[metadata]": {
                // original URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
                "url": ...,
                // proxy type - null / tor / i2p / zeronet / freenet
                "proxy": ...,
                // hostname / netloc, c.f. ``urllib.parse.urlparse``
                "host": ...,
                // base folder, relative path (to data root path ``PATH_DATA``) in containter - <proxy>/<scheme>/<host>
                "base": ...,
                // sha256 of URL as name for saved files (timestamp is in ISO format)
                //   JSON log as this one - <base>/<name>_<timestamp>.json
                //   HTML from requests - <base>/<name>_<timestamp>_raw.html
                //   HTML from selenium - <base>/<name>_<timestamp>.html
                //   generic data files - <base>/<name>_<timestamp>.dat
                "name": ...
            },
            // requested timestamp in ISO format as in name of saved file
            "Timestamp": ...,
            // original URL
            "URL": ...,
            // rendered HTML document (if not exists, then ``null``)
            "Document": {
                // path of the file, relative path (to data root path ``PATH_DATA``) in container
                //   - <proxy>/<scheme>/<host>/<name>_<timestamp>.html
                "path": ...,
                // content of the file (**base64** encoded)
                "data": ...,
            },
            // web page screenshot (if not exists, then ``null``)
            "Screenshot": {
                // path of the file, relative path (to data root path ``PATH_DATA``) in container
                //   - <proxy>/<scheme>/<host>/<name>_<timestamp>.png
                "path": ...,
                // content of the file (**base64** encoded)
                "data": ...,
            }
        }

    See Also:
        * :data:`darc.submit.API_SELENIUM`
        * :func:`darc.submit.submit`
        * :func:`darc.submit.save_submit`
        * :func:`darc.submit.get_metadata`
        * :func:`darc.submit.get_html`
        * :func:`darc.submit.get_screenshot`
        * :func:`darc.crawl.loader`

    """
    metadata = get_metadata(link)
    ts = time.isoformat()

    data = {
        '[metadata]': metadata,
        'Timestamp': ts,
        'URL': link.url,
        'Document': get_html(link, ts),
        'Screenshot': get_screenshot(link, ts),
    }

    if DEBUG:
        print(stem.util.term.format('-*- SELENIUM DATA -*-',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(render_error(pprint.pformat(data), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

    if API_SELENIUM is None:
        save_submit('selenium', data)
        return

    # submit data
    submit(API_REQUESTS, 'selenium', data)
