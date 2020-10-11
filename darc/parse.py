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
import json
import os
import re

import bs4
import magic
import requests
import stem.util.term

import darc.typing as typing
from darc._compat import RobotFileParser
from darc.const import (CHECK, CHECK_NG, LINK_BLACK_LIST, LINK_FALLBACK, LINK_WHITE_LIST,
                        MIME_BLACK_LIST, MIME_FALLBACK, MIME_WHITE_LIST, PROXY_BLACK_LIST,
                        PROXY_FALLBACK, PROXY_WHITE_LIST)
from darc.error import render_error
from darc.link import Link, parse_link, urljoin, urlsplit

# Regular expression patterns to match all reasonable URLs.
URL_PAT = [
    # HTTP(S) and other *regular* URLs, e.g. WebSocket, IRC, etc.
    re.compile(r'(?P<url>((https?|wss?|irc):)?(//)?\w+(\.\w+)+/?\S*)', re.UNICODE),
    # bitcoin / data / ed2k / magnet / mail / script / tel, etc.
    re.compile(r'(?P<url>(bitcoin|data|ed2k|magnet|mailto|script|tel):\w+)', re.ASCII),
]
URL_PAT.extend(re.compile(pattern, re.RegexFlag(flags))  # pattern string + compiling flags
               for pattern, flags in json.loads(os.getenv('DARC_URL_PAT', '[]')))


def match_proxy(proxy: str) -> bool:
    """Check if proxy type in black list.

    Args:
        proxy: Proxy type to be checked.

    Returns:
        If ``proxy`` in  black list.

    Note:
        If ``proxy`` is ``script``, then it
        will always return :data:`True`.

    See Also:
        * :data:`darc.const.PROXY_WHITE_LIST`
        * :data:`darc.const.PROXY_BLACK_LIST`
        * :data:`darc.const.PROXY_FALLBACK`

    """
    if proxy == 'script':
        return True

    # any matching black list
    if proxy in PROXY_BLACK_LIST:
        return True

    # any matching white list
    if proxy in PROXY_WHITE_LIST:
        return False

    # fallback
    return PROXY_FALLBACK


def match_host(host: str) -> bool:
    """Check if hostname in black list.

    Args:
        host: Hostname to be checked.

    Returns:
        If ``host`` in  black list.

    Note:
        If ``host`` is :data:`None`, then it
        will always return :data:`True`.

    See Also:
        * :data:`darc.const.LINK_WHITE_LIST`
        * :data:`darc.const.LINK_BLACK_LIST`
        * :data:`darc.const.LINK_FALLBACK`

    """
    # invalid hostname
    if host is None:
        return True  # type: ignore

    # any matching black list
    if any(pattern.fullmatch(host) is not None for pattern in LINK_BLACK_LIST):
        return True

    # any matching white list
    if any(pattern.fullmatch(host) is not None for pattern in LINK_WHITE_LIST):
        return False

    # fallback
    return LINK_FALLBACK


def match_mime(mime: str) -> bool:
    """Check if content type in black list.

    Args:
        mime: Content type to be checked.

    Returns:
        If ``mime`` in  black list.

    See Also:
        * :data:`darc.const.MIME_WHITE_LIST`
        * :data:`darc.const.MIME_BLACK_LIST`
        * :data:`darc.const.MIME_FALLBACK`

    """
    # any matching black list
    if any(pattern.fullmatch(mime) is not None for pattern in MIME_BLACK_LIST):
        return True

    # any matching white list
    if any(pattern.fullmatch(mime) is not None for pattern in MIME_WHITE_LIST):
        return False

    # fallback
    return MIME_FALLBACK


