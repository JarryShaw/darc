# -*- coding: utf-8 -*-
"""Web Crawlers
==================

The :mod:`darc.crawl` module provides two types of crawlers.

* :func:`~darc.crawl.crawler` -- crawler powered by |requests|_
* :func:`~darc.crawl.loader` -- crawler powered by |selenium|_

"""

import contextlib
import math
import os
import shutil
import sys
import traceback

import magic
import requests
import selenium.common.exceptions
import selenium.webdriver
import selenium.webdriver.common.proxy
import stem
import stem.control
import stem.process
import stem.util.term
import urllib3

from darc._compat import datetime
from darc.const import FORCE, SAVE_REQUESTS, SAVE_SELENIUM, SE_EMPTY
from darc.db import save_requests, save_selenium
from darc.error import render_error
from darc.link import parse_link
from darc.parse import (check_robots, extract_links, get_content_type, match_host, match_mime,
                        match_proxy)
from darc.proxy.bitcoin import save_bitcoin
from darc.proxy.data import save_data
from darc.proxy.ed2k import save_ed2k
from darc.proxy.i2p import fetch_hosts, read_hosts
from darc.proxy.irc import save_irc
from darc.proxy.magnet import save_magnet
from darc.proxy.mail import save_mail
from darc.proxy.null import fetch_sitemap, save_invalid
from darc.requests import request_session
from darc.save import has_folder, has_html, has_raw, sanitise, save_file, save_headers, save_html
from darc.selenium import request_driver
from darc.sites import crawler_hook, loader_hook
from darc.submit import submit_new_host, submit_requests, submit_selenium


