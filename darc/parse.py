# -*- coding: utf-8 -*-
"""Source parser."""

import concurrent.futures
import io
import os
import re
import urllib.parse
import urllib.robotparser

import bs4
import requests

import darc.typing as typing
from darc.const import (DEBUG, LINK_BLACK_LIST, LINK_WHITE_LIST, MIME_BLACK_LIST, MIME_WHITE_LIST,
                        PROXY_BLACK_LIST, PROXY_WHITE_LIST)
from darc.link import Link, parse_link


def match_proxy(proxy: str) -> bool:
    """Check if proxy in black list."""
    # any matching white list
    if proxy in PROXY_WHITE_LIST:
        return False

    # any matching black list
    if proxy in PROXY_BLACK_LIST:
        return True

    # fallback
    return False


def match_link(link: str) -> bool:
    """Check if link in black list."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.netloc or parse.hostname

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
        return [parse_link(urllib.parse.urljoin(link, '/sitemap.xml'))]
    return [parse_link(urllib.parse.urljoin(link, sitemap), host=host) for sitemap in sitemaps]


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
        sitemaps.append(urllib.parse.urljoin(link, loc.text))
    return [parse_link(sitemap, host=host) for sitemap in sitemaps]


def read_sitemap(link: str, text: str) -> typing.Iterator[str]:
    """Read sitemap."""
    link_list = list()
    soup = bs4.BeautifulSoup(text, 'html5lib')

    # https://www.sitemaps.org/protocol.html
    for loc in soup.select('urlset > url > loc'):
        temp_link = urllib.parse.urljoin(link, loc.text)
        if match_link(temp_link):
            continue
        link_list.append(temp_link)
    yield from set(link_list)


def get_content_type(response: typing.Response) -> str:
    """Get content type of response."""
    return response.headers.get('Content-Type', 'text/html').casefold().split(';', maxsplit=1)[0].strip()


def extract_links(link: str, html: typing.Union[str, bytes], check: bool = False) -> typing.Iterator[str]:
    """Extract links from HTML context."""
    soup = bs4.BeautifulSoup(html, 'html5lib')

    temp_list = list()
    for child in soup.find_all(lambda tag: tag.has_attr('href') or tag.has_attr('src')):
        if (href := child.get('href', child.get('src'))) is None:
            continue
        temp_link = urllib.parse.urljoin(link, href)
        if match_link(temp_link):
            continue
        temp_list.append(temp_link)

    # check content type
    if check:
        from darc.crawl import request_session  # pylint: disable=import-outside-toplevel

        session_map = dict()
        result_list = list()
        for item in temp_list:
            link_obj = parse_link(item)

            # get session
            session = session_map.get(link_obj.proxy)
            if session is None:
                session = request_session(link_obj, futures=True)
                session_map[link_obj.proxy] = session

            result = session.head(item)
            result_list.append(result)

            if DEBUG:
                print(f'[HEAD] Checking content type from {item}')

        link_list = list()
        for result in concurrent.futures.as_completed(result_list):
            try:
                response: typing.Response = result.result()
            except requests.RequestException:
                continue

            ct_type = get_content_type(response)
            if DEBUG:
                print(f'[HEAD] Checked content type from {response.url} ({ct_type})')
            if match_mime(ct_type):
                continue
            link_list.append(response.url)
    else:
        link_list = temp_list.copy()
    yield from set(link_list)
