# -*- coding: utf-8 -*-

import argparse
import hashlib
import multiprocessing
import os
import queue
import re
import sys
import traceback
import typing
import urllib.parse

import bs4
import requests

###############################################################################
# typings

# argparse.ArgumentParser
ArgumentParser = typing.NewType('ArgumentParser', argparse.ArgumentParser)

# requests.Response
Response = typing.NewType('Response', requests.Response)

###############################################################################
# const

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))

# data storage
PATH_DB = os.path.abspath(os.getenv('PATH_DATA', 'data'))
os.makedirs(PATH_DB, exist_ok=True)

# Socks5 port
SOCKS_PORT = 9050

# link queue
QUEUE = multiprocessing.Queue()

# link database
LINK_DB = list()

# link file mapping
PATH_MAP = os.path.join(PATH_DB, 'link.csv')

###############################################################################
# error


class UnsupportedLink(Exception):
    """The link is not supported."""


###############################################################################
# save


def sanitise(link: str, makedirs: bool = True) -> str:
    """Sanitise link to path."""
    # return urllib.parse.quote(link, safe='')
    link_unquote = urllib.parse.unquote(link)

    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link_unquote)
    host = parse.hostname or parse.netloc
    ident = '.'.join(reversed(host.split('.')))

    # <scheme>/<identifier>/<path>/<hash>
    base = os.path.normpath(os.path.sep.join((parse.scheme, ident, parse.path)))
    name = hashlib.sha256(link.encode()).hexdigest()

    if makedirs:
        os.makedirs(os.path.join(PATH_DB, base), exist_ok=True)
    return f'{os.path.join(PATH_DB, base, name)}.html'


def save(link: str, html: bytes):
    """Save response."""
    path = sanitise(link)
    with open(path, 'wb') as file:
        file.write(html)
    with open(PATH_MAP, 'a') as file:
        print(f'{link!r},{path!r}', file=file)


###############################################################################
# parse


def extract_links(link: str, html: bytes) -> typing.Iterator[str]:
    """Extract links from HTML context."""
    soup = bs4.BeautifulSoup(html, 'html5lib')

    link_list = []
    for child in filter(lambda element: isinstance(element, bs4.element.Tag),
                        soup.descendants):
        href = child.get('href')
        if href is None:
            continue
        link_list.append(urllib.parse.urljoin(link, href))
    yield from filter(lambda link: link not in LINK_DB, set(link_list))


###############################################################################
# request


def default(link: str) -> Response:
    """Request a common link."""
    return requests.get(link)


def tor(link: str) -> Response:
    """Request a Tor (.onion) link."""
    return requests.get(link, proxies={'http':  f'socks5://127.0.0.1:{SOCKS_PORT}',
                                       'https': f'socks5://127.0.0.1:{SOCKS_PORT}'})


###############################################################################
# process

# link regex mapping
LINK_MAP = [
    (r'.*?\.onion', tor),
    (r'.*', default),
]


def request_func(link: str) -> typing.Callable[[str], Response]:
    """Request a link."""
    netloc = urllib.parse.urlparse(link).netloc
    for regex, func in LINK_MAP:
        if re.match(regex, netloc):
            return func
    raise UnsupportedLink(link)


def crawler(link: str):
    """Single crawler for a entry link."""
    path = sanitise(link, makedirs=False)
    if os.path.isfile(path):
        return

    print(f'Requesting {link}')
    request = request_func(link)
    try:
        response = request(link)
    except requests.exceptions.InvalidSchema:
        return
    except requests.RequestException:
        print(f'Failed on {link}')
        QUEUE.put(link)
        return
    print(f'Requested {link}')

    ct_type = response.headers.get('Content-Type')
    if 'html' not in ct_type:
        return
    html = response.content

    # save HTML
    save(link, html)

    # add link to queue
    [QUEUE.put(href) for href in extract_links(link, html)]  # pylint: disable=expression-not-assigned


def process():
    """Main process."""
    pool = multiprocessing.Pool()

    while True:
        link_list = list()
        while True:
            try:
                link = QUEUE.get_nowait()
            except queue.Empty:
                break
            link_list.append(link)

        if link_list:
            pool.map(crawler, link_list)
        else:
            break
    print('Gracefully exit...')


###############################################################################
# __main__


def get_parser() -> ArgumentParser:
    """Argument parser."""
    parser = argparse.ArgumentParser('darc')

    parser.add_argument('-f', '--file', help='read links from file')
    parser.add_argument('link', nargs=argparse.REMAINDER, help='links to craw')

    return parser


def main():
    """Entrypoint."""
    parser = get_parser()
    args = parser.parse_args()

    for link in args.link:
        QUEUE.put(link)
    if args.file is not None:
        with open(args.file) as file:
            for line in file:
                QUEUE.put(line.strip())

    try:
        process()
    except BaseException:
        traceback.print_exc()
    QUEUE.close()


if __name__ == "__main__":
    sys.exit(main())
