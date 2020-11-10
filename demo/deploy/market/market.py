# -*- coding: utf-8 -*-
#: pylint: disable=import-error,no-name-in-module
"""Market Hooks
===================

The market hooks as declared in :class:`MarketSite` are specially
designed for crawling market sites data, which requires authentications.
The hooks fetch cookies information from the `remote database`_
then inject them into the requests respectively to bypass such
authentication methods of the market sites.

.. _remote database: http://43.250.173.86:7899/cookie/index

"""

import abc
import json
import math
import time
import sys

import bs4
import requests
import stem.util.term

import darc.typing as typing
from darc._compat import datetime
from darc.const import CHECK, SE_EMPTY, SE_WAIT
from darc.db import _redis_command, save_requests, save_selenium
from darc.error import LinkNoReturn, render_error
from darc.link import Link, parse_link, urljoin
from darc.parse import _check, get_content_type
from darc.sites._abc import BaseSite
from darc.submit import submit_requests, submit_selenium

#: Optional[int]: Timeout for cached cookies information.
#: Set :data:`None` to disable caching, but it may impact
#: the performance of the :mod:`darc` workers.
CACHE_TIMEOUT = None  # type: typing.Optional[int]


class CacheRecord(typing.TypedDict):
    """Cache record."""

    #: Home page URL (``homeUrl``).
    homepage: str

    #: Flag if the market site alive (isAlive).
    alive: bool

    #: Market name (``marketName``).
    name: str

    #: Cookies information (``cookie``).
    cookies: typing.Dict[str, str]

    #: List of domains (``domain``).
    domains: typing.List[str]

    #: Exit node (``exitNode``).
    exit_node: str

    #: Flag if the information is valid (``isValid``).
    valid: bool

    #: Timestamp last update (``updateTime``).
    last_update: typing.Datetime

    #: Flag if the entry is deleted (``isDel``).
    deleted: bool

    #: List of history domains (``historyDomain``).
    history_domains: typing.List[str]


