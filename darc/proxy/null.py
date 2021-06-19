# -*- coding: utf-8 -*-
"""No Proxy
===============

The :mod:`darc.proxy.null` module contains the auxiliary functions
around managing and processing normal websites with no proxy.

"""

import gzip
import io
import json
import os
from typing import TYPE_CHECKING

import bs4
import requests

from darc._compat import RobotFileParser
from darc.const import CHECK, PATH_MISC, get_lock
from darc.db import save_requests
from darc.link import parse_link
from darc.logging import logger
from darc.parse import _check, get_content_type, urljoin
from darc.requests import request_session
from darc.save import save_link

if TYPE_CHECKING:
    from typing import List, Optional

    import darc.link as darc_link  # Link

PATH = os.path.join(PATH_MISC, 'invalid.txt')
LOCK = get_lock()


def save_invalid(link: 'darc_link.Link') -> None:
    """Save link with invalid scheme.

    The function will save link with invalid scheme to the file
    as defined in :data:`~darc.proxy.null.PATH`.

    Args:
        link: Link object representing the link with invalid scheme.

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': link.url,
            }), file=file)


def save_robots(link: 'darc_link.Link', text: str) -> str:
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


def save_sitemap(link: 'darc_link.Link', text: str) -> str:
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


def have_robots(link: 'darc_link.Link') -> 'Optional[str]':
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


def have_sitemap(link: 'darc_link.Link') -> 'Optional[str]':
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


def read_robots(link: 'darc_link.Link', text: str, host: 'Optional[str]' = None) -> 'List[darc_link.Link]':
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
        return [parse_link(urljoin(link.url, '/sitemap.xml'), backref=link)]
    return [parse_link(urljoin(link.url, sitemap), host=host, backref=link) for sitemap in sitemaps]


def get_sitemap(link: 'darc_link.Link', text: str, host: 'Optional[str]' = None) -> 'List[darc_link.Link]':
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
    sitemaps = []
    soup = bs4.BeautifulSoup(text, 'html5lib')

    # https://www.sitemaps.org/protocol.html#index
    for loc in soup.select('sitemapindex > sitemap > loc'):
        sitemaps.append(urljoin(link.url, loc.text))
    return [parse_link(sitemap, host=host, backref=link) for sitemap in sitemaps]


def read_sitemap(link: 'darc_link.Link', text: str, check: bool = CHECK) -> 'List[darc_link.Link]':
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
    temp_list = [parse_link(urljoin(link.url, loc.text), host=link.host, backref=link)
                 for loc in soup.select('urlset > url > loc')]

    # check content / proxy type
    if check:
        return _check(temp_list)
    return temp_list


def fetch_sitemap(link: 'darc_link.Link', force: bool = False) -> None:
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
        logger.warning('[ROBOTS] Force refetch %s', link.url)

    robots_path = None if force else have_robots(link)
    if robots_path is not None:

        logger.warning('[ROBOTS] Cached %s', link.url)
        with open(robots_path) as file:
            robots_text = file.read()

    else:

        robots_link = parse_link(urljoin(link.url, '/robots.txt'), backref=link)
        logger.info('[ROBOTS] Checking %s', robots_link.url)

        with request_session(robots_link) as session:
            try:
                response = session.get(robots_link.url)
            except requests.RequestException:
                logger.pexc(message=f'[ROBOTS] Failed on {robots_link.url}')
                return

        if response.ok:
            ct_type = get_content_type(response)
            if ct_type not in ['text/text', 'text/plain']:
                logger.error('[ROBOTS] Unresolved content type on %s (%s)', robots_link.url, ct_type)
                robots_text = ''
            else:
                robots_text = response.text
                save_robots(robots_link, robots_text)
                logger.info('[ROBOTS] Checked %s', robots_link.url)
        else:
            logger.error('[ROBOTS] Failed on %s [%d]', robots_link.url, response.status_code)
            robots_text = ''

    if force:
        logger.warning('[SITEMAP] Force refetch %s', link.url)

    sitemaps = read_robots(link, robots_text, host=link.host)
    for sitemap_link in sitemaps:
        sitemap_path = None if force else have_sitemap(sitemap_link)
        if sitemap_path is not None:

            logger.warning('[SITEMAP] Cached %s', sitemap_link.url)
            with open(sitemap_path) as file:
                sitemap_text = file.read()

        else:

            logger.info('[SITEMAP] Fetching %s', sitemap_link.url)

            with request_session(sitemap_link) as session:
                try:
                    response = session.get(sitemap_link.url)
                except requests.RequestException:
                    logger.pexc(message=f'[SITEMAP] Failed on {sitemap_link.url}')
                    continue

            if not response.ok:
                logger.error('[SITEMAP] Failed on %s [%d]', sitemap_link.url, response.status_code)
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
                logger.error('[SITEMAP] Unresolved content type on %s (%s)', sitemap_link.url, ct_type)
                continue

            logger.info('[SITEMAP] Fetched %s', sitemap_link.url)

        # get more sitemaps
        sitemaps.extend(get_sitemap(sitemap_link, sitemap_text, host=link.host))

        # add link to queue
        save_requests(read_sitemap(link, sitemap_text))
