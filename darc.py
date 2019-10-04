# -*- coding: utf-8 -*-

import argparse
import contextlib
import datetime
import getpass
import glob
import hashlib
import multiprocessing
import os
import queue
import re
import sys
import time
import traceback
import typing
import urllib.parse

import bs4
import requests
import stem
from stem.control import Controller
from stem.process import launch_tor_with_config

###############################################################################
# typings

# argparse.ArgumentParser
ArgumentParser = typing.NewType('ArgumentParser', argparse.ArgumentParser)

# requests.Response
Response = typing.NewType('Response', requests.Response)

# requests.Session
Session = typing.NewType('Session', requests.Session)

###############################################################################
# const

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))

# data storage
PATH_DB = os.path.abspath(os.getenv('PATH_DATA', 'data'))
os.makedirs(PATH_DB, exist_ok=True)

# Socks5 proxy & control port
SOCKS_PORT = os.getenv('SOCKS_PORT', '9050')
SOCKS_CTRL = os.getenv('SOCKS_CTRL', '9051')

# Tor authentication
TOR_PASS = os.getenv('TOR_PASS')
if TOR_PASS is None:
    TOR_PASS = getpass.getpass('Tor authentication: ')

# Tor reset timeout
TOR_RESET = float(os.getenv('TOR_RESET', '60'))

# time delta in seconds
TIME_DELTA = datetime.timedelta(seconds=int(os.getenv('TIME_DELTA', '60')))

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
# session

_SESSION_NORM = None
_SESSION_TOR = None
_CTRL_TOR = None
_PROC_TOR = None
_RST_TOR = None


def renew_tor_session():
    """Renew Tor session."""
    global _CTRL_TOR
    if _CTRL_TOR is None:
        _CTRL_TOR = Controller.from_port(port=int(SOCKS_CTRL))
        _CTRL_TOR.authenticate(TOR_PASS)

    while True:
        time.sleep(TOR_RESET)
        _CTRL_TOR.signal(stem.Signal.NEWNYM)  # pylint: disable=no-member
        time.sleep(_CTRL_TOR.get_newnym_wait())


def tor_session() -> Session:
    """Tor (.onion) session."""
    global _PROC_TOR
    if _PROC_TOR is None:
        _PROC_TOR = launch_tor_with_config(
            config={
                'SocksPort': SOCKS_PORT,
                'ControlPort': SOCKS_CTRL,
            },
            take_ownership=True
        )

    global _RST_TOR
    if _RST_TOR is None:
        _RST_TOR = multiprocessing.Process(target=renew_tor_session)
        _RST_TOR.start()

    global _SESSION_TOR
    if _SESSION_TOR is None:
        _SESSION_TOR = requests.Session()
        _SESSION_TOR.proxies.update({'http':  f'socks5://localhost:{SOCKS_PORT}',
                                     'https': f'socks5://localhost:{SOCKS_PORT}'})
    return _SESSION_TOR


def norm_session() -> Session:
    """Normal session"""
    global _SESSION_NORM
    if _SESSION_NORM is None:
        _SESSION_NORM = requests.Session()
    return _SESSION_NORM


###############################################################################
# save


def check(link: str) -> str:
    """Check if we need to re-craw the link."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    # <scheme>/<identifier>/<timestamp>-<hash>.html
    base = os.path.join(PATH_DB, parse.scheme, host)
    name = hashlib.sha256(link.encode()).hexdigest()
    path = os.path.join(base, name)
    time = datetime.datetime.now()  # pylint: disable=redefined-outer-name

    glob_list = glob.glob(f'{path}_*.html')
    if not glob_list:
        return 'nil'

    item = sorted(glob_list, reverse=True)[0]
    date = datetime.datetime.fromisoformat(item[len(path)+1:-5])
    if time - date > TIME_DELTA:
        return 'nil'
    return item


def sanitise(link: str, makedirs: bool = True) -> str:
    """Sanitise link to path."""
    # return urllib.parse.quote(link, safe='')

    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    # <scheme>/<identifier>/<timestamp>-<hash>.html
    base = os.path.join(PATH_DB, parse.scheme, host)
    name = hashlib.sha256(link.encode()).hexdigest()
    time = datetime.datetime.now().isoformat()  # pylint: disable=redefined-outer-name

    if makedirs:
        os.makedirs(base, exist_ok=True)
    return f'{os.path.join(base, name)}_{time}.html'


def save(link: str, html: bytes):
    """Save response."""
    path = sanitise(link)
    with open(path, 'wb') as file:
        file.write(html)

    safe_link = link.replace('"', '\\"')
    safe_path = path.replace('"', '\\"')
    with open(PATH_MAP, 'a') as file:
        print(f'"{safe_link}","{safe_path}"', file=file)


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
# process

# link regex mapping
LINK_MAP = [
    (r'.*?\.onion', tor_session),
    (r'.*', norm_session),
]


def request_session(link: str) -> Session:
    """Get session."""
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc
    for regex, session in LINK_MAP:
        if re.match(regex, host):
            return session()
    raise UnsupportedLink(link)


def crawler(link: str):
    """Single crawler for a entry link."""
    path = check(link)
    if os.path.isfile(path):

        print(f'Cached {link}')
        with open(path, 'rb') as file:
            html = file.read()

    else:

        print(f'Requesting {link}')

        session = request_session(link)
        try:
            response = session.get(link)
        except requests.exceptions.InvalidSchema:
            return
        except requests.RequestException as error:
            print(f'Failed on {link} ({error})')
            QUEUE.put(link)
            return

        print(f'Requested {link}')

        ct_type = response.headers.get('Content-Type', 'undefined')
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


def _exit():
    """Gracefully exit."""
    with contextlib.suppress():
        QUEUE.close()

    with contextlib.suppress():
        if _SESSION_NORM is not None:
            _SESSION_NORM.close()
    with contextlib.suppress():
        if _SESSION_TOR is not None:
            _SESSION_TOR.close()

    with contextlib.suppress():
        if _CTRL_TOR is not None:
            _CTRL_TOR.close()
    with contextlib.suppress():
        if _PROC_TOR is not None:
            _PROC_TOR.terminate()
    with contextlib.suppress():
        if _RST_TOR is not None:
            _RST_TOR.close()


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
    _exit()


if __name__ == "__main__":
    sys.exit(main())
