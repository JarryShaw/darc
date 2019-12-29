# -*- coding: utf-8 -*-

import argparse
import contextlib
import copy
import datetime
import getpass
import glob
import hashlib
import json
import math
import mimetypes
import multiprocessing
import os
import platform
import posixpath
#import queue
import random
import re
import shutil
import sys
import time
import traceback
import typing
import urllib.parse
import warnings

import bs4
import defusedxml.ElementTree
import requests
import stem
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.proxy import Proxy, ProxyType
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

# selenium.webdriver.Chrome
Driver = typing.NewType('Driver', webdriver.Chrome)

###############################################################################
# const

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))
CWD = os.path.realpath(os.curdir)

# process number
DARC_CPU = os.getenv('DARC_CPU')
if DARC_CPU is not None:
    DARC_CPU = int(DARC_CPU)

# data storage
PATH_DB = os.path.abspath(os.getenv('PATH_DATA', 'data'))
os.makedirs(PATH_DB, exist_ok=True)

# Socks5 proxy & control port
SOCKS_PORT = os.getenv('SOCKS_PORT', '9050')
SOCKS_CTRL = os.getenv('SOCKS_CTRL', '9051')

# Tor authentication
TOR_PASS = os.getenv('TOR_PASS')

TOR_STEM = bool(int(os.getenv('TOR_STEM', '1')))

# time delta for caches in seconds
_TIME_CACHE = float(os.getenv('TIME_CACHE', '60'))
if math.isfinite(_TIME_CACHE):
    TIME_CACHE = datetime.timedelta(seconds=_TIME_CACHE)
else:
    TIME_CACHE = None

DEBUG = bool(int(os.getenv('DARC_DEBUG', '0')))

# link queue
#QUEUE = multiprocessing.Queue()
MANAGER = multiprocessing.Manager()
LIST = MANAGER.list()

# link file mapping
PATH_MAP = os.path.join(PATH_DB, 'link.csv')

# selenium wait time
DRIVER_WAIT = int(os.getenv('DARC_WAIT', '60'))

# extract link pattern
EX_LINK = urllib.parse.unquote(os.getenv('EX_LINK', r'.*'))

###############################################################################
# selenium

_proxy = Proxy()
_proxy.proxy_type = ProxyType.MANUAL
_proxy.http_proxy = f'socks5://localhost:{SOCKS_PORT}'
_proxy.ssl_proxy = f'socks5://localhost:{SOCKS_PORT}'

_norm_capabilities = webdriver.DesiredCapabilities.CHROME
_tor_capabilities = copy.deepcopy(webdriver.DesiredCapabilities.CHROME)
_proxy.add_to_capabilities(_tor_capabilities)

_system = platform.system()

# c.f. https://peter.sh/experiments/chromium-command-line-switches/
_norm_options = webdriver.ChromeOptions()
if _system == 'Darwin':
    _norm_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    if not DEBUG:
        _norm_options.add_argument('--headless')
elif _system == 'Linux':
    _norm_options.binary_location = shutil.which('google-chrome') or '/usr/bin/google-chrome'
    _norm_options.add_argument('--headless')
    # c.f. https://crbug.com/638180; https://stackoverflow.com/a/50642913/7218152
    if getpass.getuser() == 'root':
        _norm_options.add_argument('--no-sandbox')
    #_norm_options.add_argument('--disable-dev-shm-usage')
else:
    sys.exit(f'unsupported system: {_system}')

_tor_options = copy.deepcopy(_norm_options)
# c.f. https://www.chromium.org/developers/design-documents/network-stack/socks-proxy
_tor_options.add_argument(f'--proxy-server=socks5://localhost:{SOCKS_PORT}')
_tor_options.add_argument('--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE localhost"')

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
    if DEBUG:
        print(term.format(line, term.Color.BLUE))  # pylint: disable=no-member
        return

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
                if TOR_STEM:
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


def check_robots(link: str) -> str:
    """Check if robots.txt already exists."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    # <scheme>/<identifier>/<sitemap>
    return os.path.join(PATH_DB, parse.scheme, host, 'robots.txt')


def check_sitemap(link: str) -> str:
    """Check if sitemap.xml already exists."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    # <scheme>/<identifier>/<sitemap>
    return os.path.join(PATH_DB, parse.scheme, host, 'sitemap.xml')


def check_folder(link: str) -> bool:
    """Check if folder created."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    # <scheme>/<identifier>/<timestamp>-<hash>.html
    base = os.path.join(PATH_DB, parse.scheme, host)
    return os.path.isdir(base)


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
    if TIME_CACHE is None:
        return item

    date = datetime.datetime.fromisoformat(item[len(path)+1:-5])
    if time - date > TIME_CACHE:
        return 'nil'
    return item


def sanitise(link: str, makedirs: bool = True,
             raw: bool = False, headers: bool = False) -> str:
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
    if raw:
        return f'{os.path.join(base, name)}_{time}_raw.html'
    if headers:
        return f'{os.path.join(base, name)}_{time}.json'
    return f'{os.path.join(base, name)}_{time}.html'


def save_robots(link: str, text: str) -> str:
    """Save `robots.txt`."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    ## <scheme>/<identifier>/<sitemap>
    base = os.path.join(PATH_DB, parse.scheme, host)
    os.makedirs(base, exist_ok=True)

    path = os.path.join(base, 'robots.txt')
    with open(path, 'w') as file:
        file.write(text)
    return path


