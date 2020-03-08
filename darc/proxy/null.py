# -*- coding: utf-8 -*-
"""No Proxy
===============

The :mod:`darc.proxy.null` module contains the auxiliary functions
around managing and processing normal websites with no proxy.

"""

import gzip
import multiprocessing
import os
import sys

import requests
import stem
import stem.control
import stem.process
import stem.util.term

from darc.const import PATH_MISC
from darc.db import save_requests
from darc.error import render_error
from darc.link import Link, parse_link
from darc.parse import get_content_type, get_sitemap, read_robots, read_sitemap, urljoin
from darc.requests import request_session
from darc.save import has_robots, has_sitemap, save_robots, save_sitemap

PATH = os.path.join(PATH_MISC, 'invalid.txt')
LOCK = multiprocessing.Lock()


def save_invalid(link: Link):
    """Save link with invalid scheme.

    The function will save link with invalid scheme to the file
    as defined in :data:`~darc.proxy.null.PATH`.

    Args:
        link: Link object representing the link with invalid scheme.

    """
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url_parse.path, file=file)


def fetch_sitemap(link: Link):
    """Fetch sitemap.

    The function will first fetch the ``robots.txt``, then
    fetch the sitemaps accordingly.

    Args:
        link: Link object to fetch for its sitemaps.

    See Also:
        * :func:`darc.parse.read_robots`
        * :func:`darc.parse.read_sitemap`
        * :func:`darc.parse.get_sitemap`

    """
    robots_path = has_robots(link)
    if robots_path is not None:

        print(stem.util.term.format(f'[ROBOTS] Cached {link.url}',
                                    stem.util.term.Color.YELLOW))  # pylint: disable=no-member
        with open(robots_path) as file:
            robots_text = file.read()

    else:

        robots_link = parse_link(urljoin(link.url, '/robots.txt'))
        print(f'[ROBOTS] Checking {robots_link.url}')

        with request_session(robots_link) as session:
            try:
                response = session.get(robots_link.url)
            except requests.RequestException as error:
                print(render_error(f'[ROBOTS] Failed on {robots_link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                return

        if response.ok:
            ct_type = get_content_type(response)
            if ct_type not in ['text/text', 'text/plain']:
                print(render_error(f'[ROBOTS] Unresolved content type on {robots_link.url} ({ct_type}',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                robots_text = ''
            else:
                robots_text = response.text
                save_robots(robots_link, robots_text)
                print(f'[ROBOTS] Checked {robots_link.url}')
        else:
            print(render_error(f'[ROBOTS] Failed on {robots_link.url} [{response.status_code}]',
                               stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
            robots_text = ''

    sitemaps = read_robots(link.url, robots_text, host=link.host)
    for sitemap_link in sitemaps:
        sitemap_path = has_sitemap(sitemap_link)
        if sitemap_path is not None:

            print(stem.util.term.format(f'[SITEMAP] Cached {link.url}',
                                        stem.util.term.Color.YELLOW))  # pylint: disable=no-member
            with open(sitemap_path) as file:
                sitemap_text = file.read()

        else:

            print(f'[SITEMAP] Fetching {sitemap_link.url}')

            with request_session(sitemap_link) as session:
                try:
                    response = session.get(sitemap_link.url)
                except requests.RequestException as error:
                    print(render_error(f'[SITEMAP] Failed on {sitemap_link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    continue

            if not response.ok:
                print(render_error(f'[SITEMAP] Failed on {sitemap_link.url} [{response.status_code}]',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                continue

            # check content type
            ct_type = get_content_type(response)
            if ct_type == 'application/gzip':
                try:
                    sitemap_text = gzip.decompress(response.content).decode()
                except UnicodeDecodeError:
                    sitemap_text = response.text
            elif ct_type in ['text/xml', 'text/html']:
                sitemap_text = response.text
                save_sitemap(sitemap_link, sitemap_text)
            else:
                print(render_error(f'[SITEMAP] Unresolved content type on {sitemap_link.url} ({ct_type}',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                continue

            print(f'[SITEMAP] Fetched {sitemap_link.url}')

        # get more sitemaps
        sitemaps.extend(get_sitemap(sitemap_link.url, sitemap_text, host=link.host))

        # add link to queue
        #[QUEUE_REQUESTS.put(url) for url in read_sitemap(link.url, sitemap_text)]  # pylint: disable=expression-not-assigned
        save_requests(read_sitemap(link.url, sitemap_text))
