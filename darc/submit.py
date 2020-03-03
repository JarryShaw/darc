# -*- coding: utf-8 -*-
"""Submit crawled data to web UI."""

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
    """Generate metadata field."""
    metadata = dataclasses.asdict(link)
    metadata['base'] = os.path.relpath(link.base, PATH_DB)
    del metadata['url_parse']
    return metadata


def get_robots(link: Link) -> typing.Optional[File]:  # pylint: disable=inconsistent-return-statements
    """Read ``robots.txt``."""
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
    """Read ``sitemap.xml``."""
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
    """Read raw document."""
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
    """Read HTML document."""
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
    """Read screenshot picture."""
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
    """Save failed submit data."""
    metadata = data['[metadata]']
    name = metadata['name']
    ts = data['Timestamp']

    root = os.path.join(PATH_API, metadata['base'], domain)
    os.makedirs(root, exist_ok=True)

    with open(os.path.join(root, f'{name}_{ts}.json'), 'w') as file:
        json.dump(data, file, indent=2)


def submit(api: str, domain: Domain, data: typing.Dict[str, typing.Any]):
    """Submit data."""
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
    """Submit new host."""
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
    """Submit requests data."""
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
    """Submit selenium data."""
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
