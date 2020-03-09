# -*- coding: utf-8 -*-
"""Source Parsing
====================

The :mod:`darc.parse` module provides auxiliary functions
to read ``robots.txt``, sitemaps and HTML documents. It
also contains utility functions to check if the proxy type,
hostname and content type if in any of the black and white
lists.

"""

import concurrent.futures
import io
import os
import urllib.robotparser

import bs4
import magic
import requests
import stem.util.term

import darc.typing as typing
from darc.const import (CHECK, CHECK_NG, LINK_BLACK_LIST, LINK_WHITE_LIST, MIME_BLACK_LIST,
                        MIME_WHITE_LIST, PROXY_BLACK_LIST, PROXY_WHITE_LIST)
from darc.error import render_error
from darc.link import Link, parse_link, urljoin


def match_proxy(proxy: str) -> bool:
    """Check if proxy type in black list.

    Args:
        proxy: Proxy type to be checked.

    Returns:
        If ``proxy`` in  black list.

    Note:
        If ``proxy`` is ``script``, then it
        will always return ``True``.

    See Also:
        * :data:`darc.const.PROXY_WHITE_LIST`
        * :data:`darc.const.PROXY_BLACK_LIST`

    """
    if proxy == 'script':
        return True

    # any matching white list
    if proxy in PROXY_WHITE_LIST:
        return False

    # any matching black list
    if proxy in PROXY_BLACK_LIST:
        return True

    # fallback
    return False


def match_host(host: str) -> bool:
    """Check if hostname in black list.

    Args:
        host: Hostname to be checked.

    Returns:
        If ``host`` in  black list.

    Note:
        If ``host`` is ``None``, then it
        will always return ``True``.

    See Also:
        * :data:`darc.const.LINK_WHITE_LIST`
        * :data:`darc.const.LINK_BLACK_LIST`

    """
    # invalid hostname
    if host is None:
        return True

    # any matching white list
    if any(pattern.fullmatch(host) is not None for pattern in LINK_WHITE_LIST):
        return False

    # any matching black list
    if any(pattern.fullmatch(host) is not None for pattern in LINK_BLACK_LIST):
        return True

    # fallback
    return False


def match_mime(mime: str) -> bool:
    """Check if content type in black list.

    Args:
        mime: Content type to be checked.

    Returns:
        If ``mime`` in  black list.

    See Also:
        * :data:`darc.const.MIME_WHITE_LIST`
        * :data:`darc.const.MIME_BLACK_LIST`

    """
    # any matching white list
    if any(pattern.fullmatch(mime) is not None for pattern in MIME_WHITE_LIST):
        return False

    # any matching black list
    if any(pattern.fullmatch(mime) is not None for pattern in MIME_BLACK_LIST):
        return True

    # fallback
    return False


def read_robots(link: str, text: str, host: typing.Optional[str] = None) -> typing.List[Link]:
    """Read ``robots.txt`` to fetch link to sitemaps.

    Args:
        link: Original link to ``robots.txt``.
        text: Content of ``robots.txt``.
        host: Hostname of the URL to ``robots.txt``,
            the value may not be same as in ``link``.

    Returns:
        List of link to sitemaps.

    Note:
        If the link to sitemap is not specified in
        ``robots.txt`` [*]_, the fallback link
        ``/sitemap.xml`` will be used.

        .. [*] https://www.sitemaps.org/protocol.html#submit_robots

    """
    rp = urllib.robotparser.RobotFileParser()
    with io.StringIO(text) as file:
        rp.parse(file)

    sitemaps = rp.site_maps()
    if sitemaps is None:
        return [parse_link(urljoin(link, '/sitemap.xml'))]
    return [parse_link(urljoin(link, sitemap), host=host) for sitemap in sitemaps]


def check_robots(link: Link) -> bool:
    """Check if ``link`` is allowed in ``robots.txt``.

    Args:
        link: The link object to be checked.

    Returns:
        If ``link`` is allowed in ``robots.txt``.

    Note:
        The root path of a URL will always return ``True``.

    """
    # bypass robots for root path
    if link.url_parse.path in ['', '/']:
        return True

    robots = os.path.join(link.base, 'robots.txt')
    if os.path.isfile(robots):
        rp = urllib.robotparser.RobotFileParser()
        with open(robots) as file:
            rp.parse(file)
        return rp.can_fetch(requests.utils.default_user_agent(), link.url)
    return True


def get_sitemap(link: str, text: str, host: typing.Optional[str] = None) -> typing.List[Link]:
    """Fetch link to other sitemaps from a sitemap.

    Args:
        link: Original link to the sitemap.
        text: Content of the sitemap.
        host: Hostname of the URL to the sitemap,
            the value may not be same as in ``link``.

    Returns:
        List of link to sitemaps.

    Note:
        As specified in the sitemap protocol,
        it may contain links to other sitemaps. [*]_

        .. [*] https://www.sitemaps.org/protocol.html#index

    """
    sitemaps = list()
    soup = bs4.BeautifulSoup(text, 'html5lib')

    # https://www.sitemaps.org/protocol.html#index
    for loc in soup.select('sitemapindex > sitemap > loc'):
        sitemaps.append(urljoin(link, loc.text))
    return [parse_link(sitemap, host=host) for sitemap in sitemaps]


