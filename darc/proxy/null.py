# -*- coding: utf-8 -*-
"""No Proxy
===============

The :mod:`darc.proxy.null` module contains the auxiliary functions
around managing and processing normal websites with no proxy.

"""

import gzip
import io
import os
import sys

import bs4
import requests
import stem
import stem.control
import stem.process
import stem.util.term

import darc.typing as typing
from darc._compat import RobotFileParser
from darc.const import CHECK, PATH_MISC, get_lock
from darc.db import save_requests
from darc.error import render_error
from darc.link import Link, parse_link
from darc.parse import _check, get_content_type, urljoin
from darc.requests import request_session
from darc.save import save_link

PATH = os.path.join(PATH_MISC, 'invalid.txt')
LOCK = get_lock()


def save_invalid(link: Link) -> None:
    """Save link with invalid scheme.

    The function will save link with invalid scheme to the file
    as defined in :data:`~darc.proxy.null.PATH`.

    Args:
        link: Link object representing the link with invalid scheme.

    """
    with LOCK:  # type: ignore
        with open(PATH, 'a') as file:
            print(link.url, file=file)


def save_robots(link: Link, text: str) -> str:
    """Save ``robots.txt``.

    Args:
        link: Link object of ``robots.txt``.
        text: Content of ``robots.txt``.

    Returns:
        Saved path to ``robots.txt``, i.e.
        ``<root>/<proxy>/<scheme>/<hostname>/robots.txt``.

    See Also:
        * :func:`darc.save.sanitise`

    """
    path = os.path.join(link.base, 'robots.txt')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'# {link.url}', file=file)
        file.write(text)
    return path


def save_sitemap(link: Link, text: str) -> str:
    """Save sitemap.

    Args:
        link: Link object of sitemap.
        text: Content of sitemap.

    Returns:
        Saved path to sitemap, i.e.
        ``<root>/<proxy>/<scheme>/<hostname>/sitemap_<hash>.xml``.

    See Also:
        * :func:`darc.save.sanitise`

    """
    # <proxy>/<scheme>/<host>/sitemap_<hash>.xml
    path = os.path.join(link.base, f'sitemap_{link.name}.xml')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'<!-- {link.url} -->', file=file)
        file.write(text)

    save_link(link)
    return path


def have_robots(link: Link) -> typing.Optional[str]:
    """Check if ``robots.txt`` already exists.

    Args:
        link: Link object to check if ``robots.txt`` already exists.

    Returns:
        * If ``robots.txt`` exists, return the path to ``robots.txt``,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/robots.txt``.
        * If not, return :data:`None`.

    """
    # <proxy>/<scheme>/<host>/robots.txt
    path = os.path.join(link.base, 'robots.txt')
    return path if os.path.isfile(path) else None


def have_sitemap(link: Link) -> typing.Optional[str]:
    """Check if sitemap already exists.

    Args:
        link: Link object to check if sitemap already exists.

    Returns:
        * If sitemap exists, return the path to the sitemap,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/sitemap_<hash>.xml``.
        * If not, return :data:`None`.

    """
    # <proxy>/<scheme>/<host>/sitemap_<hash>.xml
    path = os.path.join(link.base, f'sitemap_{link.name}.xml')
    return path if os.path.isfile(path) else None


def read_robots(link: Link, text: str, host: typing.Optional[str] = None) -> typing.List[Link]:
    """Read ``robots.txt`` to fetch link to sitemaps.

    Args:
        link: Original link to ``robots.txt``.
        text: Content of ``robots.txt``.
        host: Hostname of the URL to ``robots.txt``,
            the value may not be same as in ``link``.

    Returns:
        List of link to sitemaps.

    Note:
        If the link to sitemap is not specified in
        ``robots.txt`` [*]_, the fallback link
        ``/sitemap.xml`` will be used.

        .. [*] https://www.sitemaps.org/protocol.html#submit_robots

    """
    rp = RobotFileParser()
    with io.StringIO(text) as file:
        rp.parse(file)

    sitemaps = rp.site_maps()
    if sitemaps is None:
        return [parse_link(urljoin(link.url, '/sitemap.xml'))]
    return [parse_link(urljoin(link.url, sitemap), host=host) for sitemap in sitemaps]


def get_sitemap(link: Link, text: str, host: typing.Optional[str] = None) -> typing.List[Link]:
    """Fetch link to other sitemaps from a sitemap.

    Args:
        link: Original link to the sitemap.
        text: Content of the sitemap.
        host: Hostname of the URL to the sitemap,
            the value may not be same as in ``link``.

    Returns:
        List of link to sitemaps.

    Note:
        As specified in the sitemap protocol,
        it may contain links to other sitemaps. [*]_

        .. [*] https://www.sitemaps.org/protocol.html#index

    """
    sitemaps = list()
    soup = bs4.BeautifulSoup(text, 'html5lib')

    # https://www.sitemaps.org/protocol.html#index
    for loc in soup.select('sitemapindex > sitemap > loc'):
        sitemaps.append(urljoin(link.url, loc.text))
    return [parse_link(sitemap, host=host) for sitemap in sitemaps]


def read_sitemap(link: Link, text: str, check: bool = CHECK) -> typing.List[Link]:
    """Read sitemap.

    Args:
        link: Original link to the sitemap.
        text: Content of the sitemap.
        check: If perform checks on extracted links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of links extracted.

    See Also:
        * :func:`darc.parse._check`
        * :func:`darc.parse._check_ng`

    """
    soup = bs4.BeautifulSoup(text, 'html5lib')

    # https://www.sitemaps.org/protocol.html
    temp_list = [parse_link(urljoin(link.url, loc.text), host=link.host) for loc in soup.select('urlset > url > loc')]

    # check content / proxy type
    if check:
        return _check(temp_list)
    return temp_list


def fetch_sitemap(link: Link, force: bool = False) -> None:
    """Fetch sitemap.

    The function will first fetch the ``robots.txt``, then
    fetch the sitemaps accordingly.

    Args:
        link: Link object to fetch for its sitemaps.
        force: Force refetch its sitemaps.

    Returns:
        Contents of ``robots.txt`` and sitemaps.

    See Also:
        * :func:`darc.proxy.null.read_robots`
        * :func:`darc.proxy.null.read_sitemap`
        * :func:`darc.parse.get_sitemap`

    """
    if force:
        print(stem.util.term.format(f'[ROBOTS] Force refetch {link.url}',
                                    stem.util.term.Color.YELLOW))  # pylint: disable=no-member

    robots_path = None if force else have_robots(link)
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
                print(render_error(f'[ROBOTS] Unresolved content type on {robots_link.url} ({ct_type})',
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

    if force:
        print(stem.util.term.format(f'[SITEMAP] Force refetch {link.url}',
                                    stem.util.term.Color.YELLOW))  # pylint: disable=no-member

    sitemaps = read_robots(link, robots_text, host=link.host)
    for sitemap_link in sitemaps:
        sitemap_path = None if force else have_sitemap(sitemap_link)
        if sitemap_path is not None:

            print(stem.util.term.format(f'[SITEMAP] Cached {sitemap_link.url}',
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
                print(render_error(f'[SITEMAP] Unresolved content type on {sitemap_link.url} ({ct_type})',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                continue

            print(f'[SITEMAP] Fetched {sitemap_link.url}')

        # get more sitemaps
        sitemaps.extend(get_sitemap(sitemap_link, sitemap_text, host=link.host))

        # add link to queue
        save_requests(read_sitemap(link, sitemap_text))
