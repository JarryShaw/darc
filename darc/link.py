# -*- coding: utf-8 -*-
"""URL Utilities
===================

The :class:`~darc.link.Link` class is the key data structure
of the :mod:`darc` project, it contains all information
required to identify a URL's proxy type, hostname, path prefix
when saving, etc.

The :mod:`~darc.link` module also provides several wrapper
function to the :mod:`urllib.parse` module.

"""

import contextlib
import dataclasses
import functools
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
    from pathlib import PurePosixPath as PosixPath  # type: ignore


def quote(string: typing.AnyStr, safe: typing.AnyStr = '/',  # type: ignore
          encoding: typing.Optional[str] = None, errors: typing.Optional[str] = None) -> str:
    """Wrapper function for :func:`urllib.parse.quote`.

    Args:
        string: string to be quoted
        safe: charaters not to escape
        encoding: string encoding
        errors: encoding error handler

    Returns:
        The quoted string.

    Note:
        The function suppressed possible errors when calling
        :func:`urllib.parse.quote`. If any, it will return
        the original string.

    """
    with contextlib.suppress(Exception):
        return urllib.parse.quote(string, safe, encoding=encoding, errors=errors)  # type: ignore
    return str(string)


def unquote(string: typing.AnyStr, encoding: str = 'utf-8', errors: str = 'replace') -> str:
    """Wrapper function for :func:`urllib.parse.unquote`.

    Args:
        string: string to be unquoted
        encoding: string encoding
        errors: encoding error handler

    Returns:
        The quoted string.

    Note:
        The function suppressed possible errors when calling
        :func:`urllib.parse.unquote`. If any, it will return
        the original string.

    """
    with contextlib.suppress(Exception):
        return urllib.parse.unquote(string, encoding=encoding, errors=errors)  # type: ignore
    return str(string)


def urljoin(base: typing.AnyStr, url: typing.AnyStr, allow_fragments: bool = True) -> str:
    """Wrapper function for :func:`urllib.parse.urljoin`.

    Args:
        base: base URL
        url: URL to be joined
        allow_fragments: if allow fragments

    Returns:
        The joined URL.

    Note:
        The function suppressed possible errors when calling
        :func:`urllib.parse.urljoin`. If any, it will return
        ``base/url`` directly.

    """
    with contextlib.suppress(ValueError):
        return urllib.parse.urljoin(base, url, allow_fragments=allow_fragments)  # type: ignore
    return f'{str(base)}/{str(url)}'


def urlparse(url: str, scheme: str = '', allow_fragments: bool = True) -> urllib.parse.ParseResult:
    """Wrapper function for :func:`urllib.parse.urlparse`.

    Args:
        url: URL to be parsed
        scheme: URL scheme
        allow_fragments: if allow fragments

    Returns:
        The parse result.

    Note:
        The function suppressed possible errors when calling
        :func:`urllib.parse.urlparse`. If any, it will return
        ``urllib.parse.ParseResult(scheme=scheme, netloc='', path=url, params='', query='', fragment='')``
        directly.

    """
    with contextlib.suppress(ValueError):
        return urllib.parse.urlparse(url, scheme, allow_fragments=allow_fragments)
    return urllib.parse.ParseResult(scheme=scheme, netloc='', path=url, params='', query='', fragment='')


def urlsplit(url: str, scheme: str = '', allow_fragments: bool = True) -> urllib.parse.SplitResult:
    """Wrapper function for :func:`urllib.parse.urlsplit`.

    Args:
        url: URL to be split
        scheme: URL scheme
        allow_fragments: if allow fragments

    Returns:
        The split result.

    Note:
        The function suppressed possible errors when calling
        :func:`urllib.parse.urlsplit`. If any, it will return
        ``urllib.parse.SplitResult(scheme=scheme, netloc='', path=url, params='', query='', fragment='')``
        directly.

    """
    with contextlib.suppress(ValueError):
        return urllib.parse.urlsplit(url, scheme, allow_fragments=allow_fragments)
    return urllib.parse.SplitResult(scheme=scheme, netloc='', path=url, query='', fragment='')


@dataclasses.dataclass
@functools.total_ordering
class Link:
    """Parsed link.

    Args:
        url: original link
        proxy: proxy type
        host: URL's hostname
        base: base folder for saving files
        name: hashed link for saving files
        url_parse: parsed URL from :func:`urllib.parse.urlparse`

    Returns:
        :class:`~darc.link.Link`: Parsed link object.

    Note:
        :class:`~darc.link.Link` is a `dataclass`_ object.
        It is safely *hashable*, through :func:`hash(url) <hash>`.

        .. _dataclass: https://www.python.org/dev/peps/pep-0557

    """

    #: original link
    url: str
    #: proxy type
    proxy: str

    #: parsed URL from :func:`urllib.parse.urlparse`
    url_parse: urllib.parse.ParseResult

    #: URL's hostname
    host: str
    #: base folder for saving files
    base: str
    #: hashed link for saving files
    name: str

    def __hash__(self) -> int:
        """Provide hash support to the :class:`~darc.link.Link` object."""
        return hash(self.url)

    def __str__(self) -> str:
        return self.url

    def __eq__(self, value: typing.Any) -> bool:
        if isinstance(value, Link):
            return self.url == value.url
        return False

    def __lt__(self, value: typing.Any) -> bool:
        if isinstance(value, Link):
            return self.url < value.url
        raise TypeError(f"'<' not supported between instances of 'Link' and {type(value).__name__!r}")


