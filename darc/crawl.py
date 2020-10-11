# -*- coding: utf-8 -*-
"""Web Crawlers
==================

The :mod:`darc.crawl` module provides two types of crawlers.

* :func:`~darc.crawl.crawler` -- crawler powered by :mod:`requests`
* :func:`~darc.crawl.loader` -- crawler powered by :mod:`selenium`

"""

import contextlib
import math
import os
import shutil
import sys
import traceback

import requests
import selenium.common.exceptions
import selenium.webdriver
import selenium.webdriver.common.proxy
import stem
import stem.control
import stem.process
import stem.util.term
import urllib3

import darc.typing as typing
from darc._compat import datetime
from darc.const import FORCE, SE_EMPTY
from darc.db import (drop_hostname, drop_requests, drop_selenium, have_hostname, save_requests,
                     save_selenium)
from darc.error import LinkNoReturn, render_error
from darc.link import Link
from darc.parse import (check_robots, extract_links, get_content_type, match_host, match_mime,
                        match_proxy)
from darc.proxy.i2p import fetch_hosts, read_hosts
from darc.proxy.null import fetch_sitemap, save_invalid
from darc.requests import request_session
from darc.save import save_headers
from darc.selenium import request_driver
from darc.sites import crawler_hook, loader_hook
from darc.submit import SAVE_DB, submit_new_host, submit_requests, submit_selenium
from darc.model import HostnameModel, URLModel