def save_sitemap(link: str, text: str) -> str:
    """Save `sitemap.xml`."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    # <scheme>/<identifier>/<sitemap>
    base = os.path.join(PATH_DB, parse.scheme, host)
    os.makedirs(base, exist_ok=True)

    path = os.path.join(base, 'sitemap.xml')
    with open(path, 'w') as file:
        file.write(text)
    return path


def save_headers(link: str, response: Response) -> str:
    """Save HTTP response headers."""
    data = dict()
    data['[metadata]'] = dict()
    data.update(response.headers)

    data['[metadata]']['URL'] = response.url
    data['[metadata]']['Reason'] = response.reason
    data['[metadata]']['Status-Code'] = response.status_code

    data['[metadata]']['Cookies'] = response.cookies.get_dict()
    data['[metadata]']['Request-Method'] = response.request.method
    data['[metadata]']['Request-Headers'] = dict(response.request.headers)

    path = sanitise(link, headers=True)
    with open(path, 'w') as file:
        json.dump(data, file, indent=2)
    return path


def save(link: str, html: typing.Union[str, bytes], orig: bool = False) -> str:
    """Save response."""
    path = sanitise(link, raw=orig)
    if orig:
        with open(path, 'wb') as file:
            file.write(html)
        return path

    with open(path, 'w') as file:
        file.write(html)

    safe_link = link.replace('"', '\\"')
    safe_path = path.replace('"', '\\"')
    with _SAVE_LOCK:
        with open(PATH_MAP, 'a') as file:
            print(f'"{safe_link}","{safe_path}"', file=file)
    return path


def save_file(link: str, text: bytes, mime: str):
    """Save file."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    temp_path = parse.path[1:]
    if not os.path.splitext(temp_path)[1]:
        temp_path += mimetypes.guess_extension(mime) or ''

    # <scheme>/<identifier>/...
    base = os.path.join(PATH_DB, parse.scheme, host)
    root = posixpath.split(temp_path)
    path = os.path.join(base, *root[:-1])
    os.makedirs(path, exist_ok=True)

    os.chdir(path)
    with open(root[-1], 'wb') as file:
        file.write(text)
    os.chdir(CWD)

    safe_link = link.replace('"', '\\"')
    safe_path = os.path.join(path, root[-1]).replace('"', '\\"')
    with _SAVE_LOCK:
        with open(PATH_MAP, 'a') as file:
            print(f'"{safe_link}","{safe_path}"', file=file)


###############################################################################
# parse


def get_sitemap(link: str, text: str) -> str:
    """Fetch link to sitemap."""
    for line in filter(lambda line: line.strip().casefold(), text.splitlines()):
        if line.startswith('sitemap'):
            with contextlib.suppress(ValueError):
                _, sitemap = line.split(':')
                return urllib.parse.urljoin(link, sitemap.strip())
    return urllib.parse.urljoin(link, '/sitemap.xml')


def read_sitemap(link: str, path: str) -> str:
    """Read sitemap."""
    tree = defusedxml.ElementTree.parse(path)
    root = tree.getroot()

    link_list = list()
    root_tag = root.tag[-6:]
    if root_tag == 'urlset':
        schema = root.tag[:-6]  # urlset
        for loc in root.findall(f'{schema}url/{schema}loc'):
            link_list.append(urllib.parse.urljoin(link, loc.text))
    yield from set(link_list)


def extract_links(link: str, html: bytes) -> typing.Iterator[str]:
    """Extract links from HTML context."""
    soup = bs4.BeautifulSoup(html, 'html5lib')

    link_list = []
    for child in filter(lambda element: isinstance(element, bs4.element.Tag),
                        soup.descendants):
        href = child.get('href')
        if href is None:
            continue
        temp_link = urllib.parse.urljoin(link, href)

        parse = urllib.parse.urlparse(temp_link)
        host = parse.hostname or parse.netloc
        if re.match(EX_LINK, host) is None:
            continue

        link_list.append(temp_link)
    yield from set(link_list)


###############################################################################
# process

# link regex mapping
LINK_MAP = [
    (r'.*?\.onion', tor_session, _tor_options, _tor_capabilities),
    (r'.*', norm_session, _norm_options, _norm_capabilities),
]


def request_session(link: str) -> Session:
    """Get session."""
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc
    for regex, session, _, _ in LINK_MAP:
        if re.match(regex, host):
            return session()
    raise UnsupportedLink(link)


def request_driver(link: str) -> Driver:
    """Get selenium driver."""
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc
    for regex, _, options, capabilities in LINK_MAP:
        if re.match(regex, host):
            return webdriver.Chrome(options=options, desired_capabilities=capabilities)
    raise UnsupportedLink(link)