class MarketSite(BaseSite):
    """Market hooks.

    The sites customisation is the abstract base hook for market sites.
    It fetches cookies information from the `remote database`_, and utilises
    them for crawling and loading of the markets respectively.

    You will need to subclass the :class:`MarketSite` and implement
    :meth:`~MarketSite.process_crawler` and :meth:`~MarketSite.process_loader`
    to fully set up the worker.

    """

    @staticmethod
    @abc.abstractmethod
    def extract_links(link: Link, html: typing.Union[str, bytes]) -> typing.List[str]:
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

        link_list = list()
        for child in soup.find_all(lambda tag: tag.has_attr('href') or tag.has_attr('src')):
            if (href := child.get('href', child.get('src'))) is None:
                continue
            temp_link = urljoin(link.url, href)
            link_list.append(temp_link)
        return link_list

    @classmethod
    def _extract_links(cls, link: Link, html: typing.Union[str, bytes],
                                check: bool = CHECK) -> typing.List[Link]:
        """Extract links from HTML document.

        Args:
            link: Original link of the HTML document.
            html: Content of the HTML document.
            check: If perform checks on extracted links,
                default to :data:`~darc.const.CHECK`.

        Returns:
            List of extracted links.

        """
        temp_list = cls.extract_links(link, html)
        link_list = [parse_link(link) for link in temp_list]

        # check content / proxy type
        if check:
            return _check(link_list)
        return link_list

    @staticmethod
    def cache_cookies(host: str) -> typing.Optional[CacheRecord]:
        """Cache cookies information.

        The method sends a ``POST`` request to the `remote database`_ to
        obtain the latest cookies information, then parses and caches them
        in the Redis database.

        Notes:
            If :data:`CACHE_TIMEOUT` is set to :data:`None`, the caching
            will then be disabled.

        The parsed cookies information represents the actual target homepage
        of the market and the cookies needed for accessing it successfully.

        Args:
            host: Hostname of the target market.

        Returns:
            Cached cookies information if any.

        """
        cached = None

        response = requests.post('http://43.250.173.86:7899/cookie/all')
        data = response.json()['result']['cookies']
        for record in data:
            domain_list = list(filter(None, record['domain'].split(',')))  # type: typing.List[str]
            cached_data = {
                'homepage': record['homeUrl'],
                'alive': record['isAlive'],
                'name': record['marketName'],
                'cookies': json.loads(record['cookie']),
                'domains': domain_list,
                'exit_node': record['exitNode'],
                'valid': record['isValid'],
                'last_update': datetime.strptime(record['updateTime'], r'%Y-%m-%d %H:%M:%S.%f'),
                'deleted': record['isDel'],
                'history_domains': list(filter(None, record['historyDomain'].split(','))),
            }  # type: CacheRecord

            if CACHE_TIMEOUT is None:
                if any(domain == host for domain in domain_list):
                    cached = cached_data.copy()
                    break
            else:
                for domain in domain_list:
                    if domain == host:
                        cached = cached_data.copy()
                    _redis_command('setex', f'cookies:{domain}', CACHE_TIMEOUT, cached_data)
        return cached

    @classmethod
    def get_cookies(cls, host: str) -> typing.Optional[CacheRecord]:
        """Get cookies information.

        The method fetches cached cookies information from the Redis database.
        If caches expired, it calls :meth:`~MarketSite.cache_cookies` to update
        the cached information.

        Args:
            host: Hostname of the target market.

        Returns:
            Cached cookies information if any.

        """
        cached: typing.Optional[CacheRecord] = _redis_command('get', f'cookies:{host}')
        if cached is None:
            cached = cls.cache_cookies(host)
        return cached

    @classmethod
    def crawler(cls, timestamp: typing.Datetime, session: typing.Session, link: Link) -> typing.Response:
        """Default crawler hook.

        The hook fetches cookies information first. If no cookies found, the hook
        will consider such link as not applicable and will then be removed from
        the task queue.

        With the cached records, the hook will set the cookies in the session
        then goes to the actual targeting homepage. Then it shall calls
        :meth:`~MarketSite.process_crawler` with the :class:`~requests.Response`
        object to perform further processing.

        Afterwards, it pushes the homepage URL into the task queues and raises
        :exc:`LinkNoReturn` to drop the further processing.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (requests.Session): Session object with proxy settings.
            link: Link object to be crawled.

        Raises:
            LinkNoReturn: This link has no return response.

        See Also:
            * :func:`darc.crawl.crawler`

        """
        cached = cls.get_cookies(link.host)
        if cached is None:
            raise LinkNoReturn(link=link)

        cookies = cached['cookies']
        for name, value in cookies.items():
            session.cookies.set(name, value)

        cls.process_crawler(timestamp, session, link, cached)
        raise LinkNoReturn(link=link, drop=False)

    @classmethod
    def process_crawler(cls, timestamp: typing.Datetime, session: typing.Session, link: Link, record: CacheRecord) -> None:  # pylint: disable=unused-argument,line-too-long
        """Process the :class:`~requests.Response` object.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (requests.Session): Session object with proxy settings
                and cookies storage.
            link: Link object to be loaded.
            record: Cached record from the remote database.

        """
        response = session.get(link.url)

        ct_type = get_content_type(response)
        html = response.content

        # submit data
        submit_requests(timestamp, link, response, session, html, mime_type=ct_type, html=True)

        # add link to queue
        extracted_links = cls._extract_links(link, response.content)
        save_requests(extracted_links, score=0, nx=True)

        # add link to queue
        save_selenium(link, single=True, score=0, nx=True)

    @classmethod
    def loader(cls, timestamp: typing.Datetime, driver: typing.Driver, link: Link) -> typing.NoReturn:
        """Market loader hook.

        The hook fetches cookies information first. If no cookies found, the hook
        will consider such link as not applicable and will then be removed from
        the task queue.

        With the cached records, the hook will set the cookies in the session
        then goes to the actual targeting homepage. Then it shall calls
        :meth:`~MarketSite.process_loader` with the
        :class:`WebDriver <selenium.webdriver.Chrome>` object to perform further
        processing.

        Afterwards, it pushes the homepage URL into the task queues and raises
        :exc:`LinkNoReturn` to drop the further processing.

        Args:
            timestamp: Timestamp of the worker node reference.
            driver (selenium.webdriver.Chrome): Web driver object with proxy settings.
            link: Link object to be loaded.

        Raises:
            LinkNoReturn: This link has no return response.

        """
        cached = cls.get_cookies(link.host)
        if cached is None:
            raise LinkNoReturn(link=link)

        cookies = cached['cookies']
        for name, value in cookies.items():
            driver.add_cookie({
                'name': name,
                'value': value,
            })

        cls.process_loader(timestamp, driver, link, cached)
        raise LinkNoReturn(link=link, drop=False)

    @classmethod
    def process_loader(cls, timestamp: typing.Datetime, driver: typing.Driver, link: Link, record: CacheRecord) -> None:  # pylint: disable=unused-argument
        """Process the :class:`WebDriver <selenium.webdriver.Chrome>` object.

        Args:
            timestamp: Timestamp of the worker node reference.
            driver (selenium.webdriver.Chrome): Web driver object with proxy settings
                and cookies presets.
            link: Link object to be loaded.
            record: Cached record from the remote database.

        """
        driver.get(link.url)

        # wait for page to finish loading
        if SE_WAIT is not None:
            time.sleep(SE_WAIT)

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
        extracted_links = cls._extract_links(link, html)
        save_requests(extracted_links, score=0, nx=True)