def _check_ng(temp_list: typing.List[str]) -> typing.List[str]:
    """Check content type of links through ``HEAD`` requests.

    Args:
        temp_list: List of links to be checked.

    Returns:
        List of links matches the requirements.

    See Also:
        * :func:`darc.parse.match_host`
        * :func:`darc.parse.match_proxy`
        * :func:`darc.parse.match_mime`

    """
    from darc.crawl import request_session  # pylint: disable=import-outside-toplevel

    session_map = dict()
    result_list = list()
    for item in temp_list:
        link = parse_link(item)
        if match_host(link.host):
            continue
        if match_proxy(link.proxy):
            continue

        # get session
        session = session_map.get(link.proxy)
        if session is None:
            session = request_session(link, futures=True)
            session_map[link.proxy] = session

        result = session.head(link.url)
        result_list.append(result)

        print(f'[HEAD] Checking content type from {link.url}')

    link_list = list()
    for result in concurrent.futures.as_completed(result_list):
        try:
            response: typing.Response = result.result()
        except requests.RequestException as error:
            if error.response is None:
                print(render_error(f'[HEAD] Checking failed <{error}>',
                                   stem.util.term.Color.RED))  # pylint: disable=no-member
                continue
            print(render_error(f'[HEAD] Failed on {error.response.url} <{error}>',
                               stem.util.term.Color.RED))  # pylint: disable=no-member
            link_list.append(error.response.url)
            continue
        ct_type = get_content_type(response)

        print(f'[HEAD] Checked content type from {response.url} ({ct_type})')

        if match_mime(ct_type):
            continue
        link_list.append(response.url)
    return link_list


def _check(temp_list: typing.List[str]) -> typing.List[str]:
    """Check hostname and proxy type of links.

    Args:
        temp_list: List of links to be checked.

    Returns:
        List of links matches the requirements.

    Note:
        If :data:`~darc.const.CHECK_NG` is ``True``,
        the function will directly call :func:`~darc.parse._check_ng`
        instead.

    See Also:
        * :func:`darc.parse.match_host`
        * :func:`darc.parse.match_proxy`

    """
    if CHECK_NG:
        return _check_ng(temp_list)

    link_list = list()
    for item in temp_list:
        link = parse_link(item)
        if match_host(link.host):
            continue
        if match_proxy(link.proxy):
            continue
        link_list.append(link.url)
    return link_list


def read_sitemap(link: str, text: str, check: bool = CHECK) -> typing.Iterator[str]:
    """Read sitemap.

    Args:
        link: Original link to the sitemap.
        text: Content of the sitemap.
        check: If perform checks on extracted links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of links extracted.

    See Also:
        * :func:`darc.parse._check`
        * :func:`darc.parse._check_ng`

    """
    soup = bs4.BeautifulSoup(text, 'html5lib')

    # https://www.sitemaps.org/protocol.html
    temp_list = [urljoin(link, loc.text) for loc in soup.select('urlset > url > loc')]

    # check content / proxy type
    if check:
        link_list = _check(temp_list)
    else:
        link_list = temp_list.copy()
    yield from set(link_list)


def get_content_type(response: typing.Response) -> str:
    """Get content type from ``response``.

    Args:
        response (|Response|_): Response object.

    Returns:
        The content type from ``response``.

    Note:
        If the ``Content-Type`` header is not defined in ``response``,
        the function will utilise |magic|_ to detect its content type.

    .. |Response| replace:: ``requests.Response``.
    .. _Response: https://requests.readthedocs.io/en/latest/api/index.html#requests.Response

    .. |magic| replace:: ``magic``
    .. _magic: https://pypi.org/project/python-magic/

    """
    ct_type = response.headers.get('Content-Type')
    if ct_type is None:
        try:
            ct_type = magic.detect_from_content(response.content).mime_type
        except Exception:
            ct_type = '(null)'
    return ct_type.casefold().split(';', maxsplit=1)[0].strip()


def extract_links(link: str, html: typing.Union[str, bytes], check: bool = CHECK) -> typing.Iterator[str]:
    """Extract links from HTML document.

    Args:
        link: Original link of the HTML document.
        html: Content of the HTML document.
        check: If perform checks on extracted links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        An iterator of extracted links.

    See Also:
        * :func:`darc.parse._check`
        * :func:`darc.parse._check_ng`

    """
    soup = bs4.BeautifulSoup(html, 'html5lib')

    temp_list = list()
    for child in soup.find_all(lambda tag: tag.has_attr('href') or tag.has_attr('src')):
        if (href := child.get('href', child.get('src'))) is None:
            continue
        temp_list.append(urljoin(link, href))

    # check content / proxy type
    if check:
        link_list = _check(temp_list)
    else:
        link_list = temp_list.copy()
    yield from set(link_list)
