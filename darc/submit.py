# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
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
   crawling process of the URL using :mod:`requests`.

3. Selenium Submission -- :data:`~darc.submit.API_SELENIUM`

   Submitted in :func:`~darc.crawl.loader` function call, after the
   loading process of the URL using :mod:`selenium`.

.. seealso::

   Please refer to :doc:`data schema </demo/schema>` for more
   information about the submission data.

"""

import base64
import contextlib
import glob
import json
import os
from datetime import date
from typing import TYPE_CHECKING, cast

import peewee
import requests

from darc._compat import datetime
from darc.const import PATH_DB
from darc.db import _db_operation
from darc.error import APIRequestFailed, DatabaseOperaionFailed
from darc.logging import DEBUG as LOG_DEBUG
from darc.logging import WARNING as LOG_WARNING
from darc.logging import logger
from darc.model import (HostnameModel, HostsModel, RequestsHistoryModel, RequestsModel, RobotsModel,
                        SeleniumModel, SitemapModel, URLModel, URLThroughModel)
from darc.model.utils import Proxy
from darc.requests import null_session

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional, Tuple

    from requests import Response, Session
    from typing_extensions import Literal

    import darc.link as darc_link  # Link
    from darc._typing import File

    Domain = Literal['new_host', 'requests', 'selenium']

# save submitted data to database
SAVE_DB = bool(int(os.getenv('SAVE_DB', '1')))

# retry times
API_RETRY = int(os.getenv('API_RETRY', '3'))

# API request storage
PATH_API = os.path.join(PATH_DB, 'api')
os.makedirs(PATH_API, exist_ok=True)

# API URLs
API_NEW_HOST = os.getenv('API_NEW_HOST')
API_REQUESTS = os.getenv('API_REQUESTS')
API_SELENIUM = os.getenv('API_SELENIUM')
logger.debug('-*- SUBMIT API -*-\nNEW HOST: %s\nREQUESTS: %s\nSELENIUM: %s\n%s',
             API_NEW_HOST, API_REQUESTS, API_SELENIUM, logger.horizon)

# UNIX epoch
EPOCH = datetime(1970, 1, 1, 0, 0)  # 1970-01-01T00:00:00


def get_robots(link: 'darc_link.Link') -> 'Optional[File]':
    """Read ``robots.txt``.

    Args:
        link: Link object to read ``robots.txt``.

    Returns:
        * If ``robots.txt`` exists, return the data from ``robots.txt``.

          * ``path`` -- relative path from ``robots.txt`` to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/robots.txt``
          * ``data`` -- *base64* encoded content of ``robots.txt``

        * If not, return :data:`None`.

    See Also:
        * :func:`darc.crawl.crawler`
        * :func:`darc.proxy.null.save_robots`

    """
    path = os.path.join(link.base, 'robots.txt')
    if not os.path.isfile(path):
        return None
    with open(path, 'rb') as file:
        content = file.read()
    return {
        'path': os.path.relpath(path, PATH_DB),
        'data': base64.b64encode(content).decode(),
    }


def get_sitemaps(link: 'darc_link.Link') -> 'Optional[List[File]]':
    """Read sitemaps.

    Args:
        link: Link object to read sitemaps.

    Returns:
        * If sitemaps exist, return list of the data from sitemaps.

          * ``path`` -- relative path from sitemap to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/sitemap_<hash>.xml``
          * ``data`` -- *base64* encoded content of sitemap

        * If not, return :data:`None`.

    See Also:
        * :func:`darc.crawl.crawler`
        * :func:`darc.proxy.null.save_sitemap`

    """
    path_list = glob.glob(os.path.join(link.base, 'sitemap_*.xml'))
    if not path_list:
        return None

    data_list = []  # type: List[File]
    for path in path_list:
        with open(path, 'rb') as file:
            content = file.read()
        data_list.append({
            'path': os.path.relpath(path, PATH_DB),
            'data': base64.b64encode(content).decode(),
        })
    return data_list


def get_hosts(link: 'darc_link.Link') -> 'Optional[File]':
    """Read ``hosts.txt``.

    Args:
        link: Link object to read ``hosts.txt``.

    Returns:
        * If ``hosts.txt`` exists, return the data from ``hosts.txt``.

          * ``path`` -- relative path from ``hosts.txt`` to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/hosts.txt``
          * ``data`` -- *base64* encoded content of ``hosts.txt``

        * If not, return :data:`None`.

    See Also:
        * :func:`darc.crawl.crawler`
        * :func:`darc.proxy.i2p.save_hosts`

    """
    if link.proxy != 'i2p':
        return None

    path = os.path.join(link.base, 'hosts.txt')
    if not os.path.isfile(path):
        return None
    with open(path, 'rb') as file:
        content = file.read()
    return {
        'path': os.path.relpath(path, PATH_DB),
        'data': base64.b64encode(content).decode(),
    }


def save_submit(domain: 'Domain', data: 'Dict[str, Any]') -> None:
    """Save failed submit data.

    Args:
        domain (``'new_host'``, ``'requests'`` or ``'selenium'``): Domain of the submit data.
        data: Submit data.

    Notes:
        The saved files will be categorised by the actual runtime day
        for better maintenance.

    See Also:
        * :data:`darc.submit.PATH_API`
        * :func:`darc.submit.submit`
        * :func:`darc.submit.submit_new_host`
        * :func:`darc.submit.submit_requests`
        * :func:`darc.submit.submit_selenium`

    """
    today = date.today().isoformat()

    metadata = data['[metadata]']
    name = metadata['name']
    ts = data['Timestamp']

    root = os.path.join(PATH_API, today, metadata['base'], domain)
    os.makedirs(root, exist_ok=True)

    with open(os.path.join(root, f'{name}_{ts}.json'), 'w') as file:
        json.dump(data, file, indent=2)


def submit(api: str, domain: 'Domain', data: 'Dict[str, Any]') -> None:
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
            except requests.RequestException:
                logger.pexc(LOG_WARNING, category=APIRequestFailed,
                            line=f'[{domain.upper()}] response = requests.post(api, json=data)')
    save_submit(domain, data)


def submit_new_host(time: 'datetime', link: 'darc_link.Link', partial: bool = False, force: bool = False) -> None:
    """Submit new host.

    When a new host is discovered, the :mod:`darc` crawler will submit the
    host information. Such includes ``robots.txt`` (if exists) and
    ``sitemap.xml`` (if any).

    Args:
        time (datetime.datetime): Timestamp of submission.
        link: Link object of submission.
        partial: If the data is not complete, i.e. failed when fetching
            ``robots.txt``, ``hosts.txt`` and/or sitemaps.
        force: If the data is force re-fetched, i.e. cache expired when
            checking with :func:`darc.db.have_hostname`.

    If :data:`~darc.submit.API_NEW_HOST` is :data:`None`, the data for submission
    will directly be save through :func:`~darc.submit.save_submit`.

    The data submitted should have following format:

    .. code-block::

        {
            // partial flag - true / false
            "$PARTIAL$": ...,
            // force flag - true / false
            "$FORCE$": ...,
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
                "name": ...,
                // originate URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
                "backref": ...
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
                    //   - <proxy>/<scheme>/<host>/sitemap_<name>.xml
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
        * :func:`darc.submit.get_robots`
        * :func:`darc.submit.get_sitemaps`
        * :func:`darc.submit.get_hosts`

    """
    metadata = link.asdict()
    ts = time.isoformat()

    robots = get_robots(link)
    sitemaps = get_sitemaps(link)
    hosts = get_hosts(link)

    if SAVE_DB:
        try:
            model, _ = cast('Tuple[HostnameModel, bool]',
                            _db_operation(HostnameModel.get_or_create, hostname=link.host, defaults={
                                'proxy': Proxy[link.proxy.upper()],
                                'discovery': time,
                                'last_seen': time,
                            }))

            if robots is not None:
                _db_operation(RobotsModel.create,
                              host=model,
                              timestamp=time,
                              document=base64.b64decode(robots['data']).decode())

            if sitemaps is not None:
                for sitemap in sitemaps:
                    _db_operation(SitemapModel.create,
                                  host=model,
                                  timestamp=time,
                                  document=base64.b64decode(sitemap['data']).decode())

            if hosts is not None:
                _db_operation(HostsModel.create,
                              host=model,
                              timestamp=time,
                              document=base64.b64decode(hosts['data']).decode())
        except Exception:
            logger.pexc(LOG_WARNING, category=DatabaseOperaionFailed, line='submit_new_host(...)')

    data = {
        '$PARTIAL$': partial,
        '$FORCE$': force,
        '[metadata]': metadata,
        'Timestamp': ts,
        'URL': link.host,
        'Robots': robots,
        'Sitemaps': sitemaps,
        'Hosts': hosts,
    }
    logger.plog(LOG_DEBUG, '-*- NEW HOST DATA -*-', object=data)

    if API_NEW_HOST is None:
        save_submit('new_host', data)
        return

    # submit data
    submit(API_NEW_HOST, 'new_host', data)


def submit_requests(time: 'datetime', link: 'darc_link.Link',
                    response: 'Response', session: 'Session',
                    content: bytes, mime_type: str, html: bool = True) -> None:
    """Submit requests data.

    When crawling, we'll first fetch the URl using :mod:`requests`, to check
    its availability and to save its HTTP headers information. Such information
    will be submitted to the web UI.

    Args:
        time (datetime.datetime): Timestamp of submission.
        link: Link object of submission.
        response (requests.Response): Response object of submission.
        session (requests.Session): Session object of submission.
        content: Raw content of from the response.
        mime_type: Content type.
        html: If current document is HTML or other files.

    If :data:`~darc.submit.API_REQUESTS` is :data:`None`, the data for submission
    will directly be save through :func:`~darc.submit.save_submit`.

    The data submitted should have following format:

    .. code-block::

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
                "name": ...,
                // originate URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
                "backref": ...
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
            // content type
            "Content-Type": ...,
            // requested file (if not exists, then ``null``)
            "Document": {
                // path of the file, relative path (to data root path ``PATH_DATA``) in container
                //   - <proxy>/<scheme>/<host>/<name>_<timestamp>_raw.html
                // or if the document is of generic content type, i.e. not HTML
                //   - <proxy>/<scheme>/<host>/<name>_<timestamp>.dat
                "path": ...,
                // content of the file (**base64** encoded)
                "data": ...,
            },
            // redirection history (if any)
            "History": [
                // same record data as the original response
                {"...": "..."}
            ]
        }

    See Also:
        * :data:`darc.submit.API_REQUESTS`
        * :func:`darc.submit.submit`
        * :func:`darc.submit.save_submit`
        * :func:`darc.submit.get_raw`
        * :func:`darc.crawl.crawler`

    """
    if SAVE_DB:
        try:
            model, model_created = cast('Tuple[HostnameModel, bool]',
                                        _db_operation(HostnameModel.get_or_create, hostname=link.host, defaults={
                                            'proxy': Proxy[link.proxy.upper()],
                                            'discovery': time,
                                            'last_seen': time,
                                        }))
            if not model_created:
                model.last_seen = time
                _db_operation(model.save)

            url, url_created = cast('Tuple[URLModel, bool]',
                                    _db_operation(URLModel.get_or_create, hash=link.name, defaults={
                                        'url': link.url,
                                        'hostname': model,
                                        'proxy': Proxy[link.proxy.upper()],
                                        'discovery': time,
                                        'last_seen': time,
                                        'alive': False,
                                        'since': EPOCH,
                                    }))
            if not url.alive and response.ok:
                url.alive = True
                url.since = time
            elif url.alive and not response.ok:
                url.alive = False
                url.since = time
            if not url_created:
                url.last_seen = time
            _db_operation(url.save)

            if link.url_backref is not None:
                with contextlib.suppress(peewee.IntegrityError):
                    _db_operation(URLThroughModel.create,
                                  parent=_db_operation(URLModel.get_by_url, link.url_backref.url),
                                  child=url)

            model = cast('RequestsModel',
                         _db_operation(RequestsModel.create,
                                       url=url,
                                       timestamp=time,
                                       method=response.request.method,
                                       document=content,
                                       mime_type=mime_type,
                                       is_html=html,
                                       status_code=response.status_code,
                                       reason=response.reason,
                                       cookies=response.cookies.get_dict(),
                                       session=response.cookies.get_dict(),
                                       request=dict(response.request.headers),
                                       response=dict(response.headers)))

            for index, history in enumerate(response.history):
                _db_operation(RequestsHistoryModel.create,
                              index=index,
                              model=model,
                              url=history.url,
                              timestamp=time,
                              method=history.request.method,
                              document=history.content,
                              status_code=history.status_code,
                              reason=history.reason,
                              cookies=history.cookies.get_dict(),
                              request=dict(history.request.headers),
                              response=dict(history.headers))
        except Exception:
            logger.pexc(LOG_WARNING, category=DatabaseOperaionFailed, line='submit_requests(...)')

    metadata = link.asdict()
    ts = time.isoformat()

    if html:
        path = f'{link.base}/{link.name}_{ts}_raw.html'
    else:
        path = f'{link.base}/{link.name}_{ts}.dat'

    data = {
        '[metadata]': metadata,
        'Timestamp': ts,
        'URL': link.url,
        'Method': response.request.method,
        'Status-Code': response.status_code,
        'Reason': response.reason,
        'Cookies': [vars(cookie) for cookie in response.cookies],
        'Session': [vars(cookie) for cookie in session.cookies],
        'Request': dict(response.request.headers),
        'Response': dict(response.headers),
        'Content-Type': mime_type,
        'Document': {
            'path': os.path.relpath(path, PATH_DB),
            'data': base64.b64encode(content).decode(),
        },
        'History': [{
            'URL': history.url,
            'Method': history.request.method,
            'Status-Code': history.status_code,
            'Reason': history.reason,
            'Cookies': history.cookies.get_dict(),
            'Request': dict(history.request.headers),
            'Response': dict(history.headers),
            'Document': base64.b64encode(history.content).decode(),
        } for history in response.history],
    }
    logger.plog(LOG_DEBUG, '-*- REQUESTS DATA -*-', object=data)

    if API_REQUESTS is None:
        save_submit('requests', data)
        return

    # submit data
    submit(API_REQUESTS, 'requests', data)


def submit_selenium(time: 'datetime', link: 'darc_link.Link',
                    html: str, screenshot: 'Optional[str]') -> None:
    """Submit selenium data.

    After crawling with :mod:`requests`, we'll then render the URl using
    :mod:`selenium` with Google Chrome and its web driver, to provide a fully
    rendered web page. Such information will be submitted to the web UI.

    Args:
        time (datetime.datetime): Timestamp of submission.
        link: Link object of submission.
        html: HTML source of the web page.
        screenshot: *base64* encoded screenshot.

    If :data:`~darc.submit.API_SELENIUM` is :data:`None`, the data for submission
    will directly be save through :func:`~darc.submit.save_submit`.

    Note:
        This information is optional, only provided if the content type from
        :mod:`requests` is HTML, status code not between ``400`` and ``600``, and
        HTML data not empty.

    The data submitted should have following format:

    .. code-block::

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
                "name": ...,
                // originate URL - <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
                "backref": ...
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
        * :func:`darc.submit.get_html`
        * :func:`darc.submit.get_screenshot`
        * :func:`darc.crawl.loader`

    """
    if SAVE_DB:
        try:
            model, model_created = cast('Tuple[HostnameModel, bool]',
                                        _db_operation(HostnameModel.get_or_create, hostname=link.host, defaults={
                                            'proxy': Proxy[link.proxy.upper()],
                                            'discovery': time,
                                            'last_seen': time,
                                        }))
            if not model_created:
                model.last_seen = time
                _db_operation(model.save)

            url, url_created = cast('Tuple[URLModel, bool]',
                                    _db_operation(URLModel.get_or_create, hash=link.name, defaults={
                                        'url': link.url,
                                        'hostname': model,
                                        'proxy': Proxy[link.proxy.upper()],
                                        'discovery': time,
                                        'last_seen': time,
                                        'alive': True,
                                        'since': time,
                                    }))
            if not url.alive:
                url.alive = True
                url.since = time
            if not url_created:
                url.last_seen = time
            _db_operation(url.save)

            if link.url_backref is not None:
                with contextlib.suppress(peewee.IntegrityError):
                    _db_operation(URLThroughModel.create,
                                  parent=_db_operation(URLModel.get_by_url, link.url_backref.url),
                                  child=url)

            _db_operation(SeleniumModel.create,
                          url=url,
                          timestamp=time,
                          document=html,
                          screenshot=base64.b64decode(screenshot) if screenshot else None)
        except Exception:
            logger.pexc(LOG_WARNING, category=DatabaseOperaionFailed, line='submit_selenium(...)')

    metadata = link.asdict()
    ts = time.isoformat()

    if screenshot is None:
        ss = None  # type: Optional[File]
    else:
        ss = {
            'path': os.path.relpath(f'{link.base}/{link.name}_{ts}.png', PATH_DB),
            'data': screenshot,
        }

    data = {
        '[metadata]': metadata,
        'Timestamp': ts,
        'URL': link.url,
        'Document': {
            'path': os.path.relpath(f'{link.base}/{link.name}_{ts}.html', PATH_DB),
            'data': base64.b64encode(html.encode()).decode(),
        },
        'Screenshot': ss,
    }
    logger.plog(LOG_DEBUG, '-*- SELENIUM DATA -*-', object=data)

    if API_SELENIUM is None:
        save_submit('selenium', data)
        return

    # submit data
    submit(API_SELENIUM, 'selenium', data)
