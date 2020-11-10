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
import datetime
import json

import requests

import darc.typing as typing
from darc.db import _redis_command
from darc.error import LinkNoReturn
from darc.link import Link
from darc.sites import SITEMAP
from darc.sites._abc import BaseSite

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
                'cookies': json.loads(record['cookie']),
                'domain': domain_list,
                'exit_node': record['exitNode'],
                'valid': record['isValid'],
                'last_update': datetime.datetime.strptime(record['updateTime'], r'%Y-%m-%d %H:%M:%S.%f'),
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
    def crawler(cls, session: typing.Session, link: Link) -> typing.Response:
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

        cls.process_crawler(session, link, cached)
        raise LinkNoReturn(link=link, drop=False)

    @staticmethod
    @abc.abstractmethod
    def process_crawler(session: typing.Session, link: Link, record: CacheRecord) -> None:
        """Process the :class:`~requests.Response` object.

        Args:
            session (requests.Session): Session object with proxy settings
                and cookies storage.
            link: Link object to be loaded.
            record: Cached record from the remote database.

        """

    @classmethod
    def loader(cls, driver: typing.Driver, link: Link) -> typing.NoReturn:
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

        cls.process_loader(driver, link, cached)
        raise LinkNoReturn(link=link, drop=False)

    @staticmethod
    @abc.abstractmethod
    def process_loader(driver: typing.Driver, link: Link, record: CacheRecord) -> None:
        """Process the :class:`WebDriver <selenium.webdriver.Chrome>` object.

        Args:
            driver:  Web driver object with proxy settings
                and cookies presets.
            link: Link object to be loaded.
            record: Cached record from the remote database.

        """