def parse_link(link: str, host: typing.Optional[str] = None) -> Link:
    """Parse link.

    Args:
        link: link to be parsed
        host: hostname of the link

    Returns:
        The parsed link object.

    Note:
        If ``host`` is provided, it will override the hostname
        of the original ``link``.

    The parsing process of proxy type is as follows:

    0.  If ``host`` is :data:`None` and the parse result from :func:`urllib.parse.urlparse`
        has no ``netloc`` (or hostname) specified, then set ``hostname``
        as ``(null)``; else set it as is.
    1.  If the scheme is ``data``, then the ``link`` is a data URI,
        set ``hostname`` as ``data`` and ``proxy`` as ``data``.
    2.  If the scheme is ``javascript``, then the link is some
        JavaScript codes, set ``proxy`` as ``script``.
    3.  If the scheme is ``bitcoin``, then the link is a Bitcoin
        address, set ``proxy`` as ``bitcoin``.
    4.  If the scheme is ``ed2k``, then the link is an ED2K magnet
        link, set ``proxy`` as ``ed2k``.
    5.  If the scheme is ``magnet``, then the link is a magnet
        link, set ``proxy`` as ``magnet``.
    6.  If the scheme is ``mailto``, then the link is an email
        address, set ``proxy`` as ``mail``.
    7.  If the scheme is ``irc``, then the link is an IRC
        link, set ``proxy`` as ``irc``.
    8.  If the scheme is **NOT** any of ``http`` or ``https``,
        then set ``proxy`` to the scheme.
    9.  If the host is :data:`None`, set ``hostname`` to ``(null)``,
        set ``proxy`` to ``null``.
    10. If the host is an onion (``.onion``) address,
        set ``proxy`` to ``tor``.
    11. If the host is an I2P (``.i2p``) address, or
        any of ``localhost:7657`` and ``localhost:7658``,
        set ``proxy`` to ``i2p``.
    12. If the host is *localhost* on :data:`~darc.proxy.zeronet.ZERONET_PORT`,
        and the path is not ``/``, i.e. **NOT** root path, set ``proxy``
        to ``zeronet``; and set the first part of its path as ``hostname``.

        Example:

           For a ZeroNet address, e.g.
           http://127.0.0.1:43110/1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D,
           :func:`~darc.link.parse_link` will parse the ``hostname`` as
           ``1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D``.

    13. If the host is *localhost* on :data:`~darc.proxy.freenet.FREENET_PORT`,
        and the path is not ``/``, i.e. **NOT** root path, set ``proxy``
        to ``freenet``; and set the first part of its path as ``hostname``.

        Example:

           For a Freenet address, e.g.
           http://127.0.0.1:8888/USK@nwa8lHa271k2QvJ8aa0Ov7IHAV-DFOCFgmDt3X6BpCI,DuQSUZiI~agF8c-6tjsFFGuZ8eICrzWCILB60nT8KKo,AQACAAE/sone/77/,
           :func:`~darc.link.parse_link` will parse the ``hostname`` as
           ``USK@nwa8lHa271k2QvJ8aa0Ov7IHAV-DFOCFgmDt3X6BpCI,DuQSUZiI~agF8c-6tjsFFGuZ8eICrzWCILB60nT8KKo,AQACAAE``.

    14. If the host is a proxied onion (``.onion.sh``) address,
        set ``proxy`` to ``tor2web``.
    15. If none of the cases above satisfied, the ``proxy`` will be set
        as ``null``, marking it a plain normal link.

    The ``base`` for parsed link :class:`~darc.link.Link` object is defined as

    .. code-block::

        <root>/<proxy>/<scheme>/<hostname>/

    where ``root`` is :data:`~darc.const.PATH_DB`.

    The ``name`` for parsed link :class:`~darc.link.Link` object is
    the sha256 hash (c.f. :func:`hashlib.sha256`) of the original ``link``.

    """
    from darc.proxy.freenet import FREENET_PORT  # pylint: disable=import-outside-toplevel
    from darc.proxy.zeronet import ZERONET_PORT  # pylint: disable=import-outside-toplevel

    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urlparse(link)
    if host is None:
        host = parse.netloc or parse.hostname

    hostname = host or '(null)'
    scheme = parse.scheme.casefold()

    # proxy type by scheme
    if scheme == 'data':
        # https://en.wikipedia.org/wiki/Data_URI_scheme
        proxy_type = 'data'
        host = '(data)'
    elif scheme == 'javascript':
        proxy_type = 'script'
        host = '(script)'
    elif scheme == 'bitcoin':
        proxy_type = 'bitcoin'
        host = '(bitcoin)'
    elif scheme == 'ed2k':
        proxy_type = 'ed2k'
        host = '(ed2k)'
    elif scheme == 'magnet':
        proxy_type = 'magnet'
        host = '(magnet)'
    elif scheme == 'mailto':
        proxy_type = 'mail'
        host = '(mail)'
    elif scheme == 'tel':
        proxy_type = 'tel'
        host = '(tel)'
    elif scheme == 'irc':
        proxy_type = 'irc'
        host = '(irc)'
    elif scheme in ('ws', 'wss'):
        proxy_type = scheme
        host = '(ws)'
    elif scheme not in ['http', 'https']:
        proxy_type = scheme
    # proxy type by hostname
    elif host is None:
        hostname = '(null)'
        proxy_type = 'null'
    elif re.fullmatch(r'.*?\.onion', host):
        proxy_type = 'tor'
    elif re.fullmatch(r'.*?\.onion\.sh', host):
        proxy_type = 'tor2web'
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
    base = os.path.join(PATH_DB, proxy_type, scheme, hostname)
    name = hashlib.sha256(link.encode()).hexdigest()

    return Link(
        url=link,
        url_parse=parse,
        host=host,  # type: ignore
        base=base,
        name=name,
        proxy=proxy_type,
    )
