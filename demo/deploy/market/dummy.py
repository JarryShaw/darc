# -*- coding: utf-8 -*-
#: pylint: disable=import-error,no-name-in-module
"""Hooks for a dummy site (example)."""

import math
import sys

import bs4
import stem.util.term

import darc.typing as typing
from darc._compat import datetime
from darc.const import CHECK, SE_EMPTY
from darc.db import save_requests, save_selenium
from darc.error import render_error
from darc.link import Link, parse_link, urljoin
from darc.parse import _check, get_content_type
from darc.submit import submit_requests, submit_selenium

from market import CacheRecord, MarketSite  # pylint: disable=wrong-import-order


class DummySite(MarketSite):
    """Dummy site (example)."""

    #: Hostnames (**case insensitive**) the sites customisation is designed for.
    hostname = [
        'dummy.onion',
        'dummy.com',
        'dummy.io',
    ]

    @staticmethod
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
            * :func:`darc.parse.extract_links`

        """
        soup = bs4.BeautifulSoup(html, 'html5lib')

        temp_list = list()
        for child in soup.find_all(lambda tag: tag.has_attr('href') or tag.has_attr('src')):
            if (href := child.get('href', child.get('src'))) is None:
                continue
            temp_link = parse_link(urljoin(link.url, href))
            temp_list.append(temp_link)

        # check content / proxy type
        if check:
            return _check(temp_list)
        return temp_list

    @classmethod
    def process_crawler(cls, session: typing.Session, link: Link, record: CacheRecord) -> None:  # pylint: disable=unused-argument
        """Process the :class:`~requests.Response` object.

        Args:
            session (requests.Session): Session object with proxy settings
                and cookies storage.
            link: Link object to be loaded.
            record: Cached record from the remote database.

        """
        timestamp = datetime.now()
        response = session.get(link.url)

        ct_type = get_content_type(response)
        html = response.content

        # submit data
        submit_requests(timestamp, link, response, session, html, mime_type=ct_type, html=True)

        # add link to queue
        extracted_links = cls.extract_links(link, response.content)
        save_requests(extracted_links, score=0, nx=True)

        # add link to queue
        save_selenium(link, single=True, score=0, nx=True)

    @classmethod
    def process_loader(cls, driver: typing.Driver, link: Link, record: CacheRecord) -> None:  # pylint: disable=unused-argument
        """Process the :class:`WebDriver <selenium.webdriver.Chrome>` object.

        Args:
            driver:  Web driver object with proxy settings
                and cookies presets.
            link: Link object to be loaded.
            record: Cached record from the remote database.

        """
        timestamp = datetime.now()
        driver.get(link.url)

        # get HTML source
        html = driver.page_source
        if html == SE_EMPTY:
            print(render_error(f'[SELENIUM] Empty page from {link.url}',
                               stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
            save_selenium(link, single=True)
            return

        screenshot = None
        try:
            # get maximum height
            height = driver.execute_script('return document.body.scrollHeight')

            # resize window (with some magic numbers)
            if height < 1000:
                height = 1000
            driver.set_window_size(1024, math.ceil(height * 1.1))

            # take a full page screenshot
            screenshot = driver.get_screenshot_as_base64()
        except Exception as error:
            print(render_error(f'[SELENIUM] Fail to save screenshot from {link.url} <{error}>',
                               stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member

        # submit data
        submit_selenium(timestamp, link, html, screenshot)

        # add link to queue
        extracted_links = cls.extract_links(link, html)
        save_requests(extracted_links, score=0, nx=True)
