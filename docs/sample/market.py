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

Important:
    :class:`MarketSite` is registered as the default sites
    customisation for such scenario. And all other default
    sites customisations will then be removed.

You may simply use this file as the new entrypoint for your
:mod:`darc` worker.

"""

import abc
import json
import sys
import time

import requests

import darc.typing as typing
from darc.__main__ import main
from darc.const import SE_WAIT
from darc.db import _redis_command, save_requests, save_selenium
from darc.error import LinkNoReturn
from darc.link import Link, parse_link
from darc.sites import SITEMAP
from darc.sites.default import DefaultSite

#: Optional[int]: Timeout for cached cookies information.
#: Set :data:`None` to disable caching, but it may impact
#: the performance of the :mod:`darc` workers.
CACHE_TIMEOUT = None  # type: typing.Optional[int]


class CacheRecord(typing.TypedDict):
    """Cache record."""

    #: Home page URL.
    homepage: str

    #: Cookies information.
    cookies: typing.Dict[str, str]


class MarketSite(DefaultSite):
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
            domain_list = record['domain'].split(',')
            cached_data = {
                'homepage': record['homeUrl'],
                'cookies': json.loads(record['cookie']),
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

        homepage = cached['homepage']
        cookies = cached['cookies']

        for name, value in cookies.items():
            session.cookies.set(name, value)

        response = session.get(homepage, allow_redirects=True)
        cls.process_crawler(response)

        home = parse_link(homepage)
        save_requests(home, single=True)
        save_selenium(home, single=True)

        raise LinkNoReturn(link=link, drop=False)

    @staticmethod
    @abc.abstractmethod
    def process_crawler(response: typing.Response) -> None:
        """Process the :class:`~requests.Response` object.

        Args:
            response: The final response object with crawled data.

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

        homepage = cached['homepage']
        cookies = cached['cookies']

        for name, value in cookies.items():
            driver.add_cookie({
                'name': name,
                'value': value,
            })

        driver.get(homepage)
        cls.process_loader(driver)

        # wait for page to finish loading
        if SE_WAIT is not None:
            time.sleep(SE_WAIT)

        home = parse_link(homepage)
        save_requests(home, single=True)
        save_selenium(home, single=True)

        raise LinkNoReturn(link=link, drop=False)

    @staticmethod
    @abc.abstractmethod
    def process_loader(driver: typing.Driver) -> None:
        """Process the :class:`WebDriver <selenium.webdriver.Chrome>` object.

        Args:
            driver: The web driver object with loaded data.

        """


# registers ``MarketSite`` as the default hook
SITEMAP.default_factory = lambda: MarketSite
SITEMAP.clear()

if __name__ == "__main__":
    sys.exit(main())