def check_robots(link: Link) -> bool:
    """Check if ``link`` is allowed in ``robots.txt``.

    Args:
        link: The link object to be checked.

    Returns:
        If ``link`` is allowed in ``robots.txt``.

    Note:
        The root path of a URL will always return :data:`True`.

    """
    # bypass robots for root path
    if link.url_parse.path in ['', '/']:
        return True

    robots = os.path.join(link.base, 'robots.txt')
    if os.path.isfile(robots):
        rp = RobotFileParser()
        with open(robots) as file:
            rp.parse(file)

        from darc.requests import default_user_agent  # pylint: disable=import-outside-toplevel
        return rp.can_fetch(default_user_agent(), link.url)
    return True


def _check_ng(temp_list: typing.List[Link]) -> typing.List[Link]:
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

    session_map: typing.Dict[str, typing.FuturesSession] = dict()
    result_list = list()
    for link in temp_list:
        if match_host(link.host):
            continue
        if match_proxy(link.proxy):
            continue

        # get session
        session = session_map.get(link.proxy)
        if session is None:
            session = request_session(link, futures=True)
            session_map[link.proxy] = session

        result = session.head(link.url, allow_redirects=True)
        result_list.append(result)

        print(f'[HEAD] Checking content type from {link.url}')

    link_list = list()
    for result in concurrent.futures.as_completed(result_list):  # type: ignore
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
        temp_link = parse_link(response.request.url)  # type: ignore
        link_list.append(temp_link)
    return link_list


def _check(temp_list: typing.List[Link]) -> typing.List[Link]:
    """Check hostname and proxy type of links.

    Args:
        temp_list: List of links to be checked.

    Returns:
        List of links matches the requirements.

    Note:
        If :data:`~darc.const.CHECK_NG` is :data:`True`,
        the function will directly call :func:`~darc.parse._check_ng`
        instead.

    See Also:
        * :func:`darc.parse.match_host`
        * :func:`darc.parse.match_proxy`

    """
    if CHECK_NG:
        return _check_ng(temp_list)

    link_list = list()
    for link in temp_list:
        if match_host(link.host):
            continue
        if match_proxy(link.proxy):
            continue
        link_list.append(link)
    return link_list


def get_content_type(response: typing.Response) -> str:
    """Get content type from ``response``.

    Args:
        response (:class:`requests.Response`): Response object.

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


def extract_links(link: Link, html: typing.Union[str, bytes], check: bool = CHECK) -> typing.List[Link]:
    """Extract links from HTML document.

    Args:
        link: Original link of the HTML document.
        html: Content of the HTML document.
        check: If perform checks on extracted links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of extracted links.

    See Also:
        * :func:`darc.parse._check`
        * :func:`darc.parse._check_ng`

    """
    soup = bs4.BeautifulSoup(html, 'html5lib')

    temp_list = list()
    for child in soup.find_all(lambda tag: tag.has_attr('href') or tag.has_attr('src')):
        if (href := child.get('href', child.get('src'))) is None:
            continue
        temp_link = parse_link(urljoin(link.url, href))
        temp_list.append(temp_link)

    # extract links from text
    temp_list.extend(extract_links_from_text(link, soup.text))

    # check content / proxy type
    if check:
        return _check(temp_list)
    return temp_list


def extract_links_from_text(link: Link, text: str) -> typing.List[Link]:
    """Extract links from raw text source.

    Args:
        link: Original link of the source document.
        text: Content of source text document.

    Returns:
        List of extracted links.

    Important:
        The extraction is **NOT** as reliable since we did not
        perform `TLD`_ checks on the extracted links and we cannot
        guarantee all links to be extracted.

        .. _TLD: https://pypi.org/project/tld/

        The URL patterns used to extract links are defined by
        :data:`darc.parse.URL_PAT` and you may register your
        own expressions by :envvar:`DARC_URL_PAT`.

    """
    temp_list = list()
    for part in text.split():
        for pattern in URL_PAT:
            for match in pattern.finditer(part):
                match_url = match.group('url')

                # add scheme if not exist
                if not urlsplit(match_url).scheme:
                    match_url = f'{link.url_parse.scheme}:{match_url}'

                temp_link = parse_link(match_url)
                temp_list.append(temp_link)
    return temp_list