def fetch_sitemap(link: str):
    """Fetch sitemap."""
    robots_path = check_robots(link)
    if os.path.isfile(robots_path):
        with open(robots_path) as file:
            robots_text = file.read()
    else:
        robots_link = urllib.parse.urljoin(link, '/robots.txt')
        with request_session(robots_link) as session:
            try:
                response = session.get(robots_link)
            except requests.exceptions.InvalidSchema:
                return
            except requests.RequestException as error:
                print(term.format(f'Failed on {robots_link} <{error}>', term.Color.RED))  # pylint: disable=no-member
                return

        if response.ok:
            save_robots(robots_link, response.text)
            robots_text = response.text
        else:
            print(term.format(f'Failed on {robots_link} [{response.status_code}]', term.Color.RED))  # pylint: disable=no-member
            robots_text = ''

    sitemap_link = get_sitemap(link, robots_text)
    sitemap_path = check_sitemap(sitemap_link)
    if not os.path.isfile(sitemap_path):
        with request_session(sitemap_link) as session:
            try:
                response = session.get(sitemap_link)
            except requests.exceptions.InvalidSchema:
                return
            except requests.RequestException as error:
                print(term.format(f'Failed on {sitemap_link} <{error}>', term.Color.RED))  # pylint: disable=no-member
                return

        if not response.ok:
            print(term.format(f'Failed on {sitemap_link} [{response.status_code}]', term.Color.RED))  # pylint: disable=no-member
            return
        save_sitemap(sitemap_link, response.text)

    # add link to queue
    #[QUEUE.put(url) for url in read_sitemap(link, sitemap_path)]  # pylint: disable=expression-not-assigned
    [LIST.append(url) for url in read_sitemap(link, sitemap_path)]  # pylint: disable=expression-not-assigned


def crawler(link: str):
    """Single crawler for a entry link."""
    try:
        path = check(link)
        if os.path.isfile(path):

            print(term.format(f'Cached {link}', term.Color.YELLOW))  # pylint: disable=no-member
            with open(path, 'rb') as file:
                html = file.read()

            # add link to queue
            #[QUEUE.put(href) for href in extract_links(link, html)]  # pylint: disable=expression-not-assigned
            [LIST.append(href) for href in extract_links(link, html)]  # pylint: disable=expression-not-assigned

        else:

            print(f'Requesting {link}')

            # fetch sitemap.xml
            if not check_folder(link):
                with contextlib.suppress(Exception):
                    fetch_sitemap(link)

            with request_session(link) as session:
                try:
                    response = session.get(link)
                except requests.exceptions.InvalidSchema:
                    return
                except requests.RequestException as error:
                    print(term.format(f'Failed on {link} <{error}>', term.Color.RED))  # pylint: disable=no-member
                    #QUEUE.put(link)
                    LIST.append(link)
                    return

            save_headers(link, response)
            if not response.ok:
                print(term.format(f'Failed on {link} [{response.status_code}]', term.Color.RED))  # pylint: disable=no-member
                #QUEUE.put(link)
                LIST.append(link)
                return

            ct_type = response.headers.get('Content-Type', 'undefined').lower()
            if 'html' not in ct_type:
                print(term.format(f'Unexpected content type from {link} ({ct_type})', term.Color.RED))  # pylint: disable=no-member
                return
                # text = response.content
                # save_file(link, text, ct_type)

            # save HTML
            save(link, response.content, orig=True)

            # wait for some time to avoid Too Many Requests
            time.sleep(random.random() * DRIVER_WAIT)

            # retrieve source from Chrome
            with request_driver(link) as driver:
                # wait for page to finish loading
                driver.implicitly_wait(DRIVER_WAIT)

                try:
                    driver.get(link)
                except WebDriverException:
                    print(term.format(f'Failed on {link} <{error}>', term.Color.RED))  # pylint: disable=no-member
                    LIST.append(link)
                    return

                # get HTML source
                html = driver.page_source

            # save HTML
            save(link, html)

            # add link to queue
            #[QUEUE.put(href) for href in extract_links(link, html)]  # pylint: disable=expression-not-assigned
            [LIST.append(href) for href in extract_links(link, html)]  # pylint: disable=expression-not-assigned

            print(f'Requested {link}')
    except Exception:
        traceback.print_exc()
        LIST.append(link)


def process():
    """Main process."""
    with multiprocessing.Pool(processes=DARC_CPU) as pool:
        while True:
            link_list = list()
            while True:
                #try:
                #    link = QUEUE.get_nowait()
                #except queue.Empty:
                #    break
                try:
                    link = LIST.pop()
                except IndexError:
                    break
                link_list.append(link)

            if link_list:
                random.shuffle(link_list)
                pool.map(crawler, set(link_list))
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
    #caller(QUEUE, 'close')
    caller(MANAGER, 'shutdown')

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
        #QUEUE.put(link)
        LIST.append(link)

    if args.file is not None:
        with open(args.file) as file:
            for line in file:
                #QUEUE.put(line.strip())
                LIST.append(line.strip())

    try:
        process()
    except BaseException:
        traceback.print_exc()
    _exit()


if __name__ == "__main__":
    sys.exit(main())