def crawler(url: str):
    """Single |requests|_ crawler for a entry link.

    Args:
        url: URL to be crawled by |requests|_.

    The function will first parse the URL using
    :func:`~darc.link.parse_link`, and check if need to crawl the
    URL (c.f. :data:`~darc.const.PROXY_WHITE_LIST`, :data:`~darc.const.PROXY_BLACK_LIST`
    , :data:`~darc.const.LINK_WHITE_LIST` and :data:`~darc.const.LINK_BLACK_LIST`);
    if true, then crawl the URL with |requests|_.

    If the URL is from a brand new host, :mod:`darc` will first try
    to fetch and save ``robots.txt`` and sitemaps of the host
    (c.f. :func:`~darc.save.save_robots` and :func:`~darc.save.save_sitemap`),
    and extract then save the links from sitemaps (c.f. :func:`~darc.parse.read_sitemap`)
    into link database for future crawling (c.f. :func:`~darc.db.save_requests`).
    Also, if the submission API is provided, :func:`~darc.submit.submit_new_host`
    will be called and submit the documents just fetched.

    .. seealso::

        * :func:`darc.proxy.null.fetch_sitemap`

    If ``robots.txt`` presented, and :data:`~darc.const.FORCE` is
    ``False``, :mod:`darc` will check if allowed to crawl the URL.

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
        processing is dropped.

    If the content type of response document is not ignored (c.f.
    :data:`~darc.const.MIME_WHITE_LIST` and :data:`~darc.const.MIME_BLACK_LIST`),
    :mod:`darc` will save the document using :func:`~darc.save.save_html` or
    :func:`~darc.save.save_file` accordingly. And if the submission API
    is provided, :func:`~darc.submit.submit_requests` will be called and
    submit the document just fetched.

    If the response document is HTML (``text/html`` and ``application/xhtml+xml``),
    :func:`~darc.parse.extract_links` will be called then to extract
    all possible links from the HTML document and save such links into
    the database (c.f. :func:`~darc.db.save_requests`).

    And if the response status code is between ``400`` and ``600``,
    the URL will be saved back to the link database
    (c.f. :func:`~darc.db.save_requests`). If **NOT**, the URL will
    be saved into |selenium|_ link database to proceed next steps
    (c.f. :func:`~darc.db.save_selenium`).

    """
    try:
        link = parse_link(url)

        if match_proxy(link.proxy):
            print(render_error(f'[REQUESTS] Ignored proxy type from {link.url} ({link.proxy})',
                               stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
            return

        # save bitcoin address
        if link.proxy == 'bitcoin':
            save_bitcoin(link)
            return

        # save ed2k link
        if link.proxy == 'ed2k':
            save_ed2k(link)
            return

        # save magnet link
        if link.proxy == 'magnet':
            save_magnet(link)
            return

        # save email address
        if link.proxy == 'mail':
            save_mail(link)
            return

        # save IRC address
        if link.proxy == 'irc':
            save_irc(link)
            return

        # save data URI
        if link.proxy == 'data':
            try:
                save_data(link)
            except ValueError as error:
                print(render_error(f'[REQUESTS] Failed to save data URI from {link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
            return

        if match_host(link.host):
            print(render_error(f'[REQUESTS] Ignored hostname from {link.url} ({link.proxy})',
                               stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
            return

        # timestamp
        timestamp = datetime.now()

        path = has_raw(timestamp, link)
        if path is not None:

            if link.proxy not in ('zeronet', 'freenet'):
                # load sitemap.xml
                try:
                    fetch_sitemap(link)
                except Exception:
                    error = f'[Error loading sitemap of {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                    print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member

            # load hosts.txt
            if link.proxy == 'i2p':
                try:
                    fetch_hosts(link)
                except Exception:
                    error = f'[Error loading hosts from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                    print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member

            ext = os.path.splitext(path)[1]
            if ext == '.dat':
                print(stem.util.term.format(f'[REQUESTS] Cached generic file from {link.url}',
                                            stem.util.term.Color.YELLOW))  # pylint: disable=no-member

                # probably hosts.txt
                if link.proxy == 'i2p':
                    with contextlib.suppress(Exception):
                        ct_type = magic.detect_from_filename(path).mime_type
                        if ct_type in ['text/plain', 'text/text']:
                            with open(path) as hosts_file:
                                save_requests(read_hosts(hosts_file))

                return

            print(stem.util.term.format(f'[REQUESTS] Cached HTML document from {link.url}',
                                        stem.util.term.Color.YELLOW))  # pylint: disable=no-member
            with open(path, 'rb') as file:
                html = file.read()

            # add link to queue
            #[QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned
            save_requests(extract_links(link.url, html))

            #QUEUE_SELENIUM.put(link.url)
            save_selenium(link.url, single=True)

        else:

            # if it's a new host
            new_host = has_folder(link) is None

            print(f'[REQUESTS] Requesting {link.url}')

            if new_host:
                if link.proxy not in ('zeronet', 'freenet'):
                    # fetch sitemap.xml
                    try:
                        fetch_sitemap(link)
                    except Exception:
                        error = f'[Error fetching sitemap of {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member

                if link.proxy == 'i2p':
                    # fetch hosts.txt
                    try:
                        fetch_hosts(link)
                    except Exception:
                        error = f'[Error subscribing hosts from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member

                # submit data
                submit_new_host(timestamp, link)

            if not FORCE and not check_robots(link):
                print(render_error(f'[REQUESTS] Robots disallowed link from {link.url}',
                                   stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
                return

            with request_session(link) as session:
                try:
                    # requests session hook
                    response = crawler_hook(link, session)
                except requests.exceptions.InvalidSchema as error:
                    print(render_error(f'[REQUESTS] Failed on {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    save_invalid(link)
                    return
                except requests.RequestException as error:
                    print(render_error(f'[REQUESTS] Failed on {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    #QUEUE_REQUESTS.put(link.url)
                    save_requests(link.url, single=True)
                    return

                # save headers
                save_headers(timestamp, link, response, session)

                # check content type
                ct_type = get_content_type(response)
                if ct_type not in ['text/html', 'application/xhtml+xml']:
                    print(render_error(f'[REQUESTS] Generic content type from {link.url} ({ct_type})',
                                       stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member

                    text = response.content
                    try:
                        path = save_file(timestamp, link, text)
                    except Exception as error:
                        print(render_error(f'[REQUESTS] Failed to save generic file from {link.url} <{error}>',
                                           stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                        return

                    # probably hosts.txt
                    if link.proxy == 'i2p' and ct_type in ['text/plain', 'text/text']:
                        with open(path) as hosts_file:
                            save_requests(read_hosts(hosts_file))

                    if match_mime(ct_type):
                        return

                    # submit data
                    submit_requests(timestamp, link, response, session)

                    return

                html = response.content
                if not html:
                    print(render_error(f'[REQUESTS] Empty response from {link.url}',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    #QUEUE_REQUESTS.put(link.url)
                    save_requests(link.url, single=True)
                    return

                # save HTML
                save_html(timestamp, link, html, raw=True)

                # submit data
                submit_requests(timestamp, link, response, session)

            # add link to queue
            #[QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned
            save_requests(extract_links(link.url, html))

            if not response.ok:
                print(render_error(f'[REQUESTS] Failed on {link.url} [{response.status_code}]',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                #QUEUE_REQUESTS.put(link.url)
                save_requests(link.url, single=True)
                return

            # add link to queue
            #QUEUE_SELENIUM.put(link.url)
            save_selenium(link.url, single=True)

            if SAVE_REQUESTS:
                save_requests(link.url, single=True)

            print(f'[REQUESTS] Requested {link.url}')
    except Exception:
        error = f'[Error from {url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
        #QUEUE_REQUESTS.put(url)
        save_requests(url, single=True)


def loader(url: str):
    """Single |selenium|_ loader for a entry link.

    Args:
        url: URL to be crawled by |requests|_.

    The function will first parse the URL using :func:`~darc.link.parse_link`
    and start loading the URL using |selenium|_ with Google Chrome.

    At this point, :mod:`darc` will call the customised hook function
    from :mod:`darc.sites` to load and return the original
    |Chrome|_ object.

    If successful, the rendered source HTML document will be saved
    using :func:`~darc.save.save_html`, and a full-page screenshot
    will be taken and saved.

    .. note::

       When taking full-page screenshot, :func:`~darc.crawl.loader` will
       use :javascript:`document.body.scrollHeight` to get the total
       height of web page. If the page height is *less than* **1,000 pixels**,
       then :mod:`darc` will by default set the height as **1,000 pixels**.

       Later :mod:`darc` will tell |selenium|_ to resize the window (in
       *headless* mode) to **1,024 pixels** in width and **110%** of the
       page height in height, and take a *PNG* screenshot.

    .. seealso::

       * :data:`darc.const.SE_EMPTY`
       * :data:`darc.const.SE_WAIT`

    If the submission API is provided, :func:`~darc.submit.submit_selenium`
    will be called and submit the document just loaded.

    Later, :func:`~darc.parse.extract_links` will be called then to
    extract all possible links from the HTML document and save such
    links into the |requests|_ database (c.f. :func:`~darc.db.save_requests`).

    """
    try:
        link = parse_link(url)

        # timestamp
        timestamp = datetime.now()

        path = has_html(timestamp, link)
        if path is not None:

            print(stem.util.term.format(f'[SELENIUM] Cached {link.url}', stem.util.term.Color.YELLOW))  # pylint: disable=no-member
            with open(path, 'rb') as file:
                html = file.read()

            # add link to queue
            #[QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned
            save_requests(extract_links(link.url, html))

        else:

            print(f'[SELENIUM] Loading {link.url}')

            # retrieve source from Chrome
            with request_driver(link) as driver:
                try:
                    # selenium driver hook
                    driver = loader_hook(link, driver)
                except urllib3.exceptions.HTTPError as error:
                    print(render_error(f'[SELENIUM] Fail to load {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    #QUEUE_SELENIUM.put(link.url)
                    save_selenium(link.url, single=True)
                    return
                except selenium.common.exceptions.WebDriverException as error:
                    print(render_error(f'[SELENIUM] Fail to load {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    #QUEUE_SELENIUM.put(link.url)
                    save_selenium(link.url, single=True)
                    return

                # get HTML source
                html = driver.page_source

                if html == SE_EMPTY:
                    print(render_error(f'[SELENIUM] Empty page from {link.url}',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    #QUEUE_SELENIUM.put(link.url)
                    save_selenium(link.url, single=True)
                    return

                # save HTML
                save_html(timestamp, link, html)

                try:
                    # get maximum height
                    height = driver.execute_script('return document.body.scrollHeight')

                    # resize window (with some magic numbers)
                    if height < 1000:
                        height = 1000
                    driver.set_window_size(1024, math.ceil(height * 1.1))

                    # take a full page screenshot
                    path = sanitise(link, timestamp, screenshot=True)
                    driver.save_screenshot(path)
                except Exception as error:
                    print(render_error(f'[SELENIUM] Fail to save screenshot from {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member

            # submit data
            submit_selenium(timestamp, link)

            # add link to queue
            #[QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned
            save_requests(extract_links(link.url, html))

            if SAVE_SELENIUM:
                save_selenium(link.url, single=True)

            print(f'[SELENIUM] Loaded {link.url}')
    except Exception:
        error = f'[Error from {url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
        #QUEUE_SELENIUM.put(url)
        save_selenium(url, single=True)
