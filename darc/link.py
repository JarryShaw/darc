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


def quote(string: typing.AnyStr, safe: typing.AnyStr = '/',
          encoding: typing.Optional[str] = None, errors: typing.Optional[str] = None) -> str:
    """Wrapper function for ``urllib.parse.quote``."""
    with contextlib.suppress():
        return urllib.parse.quote(string, safe, encoding=encoding, errors=errors)
    return string


def unquote(string: typing.AnyStr, encoding: str = 'utf-8', errors: str = 'replace') -> str:
    """Wrapper function for ``urllib.parse.unquote``."""
    with contextlib.suppress():
        return urllib.parse.unquote(string, encoding=encoding, errors=errors)
    return string


def urljoin(base: typing.AnyStr, url: typing.AnyStr, allow_fragments: bool = True) -> str:
    """Wrapper function for ``urllib.parse.urljoin``."""
    with contextlib.suppress(ValueError):
        return urllib.parse.urljoin(base, url, allow_fragments=allow_fragments)
    return f'{base}/{url}'


def urlparse(url: str, scheme: str = '', allow_fragments: bool = True) -> urllib.parse.ParseResult:
    """Wrapper function for ``urllib.parse.urlparse``."""
    with contextlib.suppress(ValueError):
        return urllib.parse.urlparse(url, scheme, allow_fragments=allow_fragments)
    return urllib.parse.ParseResult(scheme=scheme, netloc='', path=url, params='', query='', fragment='')


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

    hostname = host or '(null)'
    # proxy type by scheme
    if parse.scheme == 'data':
        # https://en.wikipedia.org/wiki/Data_URI_scheme
        proxy_type = 'data'
        hostname = 'data'
    elif parse.scheme == 'javascript':
        proxy_type = 'script'
    elif parse.scheme == 'bitcoin':
        proxy_type = 'bitcoin'
    elif parse.scheme == 'ed2k':
        proxy_type = 'ed2k'
    elif parse.scheme == 'magnet':
        proxy_type = 'magnet'
    elif parse.scheme == 'mailto':
        proxy_type = 'mail'
    elif parse.scheme == 'irc':
        proxy_type = 'irc'
    elif parse.scheme not in ['http', 'https']:
        proxy_type = parse.scheme
    # proxy type by hostname
    elif host is None:
        hostname = '(null)'
        proxy_type = 'null'
    elif re.fullmatch(r'.*?\.onion', host):
        proxy_type = 'tor'
    elif re.fullmatch(r'.*?\.i2p', host):
        proxy_type = 'i2p'
    elif host in ['127.0.0.1:7657', '127.0.0.1:7658',
                  'localhost:7657', 'localhost:7658']:
        # c.f. https://geti2p.net/en/docs/api/i2ptunnel
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
    # fallback
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
