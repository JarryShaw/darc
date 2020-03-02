# -*- coding: utf-8 -*-
"""Web crawlers."""

import datetime
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

from darc.const import FORCE, SE_EMPTY
from darc.db import save_requests, save_selenium
from darc.error import render_error
from darc.link import parse_link
from darc.parse import (check_robots, extract_links, get_content_type, match_host, match_mime,
                        match_proxy)
from darc.proxy.i2p import fetch_hosts
from darc.proxy.null import fetch_sitemap
from darc.requests import request_session
from darc.save import has_folder, has_html, has_raw, save_file, save_headers, save_html
from darc.selenium import request_driver
from darc.sites import crawler_hook, loader_hook
from darc.submit import submit_new_host, submit_requests, submit_selenium


def crawler(url: str):
    """Single requests crawler for a entry link."""
    link = parse_link(url)

    if match_host(link.host):
        print(render_error(f'[REQUESTS] Ignored hostname from {link.url} ({link.proxy})',
                           stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
        return

    if match_proxy(link.proxy):
        print(render_error(f'[REQUESTS] Ignored proxy type from {link.url} ({link.proxy})',
                           stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member
        return

    try:
        # timestamp
        timestamp = datetime.datetime.now()

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

            print(stem.util.term.format(f'[REQUESTS] Cached {link.url}', stem.util.term.Color.YELLOW))  # pylint: disable=no-member
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
                    return
                except requests.RequestException as error:
                    print(render_error(f'[REQUESTS] Failed on {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    #QUEUE_REQUESTS.put(link.url)
                    save_requests(link.url, single=True)
                    return

            # save headers
            save_headers(timestamp, link, response)

            # check content type
            ct_type = get_content_type(response, 'text/html')
            if ct_type not in ['text/html', 'application/xhtml+xml']:
                print(render_error(f'[REQUESTS] Generic content type from {link.url} ({ct_type})',
                                   stem.util.term.Color.YELLOW), file=sys.stderr)  # pylint: disable=no-member

                if match_mime(ct_type):
                    return

                text = response.content
                try:
                    save_file(timestamp, link, text)
                except Exception as error:
                    print(render_error(f'[REQUESTS] Failed to save generic file from {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    #QUEUE_REQUESTS.put(link.url)
                    save_requests(link.url, single=True)
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
            submit_requests(timestamp, link, response)

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

            print(f'[REQUESTS] Requested {link.url}')
    except Exception:
        error = f'[Error from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
        #QUEUE_REQUESTS.put(link.url)
        save_requests(link.url, single=True)


def loader(url: str):
    """Single selenium loader for a entry link."""
    link = parse_link(url)
    try:
        # timestamp
        timestamp = datetime.datetime.now()

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

            # submit data
            submit_selenium(timestamp, link)

            # add link to queue
            #[QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned
            save_requests(extract_links(link.url, html))

            print(f'[SELENIUM] Loaded {link.url}')
    except Exception:
        error = f'[Error from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
        #QUEUE_SELENIUM.put(link.url)
        save_selenium(link.url, single=True)
