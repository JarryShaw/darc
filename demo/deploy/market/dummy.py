# -*- coding: utf-8 -*-
#: pylint: disable=import-error
"""Hooks for a dummy site (example)."""

from typing import TYPE_CHECKING

import bs4
from market import MarketSite

from darc.link import urljoin

if TYPE_CHECKING:
    from typing import List, Union

    from darc.link import Link


class DummySite(MarketSite):
    """Dummy site (example)."""

    #: Hostnames (**case insensitive**) the sites customisation is designed for.
    hostname = [
        'dummy.onion',
        'dummy.com',
        'dummy.io',
    ]

    @staticmethod
    def extract_links(link: 'Link', html: 'Union[str, bytes]') -> 'List[str]':
        """Extract links from HTML document.

        Args:
            link: Original link of the HTML document.
            html: Content of the HTML document.
            check: If perform checks on extracted links,
                default to :data:`~darc.const.CHECK`.

        Returns:
            List of extracted links.

        See Also:
            * :func:`darc.parse.extract_links`

        """
        soup = bs4.BeautifulSoup(html, 'html5lib')

        link_list = []
        for child in soup.find_all(lambda tag: tag.has_attr('href') or tag.has_attr('src')):
            if (href := child.get('href', child.get('src'))) is None:
                continue
            temp_link = urljoin(link.url, href)
            link_list.append(temp_link)
        return link_list
