# -*- coding: utf-8 -*-
"""Source Saving
===================

The :mod:`darc.save` module contains the core utilities
for managing fetched files and documents.

The data storage under the root path (:data:`~darc.const.PATH_DB`)
is typically as following::

    data
    ├── api
    |   └── <date>
    │       └── <proxy>
    │           └── <scheme>
    │               └── <hostname>
    │                   ├── new_host
    │                   │   └── <hash>_<timestamp>.json
    │                   ├── requests
    │                   │   └── <hash>_<timestamp>.json
    │                   └── selenium
    │                       └── <hash>_<timestamp>.json
    ├── link.csv
    ├── misc
    │   ├── bitcoin.txt
    │   ├── data
    │   │   └── <hash>_<timestamp>.<ext>
    │   ├── ed2k.txt
    │   ├── invalid.txt
    │   ├── irc.txt
    │   ├── magnet.txt
    │   └── mail.txt
    └── <proxy>
        └── <scheme>
            └── <hostname>
                ├── <hash>_<timestamp>.json
                ├── robots.txt
                └── sitemap_<hash>.xml

"""

import dataclasses
import json
import os

import darc.typing as typing
from darc._compat import datetime
from darc.const import PATH_DB, PATH_LN, get_lock
from darc.link import Link, quote

# lock for file I/O
_SAVE_LOCK = get_lock()


def sanitise(link: Link, time: typing.Optional[typing.Datetime] = None,  # pylint: disable=redefined-outer-name
             raw: bool = False, data: bool = False,
             headers: bool = False, screenshot: bool = False) -> str:
    """Sanitise link to path.

    Args:
        link: Link object to sanitise the path
        time (datetime): Timestamp for the path.
        raw: If this is a raw HTML document from :mod:`requests`.
        data: If this is a generic content type document.
        headers: If this is response headers from :mod:`requests`.
        screenshot: If this is the screenshot from :mod:`selenium`.

    Returns:
        * If ``raw`` is :data:`True`,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>_raw.html``.
        * If ``data`` is :data:`True`,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.dat``.
        * If ``headers`` is :data:`True`,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.json``.
        * If ``screenshot`` is :data:`True`,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.png``.
        * If none above,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.html``.

    See Also:
        * :func:`darc.crawl.crawler`
        * :func:`darc.crawl.loader`

    """
    os.makedirs(link.base, exist_ok=True)

    path = os.path.join(link.base, link.name)
    if time is None:
        time = datetime.now()
    ts = time.isoformat()

    if raw:
        return f'{path}_{ts}_raw.html'
    if headers:
        return f'{path}_{ts}.json'
    if data:
        return f'{path}_{ts}.dat'
    if screenshot:
        return f'{path}_{ts}.png'
    return f'{path}_{ts}.html'


def save_link(link: Link) -> None:
    """Save link hash database ``link.csv``.

    The CSV file has following fields:

    * proxy type: :attr:`link.proxy <darc.link.Link.proxy>`
    * URL scheme: :attr:`link.url_parse.scheme <darc.link.Link.url_parse>`
    * hostname: :attr:`link.base <darc.link.Link.base>`
    * link hash: :attr:`link.name <darc.link.Link.name>`
    * original URL: :attr:`link.url <darc.link.Link.url>`

    Args:
        link: Link object to be saved.

    See Also:
        * :data:`darc.const.PATH_LN`
        * :data:`darc.save._SAVE_LOCK`

    """
    with _SAVE_LOCK:  # type: ignore
        with open(PATH_LN, 'a') as file:
            print(f'{link.proxy},{link.url_parse.scheme},{os.path.split(link.base)[1]},'
                  f'{link.name},{quote(link.url)}', file=file)


def save_headers(time: typing.Datetime, link: Link,
                 response: typing.Response, session: typing.Session) -> str:  # pylint: disable=redefined-outer-name
    """Save HTTP response headers.

    Args:
        time (datetime): Timestamp of response.
        link: Link object of response.
        response (:class:`requests.Response`): Response object to be saved.
        session (:class:`requests.Session`): Session object of response.

    Returns:
        Saved path to response headers, i.e.
        ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.json``.

    The JSON data saved is as following:

    .. code-block:: json

        {
            "[metadata]": {
                "url": "...",
                "proxy": "...",
                "host": "...",
                "base": "...",
                "name": "..."
            },
            "Timestamp": "...",
            "URL": "...",
            "Method": "GET",
            "Status-Code": "...",
            "Reason": "...",
            "Cookies": {
                "...": "..."
            },
            "Session": {
                "...": "..."
            },
            "Request": {
                "...": "..."
            },
            "Response": {
                "...": "..."
            },
            "History": [
                {"...": "..."}
            ]
        }

    See Also:
        * :func:`darc.save.sanitise`
        * :func:`darc.crawl.crawler`

    """
    metadata = dataclasses.asdict(link)
    metadata['base'] = os.path.relpath(link.base, PATH_DB)
    del metadata['url_parse']

    data = {
        '[metadata]': metadata,
        'Timestamp': time.isoformat(),
        'URL': response.url,
        'Method': response.request.method,
        'Status-Code': response.status_code,
        'Reason': response.reason,
        'Cookies': response.cookies.get_dict(),
        'Session': session.cookies.get_dict(),
        'Request': dict(response.request.headers),
        'Response': dict(response.headers),
        'History': [{
            'URL': history.url,
            'Method': history.request.method,
            'Status-Code': history.status_code,
            'Reason': history.reason,
            'Cookies': history.cookies.get_dict(),
            'Request': dict(history.request.headers),
            'Response': dict(history.headers),
        } for history in response.history],
    }

    path = sanitise(link, time, headers=True)
    with open(path, 'w') as file:
        json.dump(data, file, indent=2)

    save_link(link)
    return path
