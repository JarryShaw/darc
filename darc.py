# -*- coding: utf-8 -*-

import argparse
import contextlib
import datetime
import math
import getpass
import glob
import hashlib
import multiprocessing
import os
import queue
import re
import sys
import traceback
import typing
import urllib.parse
import warnings

import bs4
import requests
import stem
from stem.control import Controller as TorController
from stem.process import launch_tor_with_config
from stem.util import term

###############################################################################
# typings

# argparse.ArgumentParser
ArgumentParser = typing.NewType('ArgumentParser', argparse.ArgumentParser)

# requests.Response
Response = typing.NewType('Response', requests.Response)

# requests.Session
Session = typing.NewType('Session', requests.Session)

# multiprocessing.Queue
Queue = typing.NewType('Queue', multiprocessing.Queue)

# subprocess.Popen
Popen = typing.NewType('Popen', __import__('subprocess').Popen)

# stem.control.Controller
Controller = typing.NewType('Controller', TorController)

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

# time delta for caches in seconds
_TIME_CACHE = float(os.getenv('TIME_CACHE', '60'))
if math.isfinite(_TIME_CACHE):
    TIME_CACHE = datetime.timedelta(seconds=_TIME_CACHE)
else:
    TIME_CACHE = None

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


class TorBootstrapFailed(Warning):
    """Tor bootstrap process failed."""


###############################################################################
# session

# Tor bootstrapped flag
_TOR_BS_FLAG = multiprocessing.Value('B', False)
# Tor bootstrapping lock
_TOR_BS_LOCK = multiprocessing.Lock()
# Tor controller
_CTRL_TOR = None
# Tor daemon process
_PROC_TOR = None


def renew_tor_session():
    """Renew Tor session."""
    if _CTRL_TOR is None:
        return
    _CTRL_TOR.signal(stem.Signal.NEWNYM)  # pylint: disable=no-member


def print_bootstrap_lines(line: str):
    """Print Tor bootstrap lines."""
    if 'Bootstrapped ' in line:
        print(term.format(line, term.Color.BLUE))  # pylint: disable=no-member


def tor_bootstrap():
    """Tor bootstrap."""
    # don't re-bootstrap
    if _TOR_BS_FLAG.value:
        return

    global _CTRL_TOR, _PROC_TOR, TOR_PASS

    # launch Tor process
    _PROC_TOR = launch_tor_with_config(
        config={
            'SocksPort': SOCKS_PORT,
            'ControlPort': SOCKS_CTRL,
        },
        take_ownership=True,
        init_msg_handler=print_bootstrap_lines,
    )

    if TOR_PASS is None:
        TOR_PASS = getpass.getpass('Tor authentication: ')

    # Tor controller process
    _CTRL_TOR = TorController.from_port(port=int(SOCKS_CTRL))
    _CTRL_TOR.authenticate(TOR_PASS)

    # update flag
    _TOR_BS_FLAG.value = True


def tor_session() -> Session:
    """Tor (.onion) session."""
    if not _TOR_BS_FLAG.value:
        with _TOR_BS_LOCK:
            try:
                tor_bootstrap()
            except Exception as error:
                warning = warnings.formatwarning(error, TorBootstrapFailed, __file__, 148, 'tor_bootstrap()')
                print(''.join(
                    term.format(line, term.Color.YELLOW) for line in warning.splitlines(True)  # pylint: disable=no-member
                ), end='', file=sys.stderr)

    session = requests.Session()
    session.proxies.update({
        # c.f. https://stackoverflow.com/a/42972942
        'http':  f'socks5h://localhost:{SOCKS_PORT}',
        'https': f'socks5h://localhost:{SOCKS_PORT}'
    })
    return session


def norm_session() -> Session:
    """Normal session"""
    return requests.Session()


###############################################################################
# save

# lock for file I/O
_SAVE_LOCK = multiprocessing.Lock()


def check(link: str) -> str:
    """Check if we need to re-craw the link."""
    if _TIME_CACHE is None:
        return 'nil'

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
    if time - date > TIME_CACHE:
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
    with _SAVE_LOCK:
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

        print(term.format(f'Cached {link}', term.Color.YELLOW))  # pylint: disable=no-member
        with open(path, 'rb') as file:
            html = file.read()

    else:

        print(f'Requesting {link}')

        with request_session(link) as session:
            try:
                response = session.get(link)
            except requests.exceptions.InvalidSchema:
                return
            except requests.RequestException as error:
                print(term.format(f'Failed on {link} ({error})', term.Color.RED))  # pylint: disable=no-member
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
    with multiprocessing.Pool() as pool:
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
            renew_tor_session()
    print(term.format('Gracefully exiting...', term.Color.MAGENTA))  # pylint: disable=no-member


###############################################################################
# __main__


def _exit():
    """Gracefully exit."""
    def caller(target: typing.Optional[typing.Union[Queue, Popen]], function: str):
        """Wrapper caller."""
        if target is None:
            return
        with contextlib.suppress():
            getattr(target, function)()

    # close link queue
    caller(QUEUE, 'close')

    # close Tor processes
    caller(_CTRL_TOR, 'close')
    caller(_PROC_TOR, 'terminate')


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