def crawler(link: Link) -> None:
    """Single :mod:`requests` crawler for a entry link.

    Args:
        link: URL to be crawled by :mod:`requests`.

    The function will first parse the URL using
    :func:`~darc.link.parse_link`, and check if need to crawl the
    URL (c.f. :data:`~darc.const.PROXY_WHITE_LIST`, :data:`~darc.const.PROXY_BLACK_LIST`,
    :data:`~darc.const.LINK_WHITE_LIST` and :data:`~darc.const.LINK_BLACK_LIST`);
    if true, then crawl the URL with :mod:`requests`.

    If the URL is from a brand new host, :mod:`darc` will first try
    to fetch and save ``robots.txt`` and sitemaps of the host
    (c.f. :func:`~darc.proxy.null.save_robots` and :func:`~darc.proxy.null.save_sitemap`),
    and extract then save the links from sitemaps (c.f. :func:`~darc.proxy.null.read_sitemap`)
    into link database for future crawling (c.f. :func:`~darc.db.save_requests`).

    .. note::

       A host is new if :func:`~darc.db.have_hostname` returns :data:`True`.

       If :func:`darc.proxy.null.fetch_sitemap` and/or :func:`darc.proxy.i2p.fetch_hosts`
       failed when fetching such documents, the host will be removed from the
       hostname database through :func:`~darc.db.drop_hostname`, and considered
       as new when next encounter.

    Also, if the submission API is provided, :func:`~darc.submit.submit_new_host`
    will be called and submit the documents just fetched.

    If ``robots.txt`` presented, and :data:`~darc.const.FORCE` is
    :data:`False`, :mod:`darc` will check if allowed to crawl the URL.

    .. note::

        The root path (e.g. ``/`` in https://www.example.com/) will always
        be crawled ignoring ``robots.txt``.

    At this point, :mod:`darc` will call the customised hook function
    from :mod:`darc.sites` to crawl and get the final response object.
    :mod:`darc` will save the session cookies and header information,
    using :func:`~darc.save.save_headers`.

    .. note::

        If :exc:`requests.exceptions.InvalidSchema` is raised, the link
        will be saved by :func:`~darc.proxy.null.save_invalid`. Further
        processing is dropped, and the link will be removed from the
        :mod:`requests` database through :func:`~darc.db.drop_requests`.

        If :exc:`~darc.error.LinkNoReturn` is raised, the link will be
        removed from the :mod:`requests` database through
        :func:`~darc.db.drop_requests`.

    If the content type of response document is not ignored (c.f.
    :data:`~darc.const.MIME_WHITE_LIST` and :data:`~darc.const.MIME_BLACK_LIST`),
    :func:`~darc.submit.submit_requests` will be called and submit the document
    just fetched.

    If the response document is HTML (``text/html`` and ``application/xhtml+xml``),
    :func:`~darc.parse.extract_links` will be called then to extract
    all possible links from the HTML document and save such links into
    the database (c.f. :func:`~darc.db.save_requests`).

    And if the response status code is between ``400`` and ``600``,
    the URL will be saved back to the link database
    (c.f. :func:`~darc.db.save_requests`). If **NOT**, the URL will
    be saved into :mod:`selenium` link database to proceed next steps
    (c.f. :func:`~darc.db.save_selenium`).

    """
    print(f'[REQUESTS] Requesting {link.url}')
    try:
        if match_proxy(link.proxy):
            print(render_error(f'[REQUESTS] Ignored proxy type from {link.url} ({link.proxy})',
                               stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
            drop_requests(link)
            return

        if match_host(link.host):
            print(render_error(f'[REQUESTS] Ignored hostname from {link.url} ({link.proxy})',
                               stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
            drop_requests(link)
            return

        # timestamp
        timestamp = datetime.now()

        # get the session object in advance
        session = request_session(link)

        # check whether schema supported by :mod:`requests`
        try:
            session.get_adapter(link.url)  # test for adapter
            requests_supported = True
        except requests.exceptions.InvalidSchema:
            requests_supported = False

        # if need to test for new host
        if requests_supported:
            # if it's a new host
            flag_have, force_fetch = have_hostname(link)
            if not flag_have or force_fetch:
                partial = False

                if link.proxy not in ('zeronet', 'freenet'):
                    # fetch sitemap.xml
                    try:
                        fetch_sitemap(link, force=force_fetch)
                    except Exception:
                        error = f'[Error fetching sitemap of {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
                        partial = True

                if link.proxy == 'i2p':
                    # fetch hosts.txt
                    try:
                        fetch_hosts(link, force=force_fetch)
                    except Exception:
                        error = f'[Error subscribing hosts from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
                        partial = True

                # submit data / drop hostname from db
                if partial:
                    drop_hostname(link)
                submit_new_host(timestamp, link, partial=partial, force=force_fetch)

            if not FORCE and not check_robots(link):
                print(render_error(f'[REQUESTS] Robots disallowed link from {link.url}',
                                stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
                return

        # reuse the session object
        with session:
            try:
                # requests session hook
                response = crawler_hook(link, session)
            except requests.exceptions.InvalidSchema as error:
                print(render_error(f'[REQUESTS] Failed on {link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                save_invalid(link)
                drop_requests(link)
                return
            except requests.RequestException as error:
                print(render_error(f'[REQUESTS] Failed on {link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                save_requests(link, single=True)
                return
            except LinkNoReturn:
                print(render_error(f'[REQUESTS] Removing from database: {link.url}',
                                   stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
                drop_requests(link)
                return

            # save headers
            save_headers(timestamp, link, response, session)

            # check content type
            ct_type = get_content_type(response)
            if ct_type not in ['text/html', 'application/xhtml+xml']:
                print(render_error(f'[REQUESTS] Generic content type from {link.url} ({ct_type})',
                                   stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member

                # probably hosts.txt
                if link.proxy == 'i2p' and ct_type in ['text/plain', 'text/text']:
                    text = response.text
                    save_requests(read_hosts(text))

                if match_mime(ct_type):
                    drop_requests(link)
                    return

                # submit data
                data = response.content
                submit_requests(timestamp, link, response, session, data, mime_type=ct_type, html=False)

                return

            html = response.content
            if not html:
                print(render_error(f'[REQUESTS] Empty response from {link.url}',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                save_requests(link, single=True)
                return

            # submit data
            submit_requests(timestamp, link, response, session, html, mime_type=ct_type, html=True)

            # add link to queue
            save_requests(extract_links(link, html), score=0, nx=True)

            if not response.ok:
                print(render_error(f'[REQUESTS] Failed on {link.url} [{response.status_code}]',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                save_requests(link, single=True)
                return

            # add link to queue
            save_selenium(link, single=True, score=0, nx=True)
    except Exception:
        if SAVE_DB:
            with contextlib.suppress(Exception):
                host: typing.Optional[HostnameModel] = HostnameModel.get_or_none(HostnameModel.hostname == link.host)
                if host is not None:
                    host.alive = False
                    host.save()

            with contextlib.suppress(Exception):
                url: typing.Optional[URLModel] = URLModel.get_or_none(URLModel.hash == link.name)
                if url is not None:
                    url.alias = False
                    url.save()

        error = f'[Error from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # type: ignore # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # type: ignore # pylint: disable=no-member
        save_requests(link, single=True)
    print(f'[REQUESTS] Requested {link.url}')


def loader(link: Link) -> None:
    """Single :mod:`selenium` loader for a entry link.

    Args:
        Link: URL to be crawled by :mod:`selenium`.

    The function will first parse the URL using :func:`~darc.link.parse_link`
    and start loading the URL using :mod:`selenium` with Google Chrome.

    At this point, :mod:`darc` will call the customised hook function
    from :mod:`darc.sites` to load and return the original
    :class:`selenium.webdriver.Chrome` object.

    .. note::

        If :exc:`~darc.error.LinkNoReturn` is raised, the link will be
        removed from the :mod:`selenium` database through
        :func:`~darc.db.drop_selenium`.

    If successful, the rendered source HTML document will be saved, and a
    full-page screenshot will be taken and saved.

    .. note::

       When taking full-page screenshot, :func:`~darc.crawl.loader` will
       use :javascript:`document.body.scrollHeight` to get the total
       height of web page. If the page height is *less than* **1,000 pixels**,
       then :mod:`darc` will by default set the height as **1,000 pixels**.

       Later :mod:`darc` will tell :mod:`selenium` to resize the window (in
       *headless* mode) to **1,024 pixels** in width and **110%** of the
       page height in height, and take a *PNG* screenshot.

    If the submission API is provided, :func:`~darc.submit.submit_selenium`
    will be called and submit the document just loaded.

    Later, :func:`~darc.parse.extract_links` will be called then to
    extract all possible links from the HTML document and save such
    links into the :mod:`requests` database (c.f. :func:`~darc.db.save_requests`).

    .. seealso::

       * :data:`darc.const.SE_EMPTY`
       * :data:`darc.const.SE_WAIT`

    """
    print(f'[SELENIUM] Loading {link.url}')
    try:
        # timestamp
        timestamp = datetime.now()

        # retrieve source from Chrome
        with request_driver(link) as driver:
            try:
                # selenium driver hook
                driver = loader_hook(link, driver)
            except urllib3.exceptions.HTTPError as error:
                print(render_error(f'[SELENIUM] Fail to load {link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                save_selenium(link, single=True)
                return
            except selenium.common.exceptions.WebDriverException as error:
                print(render_error(f'[SELENIUM] Fail to load {link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                save_selenium(link, single=True)
                return
            except LinkNoReturn:
                print(render_error(f'[SELENIUM] Removing from database: {link.url}',
                                   stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
                drop_selenium(link)
                return

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
            save_requests(extract_links(link, html), score=0, nx=True)
    except Exception:
        error = f'[Error from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # type: ignore # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # type: ignore # pylint: disable=no-member
        save_selenium(link, single=True)
    print(f'[SELENIUM] Loaded {link.url}')
