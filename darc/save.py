# -*- coding: utf-8 -*-
"""Source Saving
===================

The :mod:`darc.save` module contains the core utilities
for managing fetched files and documents.

The data storage under the root path (:data:`~darc.const.PATH_DB`)
is typically as following::

    data
    ├── _queue_requests.txt
    ├── _queue_requests.txt.tmp
    ├── _queue_selenium.txt
    ├── _queue_selenium.txt.tmp
    ├── api
    │   └── <proxy>
    │       └── <scheme>
    │           └── <hostname>
    │               ├── new_host
    │               │   └── <hash>_<timestamp>.json
    │               ├── requests
    │               │   └── <hash>_<timestamp>.json
    │               └── selenium
    │                   └── <hash>_<timestamp>.json
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
                ├── <hash>_<timestamp>.dat
                ├── <hash>_<timestamp>.json
                ├── <hash>_<timestamp>_raw.html
                ├── <hash>_<timestamp>.html
                ├── <hash>_<timestamp>.png
                ├── robots.txt
                └── sitemap_<hash>.xml

"""

import dataclasses
import glob
import json
import multiprocessing
import os
import pathlib
import posixpath

import darc.typing as typing
from darc._compat import datetime
from darc.const import PATH_DB, PATH_LN, TIME_CACHE
from darc.link import Link

# lock for file I/O
#_SAVE_LOCK = MANAGER.Lock()  # pylint: disable=no-member
_SAVE_LOCK = multiprocessing.Lock()


def has_folder(link: Link) -> typing.Optional[str]:  # pylint: disable=inconsistent-return-statements
    """Check if is a new host.

    Args:
        link: Link object to check if is a new host.

    Returns:
        * If ``link`` is a new host, return :attr:`link.base <darc.link.Link.base>`.
        * If not, return ``None``.

    """
    # <proxy>/<scheme>/<host>/<hash>.json
    glob_list = glob.glob(os.path.join(link.base, '*.json'))
    if not glob_list:
        return
    return link.base


def has_robots(link: Link) -> typing.Optional[str]:
    """Check if ``robots.txt`` already exists.

    Args:
        link: Link object to check if ``robots.txt`` already exists.

    Returns:
        * If ``robots.txt`` exists, return the path to ``robots.txt``,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/robots.txt``.
        * If not, return ``None``.

    """
    # <proxy>/<scheme>/<host>/robots.txt
    path = os.path.join(link.base, 'robots.txt')
    return path if os.path.isfile(path) else None


def has_sitemap(link: Link) -> typing.Optional[str]:
    """Check if sitemap already exists.

    Args:
        link: Link object to check if sitemap already exists.

    Returns:
        * If sitemap exists, return the path to the sitemap,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/sitemap_<hash>.xml``.
        * If not, return ``None``.

    """
    # <proxy>/<scheme>/<host>/sitemap_<hash>.xml
    path = os.path.join(link.base, f'sitemap_{link.name}.xml')
    return path if os.path.isfile(path) else None


def has_raw(time: typing.Datetime, link: Link) -> typing.Optional[str]:  # pylint: disable=redefined-outer-name
    """Check if we need to re-craw the link by |requests|_.

    Args:
        link: Link object to check if we need to re-craw the link by |requests|_.

    Returns:
        * If no need, return the path to the document,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>_raw.html``,
          or ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.dat``.
        * If needed, return ``None``.

    See Also:
        * :data:`darc.const.TIME_CACHE`

    """
    path = os.path.join(link.base, link.name)
    if data_list := glob.glob(f'{path}_*.dat'):
        return data_list[0]

    temp_list = glob.glob(f'{path}_*_raw.html')
    glob_list = sorted((pathlib.Path(item) for item in temp_list), reverse=True)

    if not glob_list:
        return None

    # disable caching
    if TIME_CACHE is None:
        return glob_list[0]

    for item in glob_list:
        item_date = item.stem.split('_')[1]
        date = datetime.fromisoformat(item_date)
        if time - date <= TIME_CACHE:
            return item
    return None


def has_html(time: typing.Datetime, link: Link) -> typing.Optional[str]:  # pylint: disable=redefined-outer-name
    """Check if we need to re-craw the link by |selenium|_.

    Args:
        link: Link object to check if we need to re-craw the link by |selenium|_.

    Returns:
        * If no need, return the path to the document,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.html``.
        * If needed, return ``None``.

    See Also:
        * :data:`darc.const.TIME_CACHE`

    """
    path = os.path.join(link.base, link.name)
    temp_list = list()
    for item in glob.glob(f'{path}_*.html'):
        temp = pathlib.Path(item)
        if temp.stem.endswith('_raw'):
            continue
        temp_list.append(temp)
    glob_list = sorted(temp_list, reverse=True)

    if not glob_list:
        return None

    # disable caching
    if TIME_CACHE is None:
        return glob_list[0]

    for item in glob_list:
        item_date = item.stem.split('_')[1]
        date = datetime.fromisoformat(item_date)
        if time - date <= TIME_CACHE:
            return item
    return None


