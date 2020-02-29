# -*- coding: utf-8 -*-
"""Source parser."""

import contextlib
import io
import re
import urllib.parse
import urllib.robotparser

import bs4
import stem.util.term

import darc.typing as typing
from darc.const import DEBUG, LINK_BLACK_LIST, LINK_WHITE_LIST, MIME_BLACK_LIST, MIME_WHITE_LIST
from darc.link import Link, parse_link


def match_link(link: str) -> bool:
    """Check if link in black list."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.netloc or parse.hostname

    if DEBUG:
        print(stem.util.term.format(f'Matching {host!r} from {link}',
                                    stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

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

        # check content type
        ct_type = check_header(link)
        if match_mime(ct_type):
            continue
        link_list.append(temp_link)
    yield from set(link_list)


def check_header(link: str) -> str:
    """Request the link using HEAD command."""
    from darc.crawl import request_session  # pylint: disable=import-outside-toplevel

    link_obj = parse_link(link)
    with contextlib.suppress():
        with request_session(link_obj) as session:
            response = session.head(link)

            # fetch content type
            return response.headers.get('Content-Type', 'text/html').casefold()
    return 'null'


def extract_links(link: str, html: typing.Union[str, bytes]) -> typing.Iterator[str]:
    """Extract links from HTML context."""
    soup = bs4.BeautifulSoup(html, 'html5lib')

    link_list = []
    for child in soup.find_all(lambda tag: tag.has_attr('href') or tag.has_attr('src')):
        if (href := child.get('href', child.get('src'))) is None:
            continue
        temp_link = urllib.parse.urljoin(link, href)
        if match_link(temp_link):
            continue

        # # check content type
        # ct_type = check_header(link)
        # if match_mime(ct_type):
        #     continue
        link_list.append(temp_link)
    yield from set(link_list)
