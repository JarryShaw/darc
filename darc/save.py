# -*- coding: utf-8 -*-
"""Source saving."""

import contextlib
import dataclasses
import datetime
import glob
import json
import os
import pathlib
import posixpath
import threading

import darc.typing as typing
from darc.const import FLAG_MP, FLAG_TH, MANAGER, PATH_LN, TIME_CACHE
from darc.link import Link

# lock for file I/O
if FLAG_MP:
    _SAVE_LOCK = MANAGER.Lock()  # pylint: disable=no-member
elif FLAG_TH:
    _SAVE_LOCK = threading.Lock()
else:
    _SAVE_LOCK = contextlib.nullcontext()


def has_folder(link: Link) -> typing.Optional[str]:  # pylint: disable=inconsistent-return-statements
    """Check if is a new host."""
    # <scheme>/<host>/sitemap_<hash>.xml
    glob_list = glob.glob(os.path.join(link.base, 'sitemap_*.xml'))
    if not glob_list:
        return
    return link.base


def has_robots(link: Link) -> typing.Optional[str]:
    """Check if robots.txt already exists."""
    # <scheme>/<host>/robots.txt
    path = os.path.join(link.base, 'robots.txt')
    return path if os.path.isfile(path) else None


def has_sitemap(link: Link) -> typing.Optional[str]:
    """Check if sitemap.xml already exists."""
    # <scheme>/<host>/sitemap_<hash>.xml
    path = os.path.join(link.base, f'sitemap_{link.name}.xml')
    return path if os.path.isfile(path) else None


def has_raw(time: typing.Datetime, link: Link) -> typing.Optional[str]:  # pylint: disable=redefined-outer-name
    """Check if we need to re-craw the link by requests."""
    path = os.path.join(link.base, link.name)
    if data_list := glob.glob(f'{path}.dat'):
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
        date = datetime.datetime.fromisoformat(item_date)
        if time - date <= TIME_CACHE:
            return item
    return None


def has_html(time: typing.Datetime, link: Link) -> typing.Optional[str]:  # pylint: disable=redefined-outer-name
    """Check if we need to re-craw the link by selenium."""
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
        date = datetime.datetime.fromisoformat(item_date)
        if time - date <= TIME_CACHE:
            return item
    return None


def sanitise(link: Link, time: typing.Optional[typing.Datetime] = None,  # pylint: disable=redefined-outer-name
             raw: bool = False, data: bool = False, headers: bool = False) -> str:
    """Sanitise link to path."""
    os.makedirs(link.base, exist_ok=True)

    path = os.path.join(link.base, link.name)
    if data:
        return f'{path}.dat'

    if time is None:
        time = datetime.datetime.now()
    ts = time.isoformat()

    if raw:
        return f'{path}_{ts}_raw.html'
    if headers:
        return f'{path}_{ts}.json'
    return f'{path}_{ts}.html'


def save_link(link: Link):
    """Save link hash database."""
    with _SAVE_LOCK:
        with open(PATH_LN, 'a') as file:
            print(f'{link.url_parse.scheme} {os.path.split(link.base)[1]} {link.name} {link}', file=file)


def save_robots(link: Link, text: str) -> str:
    """Save `robots.txt`."""
    path = os.path.join(link.base, 'robots.txt')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'# {link.url}', file=file)
        file.write(text)
    return path


def save_sitemap(link: Link, text: str) -> str:
    """Save `sitemap.xml`."""
    # <scheme>/<host>/sitemap_<hash>.xml
    path = os.path.join(link.base, f'sitemap_{link.name}.xml')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'<!-- {link.url} -->', file=file)
        file.write(text)

    save_link(link)
    return path


def save_headers(time: typing.Datetime, link: Link, response: typing.Response) -> str:  # pylint: disable=redefined-outer-name
    """Save HTTP response headers."""
    metadata = dataclasses.asdict(link)
    del metadata['url_parse']

    data = {
        '[metadata]': metadata,
        'Timestamp': time.isoformat(),
        'URL': response.url,
        'Method': response.request.method,
        'Status-Code': response.status_code,
        'Reason': response.reason,
        'Cookies': response.cookies.get_dict(),
        'Request': dict(response.request.headers),
        'Response': dict(response.headers),
    }

    path = sanitise(link, time, headers=True)
    with open(path, 'w') as file:
        json.dump(data, file, indent=2)

    save_link(link)
    return path


def save_html(time: typing.Datetime, link: Link, html: typing.Union[str, bytes], raw: bool = False) -> str:  # pylint: disable=redefined-outer-name
    """Save response."""
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


def save_file(link: Link, content: bytes) -> str:
    """Save file."""
    # real path
    dest = sanitise(link, data=True)
    with open(dest, 'wb') as file:
        file.write(content)

    # remove leading slash '/'
    temp_path = link.url_parse.path[1:]

    # <scheme>/<host>/...
    root = posixpath.split(temp_path)
    path = os.path.join(link.base, *root[:-1])
    os.makedirs(path, exist_ok=True)

    # os.chdir(path)
    # with open(root[-1], 'wb') as file:
    #     file.write(content)
    # os.chdir(CWD)

    dst = os.path.join(path, root[-1])
    src = os.path.relpath(dest, dst)
    os.symlink(src, dst, target_is_directory=False)

    return dest
