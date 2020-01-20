# -*- coding: utf-8 -*-
"""Source parser."""

import re
import urllib.parse
import urllib.robotparser

import bs4

import darc.typing as typing
from darc.const import LINK_BL, LINK_EX
from darc.link import Link, parse_link


def _match(link: str) -> bool:
    """Check if link in black list."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    if re.match(LINK_EX, host) is None:
        return True

    for pattern in LINK_BL:
        if re.match(pattern, host) is not None:
            return True
    return False


def get_sitemap(link: str, text: str) -> typing.List[Link]:
    """Fetch link to sitemap."""
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())

    sitemaps = rp.site_maps()
    if sitemaps is None:
        return [parse_link(urllib.parse.urljoin(link, '/sitemap.xml'))]
    return [parse_link(urllib.parse.urljoin(link, sitemap)) for sitemap in sitemaps]


def read_sitemap(link: str, text: str) -> typing.Iterator[str]:
    """Read sitemap."""
    link_list = list()
    soup = bs4.BeautifulSoup(text, 'html5lib')
    for loc in soup.find_all('loc'):
        temp_link = urllib.parse.urljoin(link, loc.text)
        if _match(temp_link):
            continue
        link_list.append(temp_link)
    yield from set(link_list)


def extract_links(link: str, html: typing.Union[str, bytes]) -> typing.Iterator[str]:
    """Extract links from HTML context."""
    soup = bs4.BeautifulSoup(html, 'html5lib')

    link_list = []
    for child in filter(lambda element: isinstance(element, bs4.element.Tag),
                        soup.descendants):
        if (href := child.get('href', child.get('src'))) is None:
            continue
        temp_link = urllib.parse.urljoin(link, href)
        if _match(temp_link):
            continue
        link_list.append(temp_link)
    yield from set(link_list)
