# -*- coding: utf-8 -*-
"""Source parser."""

import concurrent.futures
import io
import os
import re
import urllib.robotparser

import bs4
import magic
import requests
import stem.util.term

import darc.typing as typing
from darc.const import (CHECK, CHECK_NG, LINK_BLACK_LIST, LINK_WHITE_LIST, MIME_BLACK_LIST, MIME_WHITE_LIST,
                        PROXY_BLACK_LIST, PROXY_WHITE_LIST)
from darc.error import render_error
from darc.link import Link, parse_link, urljoin


def match_proxy(proxy: str) -> bool:
    """Check if proxy in black list."""
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
    """Check if hostname in black list."""
    # invalid hostname
    if host is None:
        return True

    # any matching white list
    if any(re.fullmatch(pattern, host, re.IGNORECASE) is not None for pattern in LINK_WHITE_LIST):
        return False

    # any matching black list
    if any(re.fullmatch(pattern, host, re.IGNORECASE) is not None for pattern in LINK_BLACK_LIST):
        return True

    # fallback
    return False


def match_mime(mime: str) -> bool:
    """Check if content type in black list."""
    # any matching white list
    if any(re.fullmatch(pattern, mime, re.IGNORECASE) is not None for pattern in MIME_WHITE_LIST):
        return False

    # any matching black list
    if any(re.fullmatch(pattern, mime, re.IGNORECASE) is not None for pattern in MIME_BLACK_LIST):
        return True

    # fallback
    return False


def read_robots(link: str, text: str, host: typing.Optional[str] = None) -> typing.List[Link]:
    """Read robots."""
    rp = urllib.robotparser.RobotFileParser()
    with io.StringIO(text) as file:
        rp.parse(file)

    sitemaps = rp.site_maps()
    if sitemaps is None:
        return [parse_link(urljoin(link, '/sitemap.xml'))]
    return [parse_link(urljoin(link, sitemap), host=host) for sitemap in sitemaps]


def check_robots(link: Link) -> bool:
    """Check if link is allowed in ``robots.txt``."""
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


def get_sitemap(link: str, text: str, host: typing.Optional[str] = None) -> typing.Iterator[str]:
    """Fetch link to sitemap."""
    sitemaps = list()
    soup = bs4.BeautifulSoup(text, 'html5lib')

    # https://www.sitemaps.org/protocol.html#index
    for loc in soup.select('sitemapindex > sitemap > loc'):
        sitemaps.append(urljoin(link, loc.text))
    return [parse_link(sitemap, host=host) for sitemap in sitemaps]


def _check_ng(temp_list: typing.List[str]) -> typing.List[str]:
    """Check content and proxy type of links."""
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
    """Check hostname and proxy type of links."""
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
    """Read sitemap."""
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
    """Get content type of response."""
    ct_type = response.headers.get('Content-Type')
    if ct_type is None:
        try:
            ct_type = magic.detect_from_content(response.content).mime_type
        except Exception:
            ct_type = '(null)'
    return ct_type.casefold().split(';', maxsplit=1)[0].strip()


def extract_links(link: str, html: typing.Union[str, bytes], check: bool = CHECK) -> typing.Iterator[str]:
    """Extract links from HTML context."""
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
