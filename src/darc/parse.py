# -*- coding: utf-8 -*-

import urllib.parse as urlparse

import bs4

import darc.typings as typing

def extract_links(html: str) -> typing.Iterator[str]:
    """Extract links from HTML context."""
    soup = bs4.BeautifulSoup(html, 'html5lib')

    link = []
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href')
        if href is None:
            continue
        link.append(href)
    yield from set(link)


def parse_links(link: str, html: str) -> typing.List[str]:
    """Parse links from HTML context."""
    link_list = []
    for href in extract_links(html):
        link_list.append(urlparse.urljoin(link, href))
    return list(set(link_list))