def sanitise(link: Link, time: typing.Optional[typing.Datetime] = None,  # pylint: disable=redefined-outer-name
             raw: bool = False, data: bool = False,
             headers: bool = False, screenshot: bool = False) -> str:
    """Sanitise link to path.

    Args:
        link: Link object to sanitise the path
        time (datetime): Timestamp for the path.
        raw: If this is a raw HTML document from |requests|_.
        data: If this is a generic content type document.
        headers: If this is response headers from |requests|_.
        screenshot: If this is the screenshot from |selenium|_.

    Returns:
        * If ``raw`` is ``True``,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>_raw.html``.
        * If ``data`` is ``True``,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.dat``.
        * If ``headers`` is ``True``,
          ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.json``.
        * If ``screenshot`` is ``True``,
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


def save_link(link: Link):
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
    with _SAVE_LOCK:
        with open(PATH_LN, 'a') as file:
            print(f'{link.proxy} {link.url_parse.scheme} {os.path.split(link.base)[1]} {link.name} {link}', file=file)


def save_robots(link: Link, text: str) -> str:
    """Save ``robots.txt``.

    Args:
        link: Link object of ``robots.txt``.
        text: Content of ``robots.txt``.

    Returns:
        Saved path to ``robots.txt``, i.e.
        ``<root>/<proxy>/<scheme>/<hostname>/robots.txt``.

    See Also:
        * :func:`darc.save.sanitise`

    """
    path = os.path.join(link.base, 'robots.txt')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'# {link.url}', file=file)
        file.write(text)
    return path


def save_sitemap(link: Link, text: str) -> str:
    """Save sitemap.

    Args:
        link: Link object of sitemap.
        text: Content of sitemap.

    Returns:
        Saved path to sitemap, i.e.
        ``<root>/<proxy>/<scheme>/<hostname>/sitemap_<hash>.xml``.

    See Also:
        * :func:`darc.save.sanitise`

    """
    # <proxy>/<scheme>/<host>/sitemap_<hash>.xml
    path = os.path.join(link.base, f'sitemap_{link.name}.xml')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'<!-- {link.url} -->', file=file)
        file.write(text)

    save_link(link)
    return path


def save_headers(time: typing.Datetime, link: Link,
                 response: typing.Response, session: typing.Session) -> str:  # pylint: disable=redefined-outer-name
    """Save HTTP response headers.

    Args:
        time (datetime): Timestamp of response.
        link: Link object of response.
        response (|Response|_): Response object to be saved.
        session (|Session|_): Session object of response.

    Returns:
        Saved path to response headers, i.e.
        ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.json``.

    The JSON data saved is as following:

    .. code:: json

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


def save_html(time: typing.Datetime, link: Link, html: typing.Union[str, bytes], raw: bool = False) -> str:  # pylint: disable=redefined-outer-name
    """Save response.

    Args:
        time (datetime): Timestamp of HTML document.
        link: Link object of original URL.
        html: Content of HTML document.
        raw: If is fetched from |requests|_.

    Returns:
        Saved path to HTML document.

        * If ``raw`` is ``True``, ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>_raw.html``.
        * If not, ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.html``.

    See Also:
        * :func:`darc.save.sanitise`
        * :func:`darc.crawl.crawler`
        * :func:`darc.crawl.loader`

    """
    # comment line
    comment = f'<!-- {link.url} -->'

    path = sanitise(link, time, raw=raw)
    if raw:
        with open(path, 'wb') as file:
            file.write(comment.encode())
            file.write(os.linesep.encode())
            file.write(html)
    else:
        with open(path, 'w') as file:
            print(comment, file=file)
            file.write(html)
    return path


def save_file(time: typing.Datetime, link: Link, content: bytes) -> str:
    """Save file.

    The function will also try to make symbolic links from the saved
    file standard path to the relative path as in the URL.

    Args:
        time (datetime): Timestamp of generic file.
        link: Link object of original URL.
        content: Content of generic file.

    Returns:
        Saved path to generic content type file,
        ``<root>/<proxy>/<scheme>/<hostname>/<hash>_<timestamp>.dat``.

    See Also:
        * :func:`darc.save.sanitise`
        * :func:`darc.crawl.crawler`

    """
    # real path
    dest = sanitise(link, time, data=True)
    with open(dest, 'wb') as file:
        file.write(content)

    # remove leading slash '/'
    temp_path = link.url_parse.path[1:]

    # <proxy>/<scheme>/<host>/"..."
    root, name = posixpath.split(temp_path)
    path = os.path.join(link.base, root)
    os.makedirs(path, exist_ok=True)

    # os.chdir(path)
    # with open(name, 'wb') as file:
    #     file.write(content)
    # os.chdir(CWD)

    src = os.path.relpath(dest, path)
    dst = os.path.join(path, name)
    os.symlink(src, dst, target_is_directory=False)

    return dest
