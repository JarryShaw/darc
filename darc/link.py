# -*- coding: utf-8 -*-
"""URL utilities."""

import contextlib
import dataclasses
import hashlib
import os
import re
import urllib.parse

import darc.typing as typing
from darc.const import PATH_DB

try:
    from pathlib import PosixPath
    PosixPath(os.curdir)
except NotImplementedError:
    from pathlib import PurePosixPath as PosixPath


def urljoin(base: typing.AnyStr, url: typing.AnyStr, allow_fragments: bool = True) -> str:
    """Wrapper function for ``urllib.parse.urljoin``."""
    with contextlib.suppress(ValueError):
        return urllib.parse.urljoin(base, url, allow_fragments=allow_fragments)
    return f'{base}/{url}'


def urlparse(url: str, scheme: str = '', allow_fragments: bool = True) -> urllib.parse.ParseResult:
    """Wrapper function for ``urllib.parse.urlparse``."""
    with contextlib.suppress(ValueError):
        return urllib.parse.urlparse(url, scheme, allow_fragments=allow_fragments)
    return urllib.parse.ParseResult(scheme=scheme, netloc=url, path='', params='', query='', fragment='')


@dataclasses.dataclass
class Link:
    """Parsed link."""

    # original link
    url: str
    # proxy type
    proxy: str

    # urllib.parse.urlparse
    url_parse: urllib.parse.ParseResult

    # hostname / netloc
    host: str
    # base folder
    base: str
    # hashed link
    name: str

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url


def parse_link(link: str, host: typing.Optional[str] = None) -> Link:
    """Parse link."""
    from darc.proxy.freenet import FREENET_PORT  # pylint: disable=import-outside-toplevel
    from darc.proxy.zeronet import ZERONET_PORT  # pylint: disable=import-outside-toplevel

    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urlparse(link)
    if host is None:
        host = parse.netloc or parse.hostname

    hostname = host
    if host is None:
        hostname = '(null)'
        proxy_type = 'null'
    elif re.fullmatch(r'.*?\.onion', host):
        proxy_type = 'tor'
    elif re.fullmatch(r'.*?\.i2p', host):
        proxy_type = 'i2p'
    # c.f. https://geti2p.net/en/docs/api/i2ptunnel
    elif host in ['127.0.0.1:7657', '127.0.0.1:7658',
                  'localhost:7657', 'localhost:7658']:
        proxy_type = 'i2p'
    elif host in (f'127.0.0.1:{ZERONET_PORT}', f'localhost:{ZERONET_PORT}'):
        # not for root path
        if parse.path in ['', '/']:
            proxy_type = 'null'
        else:
            proxy_type = 'zeronet'
            hostname = PosixPath(parse.path).parts[1]
    elif host in (f'127.0.0.1:{FREENET_PORT}', f'localhost:{FREENET_PORT}'):
        # not for root path
        if parse.path in ['', '/']:
            proxy_type = 'null'
        else:
            proxy_type = 'freenet'
            hostname = PosixPath(parse.path).parts[1]
    else:
        proxy_type = 'null'

    # <proxy>/<scheme>/<host>/<hash>-<timestamp>.html
    base = os.path.join(PATH_DB, proxy_type, parse.scheme, hostname)
    name = hashlib.sha256(link.encode()).hexdigest()

    return Link(
        url=link,
        url_parse=parse,
        host=host,
        base=base,
        name=name,
        proxy=proxy_type,
    )
