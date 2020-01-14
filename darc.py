# -*- coding: utf-8 -*-

import argparse
import contextlib
import dataclasses
import datetime
import getpass
import glob
import hashlib
import json
import math
import multiprocessing
import os
import pathlib
import platform
import posixpath
import queue
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import typing
import urllib.parse
import urllib.robotparser
import warnings

import bs4
import requests
import selenium.common.exceptions
import selenium.webdriver
import selenium.webdriver.common.proxy
import stem
import stem.control
import stem.process
import stem.util.term
import urllib3

###############################################################################
# typings

# argparse.ArgumentParser
ArgumentParser = typing.NewType('ArgumentParser', argparse.ArgumentParser)

Datetime = typing.NewType('Datetime', datetime.datetime)

# requests.Response
Response = typing.NewType('Response', requests.Response)

# requests.Session
Session = typing.NewType('Session', requests.Session)

# queue.Queue
Queue = typing.NewType('Queue', queue.Queue)

# subprocess.Popen
Popen = typing.NewType('Popen', subprocess.Popen)

# stem.control.Controller
Controller = typing.NewType('Controller', stem.control.Controller)

# stem.util.term.Color
Color = typing.NewType('Color', stem.util.term.Color)

# selenium.webdriver.Chrome
Driver = typing.NewType('Driver', selenium.webdriver.Chrome)

# selenium.webdriver.ChromeOptions
Options = typing.NewType('Options', selenium.webdriver.ChromeOptions)

# selenium.webdriver.DesiredCapabilities
DesiredCapabilities = typing.NewType('DesiredCapabilities', selenium.webdriver.DesiredCapabilities)

###############################################################################
# const

# reboot mode?
REBOOT = bool(int(os.getenv('DARC_REBOOT', '0')))

# debug mode?
DEBUG = bool(int(os.getenv('DARC_DEBUG', '0')))

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))
CWD = os.path.realpath(os.curdir)

# process number
DARC_CPU = os.getenv('DARC_CPU')
if DARC_CPU is not None:
    DARC_CPU = int(DARC_CPU)

# use multiprocessing?
FLAG_MP = bool(int(os.getenv('DARC_MULTIPROCESSING', '1')))
FLAG_TH = bool(int(os.getenv('DARC_MULTITHREADING', '0')))
if FLAG_MP and FLAG_TH:
    sys.exit('cannot enable multiprocessing and multithreading at the same time')

# data storage
PATH_DB = os.path.abspath(os.getenv('PATH_DATA', 'data'))
os.makedirs(PATH_DB, exist_ok=True)

# link file mapping
PATH_LN = os.path.join(PATH_DB, 'link.csv')
PATH_QR = os.path.join(PATH_DB, '_queue_requests.txt')
PATH_QS = os.path.join(PATH_DB, '_queue_selenium.txt')

# PID file
PATH_ID = os.path.join(PATH_DB, 'darc.pid')

# extract link pattern
LINK_EX = urllib.parse.unquote(os.getenv('LINK_EX', r'.*'))

# link black list
LINK_BL = [urllib.parse.unquote(link) for link in json.loads(os.getenv('LINK_BL', '[]'))]

# Tor Socks5 proxy & control port
TOR_PORT = os.getenv('TOR_PORT', '9050')
TOR_CTRL = os.getenv('TOR_CTRL', '9051')

# Tor authentication
TOR_PASS = os.getenv('TOR_PASS')

# use stem to manage Tor?
TOR_STEM = bool(int(os.getenv('TOR_STEM', '1')))

# Tor bootstrap retry
TOR_RETRY = int(os.getenv('TOR_RETRY', '3'))

# time delta for caches in seconds
_TIME_CACHE = float(os.getenv('TIME_CACHE', '60'))
if math.isfinite(_TIME_CACHE):
    TIME_CACHE = datetime.timedelta(seconds=_TIME_CACHE)
else:
    TIME_CACHE = None
del _TIME_CACHE

# selenium wait time
_SE_WAIT = float(os.getenv('SE_WAIT', '60'))
if math.isfinite(_SE_WAIT):
    SE_WAIT = _SE_WAIT
else:
    SE_WAIT = None
del _SE_WAIT

# selenium empty page
SE_EMPTY = '<html><head></head><body></body></html>'

# link queue
MANAGER = multiprocessing.Manager()
QUEUE_REQUESTS = MANAGER.Queue()  # url
QUEUE_SELENIUM = MANAGER.Queue()  # (ts, url)

###############################################################################
# error


class UnsupportedLink(Exception):
    """The link is not supported."""


class UnsupportedPlatform(Exception):
    """The platform is not supported."""


class TorBootstrapFailed(Warning):
    """Tor bootstrap process failed."""


def render_error(message: str, colour: Color) -> str:
    """Render error message."""
    return ''.join(
        stem.util.term.format(line, colour) for line in message.splitlines(True)
    )


###############################################################################
# save

# lock for file I/O
if FLAG_MP:
    _SAVE_LOCK = MANAGER.Lock()  # pylint: disable=no-member
elif FLAG_TH:
    _SAVE_LOCK = threading.Lock()
else:
    _SAVE_LOCK = contextlib.nullcontext()


@dataclasses.dataclass
class Link:
    """Parsed link."""

    # original link
    url: str

    # urllib.parse.urlparse
    url_parse: urllib.parse.ParseResult

    # hostname / netloc
    host: str
    # base folder
    base: str
    # hashed link
    name: str

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url


def parse_link(link: str) -> Link:
    """Parse link."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    # <scheme>/<host>/<hash>-<timestamp>.html
    base = os.path.join(PATH_DB, parse.scheme, host)
    name = hashlib.sha256(link.encode()).hexdigest()

    return Link(
        url=link,
        url_parse=parse,
        host=host,
        base=base,
        name=name,
    )


def has_robots(link: Link) -> typing.Optional[str]:
    """Check if robots.txt already exists."""
    # <scheme>/<host>/robots.txt
    path = os.path.join(link.base, 'robots.txt')
    return path if os.path.isfile(path) else None


def has_sitemap(link: Link) -> typing.Optional[str]:
    """Check if sitemap.xml already exists."""
    # <scheme>/<host>/sitemap_<hash>.xml
    name = hashlib.sha256(link.url.encode()).hexdigest()
    path = os.path.join(link.base, f'sitemap_{name}.xml')
    return path if os.path.isfile(path) else None


def has_folder(link: Link) -> typing.Optional[str]:
    """Check if folder created."""
    # <scheme>/<host>/
    return link.base if os.path.isdir(link.base) else None


def has_html(time: Datetime, link: Link) -> typing.Optional[str]:  # pylint: disable=redefined-outer-name
    """Check if we need to re-craw the link."""
    path = os.path.join(link.base, link.name)
    glob_list = list()
    for item in glob.glob(f'{path}_*.html'):
        temp = pathlib.Path(item)
        if temp.stem.endswith('_raw'):
            continue
        glob_list.append(temp)

    if not glob_list:
        return None

    # disable caching
    if TIME_CACHE is None:
        return glob_list[0]

    for item in glob_list:
        item_date = item.stem.split('_')[1]
        date = datetime.datetime.fromisoformat(item_date)
        if time - date <= TIME_CACHE:
            return item
    return None


def sanitise(link: Link, time: typing.Optional[Datetime] = None,  # pylint: disable=redefined-outer-name
             raw: bool = False, headers: bool = False) -> str:
    """Sanitise link to path."""
    os.makedirs(link.base, exist_ok=True)

    path = os.path.join(link.base, link.name)
    if time is None:
        time = datetime.datetime.now()
    ts = time.isoformat()

    if raw:
        return f'{path}_{ts}_raw.html'
    if headers:
        return f'{path}_{ts}.json'
    return f'{path}_{ts}.html'


def save_robots(link: Link, text: str) -> str:
    """Save `robots.txt`."""
    path = os.path.join(link.base, 'robots.txt')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'# {link.url}', file=file)
        file.write(text)
    return path


def save_sitemap(link: Link, text: str) -> str:
    """Save `sitemap.xml`."""
    # <scheme>/<host>/sitemap_<hash>.xml
    name = hashlib.sha256(link.url.encode()).hexdigest()
    path = os.path.join(link.base, f'sitemap_{name}.xml')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'<!-- {link.url} -->', file=file)
        file.write(text)
    return path


def save_headers(time: Datetime, link: Link, response: Response) -> str:  # pylint: disable=redefined-outer-name
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

    path = sanitise(link, time, headers=True)
    with open(path, 'w') as file:
        json.dump(data, file, indent=2)
    return path


def save_html(time: Datetime, link: Link, html: typing.Union[str, bytes], raw: bool = False) -> str:  # pylint: disable=redefined-outer-name
    """Save response."""
    # comment line
    comment = f'<!-- {link.url} -->'

    path = sanitise(link, time, raw=raw)
    if raw:
        with open(path, 'wb') as file:
            file.write(comment.encode())
            file.write(os.linesep.encode())
            file.write(html)
        return path

    with open(path, 'w') as file:
        print(comment, file=file)
        file.write(html)

    safe_link = link.url.replace('"', '\\"')
    safe_path = path.replace('"', '\\"')
    with _SAVE_LOCK:
        with open(PATH_LN, 'a') as file:
            print(f'"{safe_link}","{safe_path}"', file=file)
    return path


def save_file(link: Link, content: bytes) -> str:
    """Save file."""
    # remove leading slash '/'
    temp_path = link.url_parse.path[1:]

    # <scheme>/<host>/...
    root = posixpath.split(temp_path)
    path = os.path.join(link.base, *root[:-1])
    os.makedirs(path, exist_ok=True)

    os.chdir(path)
    with open(root[-1], 'wb') as file:
        file.write(content)
    os.chdir(CWD)

    return os.path.join(path, root[-1])


###############################################################################
# selenium


def get_options(type: str = 'norm') -> Options:  # pylint: disable=redefined-builtin
    """Generate options."""
    _system = platform.system()

    # initiate options
    options = selenium.webdriver.ChromeOptions()

    if _system == 'Darwin':
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

        if not DEBUG:
            options.add_argument('--headless')
    elif _system == 'Linux':
        options.binary_location = shutil.which('google-chrome')
        options.add_argument('--headless')

        # c.f. https://crbug.com/638180; https://stackoverflow.com/a/50642913/7218152
        if getpass.getuser() == 'root':
            options.add_argument('--no-sandbox')

        # c.f. http://crbug.com/715363
        options.add_argument('--disable-dev-shm-usage')
    else:
        raise UnsupportedPlatform(f'unsupported system: {_system}')

    if type == 'tor':
        # c.f. https://www.chromium.org/developers/design-documents/network-stack/socks-proxy
        options.add_argument(f'--proxy-server=socks5://localhost:{TOR_PORT}')
        options.add_argument('--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE localhost"')
    return options


def get_capabilities(type: str = 'norm') -> dict:  # pylint: disable=redefined-builtin
    """Generate desied capabilities."""
    # do not modify source dict
    capabilities = selenium.webdriver.DesiredCapabilities.CHROME.copy()

    if type == 'tor':
        proxy = selenium.webdriver.Proxy()
        proxy.proxyType = selenium.webdriver.common.proxy.ProxyType.MANUAL
        proxy.http_proxy = f'socks5://localhost:{TOR_PORT}'
        proxy.ssl_proxy = f'socks5://localhost:{TOR_PORT}'
        proxy.add_to_capabilities(capabilities)
    return capabilities


def tor_driver() -> Driver:
    """Tor (.onion) driver."""
    options = get_options('tor')
    capabilities = get_capabilities('tor')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver


def norm_driver() -> Driver:
    """Normal driver."""
    options = get_options('norm')
    capabilities = get_capabilities('norm')

    # initiate driver
    driver = selenium.webdriver.Chrome(options=options,
                                       desired_capabilities=capabilities)
    return driver


###############################################################################
# requests

# Tor bootstrapped flag
_TOR_BS_FLAG = not TOR_STEM  # only if Tor managed through stem
# Tor controller
_TOR_CTRL = None
# Tor daemon process
_TOR_PROC = None


def renew_tor_session():
    """Renew Tor session."""
    if _TOR_CTRL is None:
        return
    _TOR_CTRL.signal(stem.Signal.NEWNYM)  # pylint: disable=no-member


def print_bootstrap_lines(line: str):
    """Print Tor bootstrap lines."""
    if DEBUG:
        print(stem.util.term.format(line, stem.util.term.Color.BLUE))  # pylint: disable=no-member
        return

    if 'Bootstrapped ' in line:
        print(stem.util.term.format(line, stem.util.term.Color.BLUE))  # pylint: disable=no-member


def _tor_bootstrap():
    """Tor bootstrap."""
    global _TOR_BS_FLAG, _TOR_CTRL, _TOR_PROC, TOR_PASS

    # launch Tor process
    _TOR_PROC = stem.process.launch_tor_with_config(
        config={
            'SocksPort': TOR_PORT,
            'ControlPort': TOR_CTRL,
        },
        take_ownership=True,
        init_msg_handler=print_bootstrap_lines,
    )

    if TOR_PASS is None:
        TOR_PASS = getpass.getpass('Tor authentication: ')

    # Tor controller process
    _TOR_CTRL = stem.control.Controller.from_port(port=int(TOR_CTRL))
    _TOR_CTRL.authenticate(TOR_PASS)

    # update flag
    #_TOR_BS_FLAG.value = True
    _TOR_BS_FLAG = True


def tor_bootstrap():
    """Bootstrap wrapper for Tor."""
    # don't re-bootstrap
    #if _TOR_BS_FLAG.value:
    if _TOR_BS_FLAG:
        return

    # with _TOR_BS_LOCK:
    for _ in range(TOR_RETRY+1):
        try:
            _tor_bootstrap()
            break
        except Exception as error:
            warning = warnings.formatwarning(error, TorBootstrapFailed, __file__, 514, 'tor_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member


def has_tor(link_pool: typing.Set[str]) -> bool:
    """Check if contain Tor links."""
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = urllib.parse.urlparse(link)
        host = parse.hostname or parse.netloc

        if re.match(r'.*?\.onion', host):
            return True
    return False


def tor_session() -> Session:
    """Tor (.onion) session."""
    session = requests.Session()
    session.proxies.update({
        # c.f. https://stackoverflow.com/a/42972942
        'http':  f'socks5h://localhost:{TOR_PORT}',
        'https': f'socks5h://localhost:{TOR_PORT}'
    })
    return session


def norm_session() -> Session:
    """Normal session"""
    return requests.Session()


###############################################################################
# parse


def _match(link: str) -> bool:
    """Check if link in black list."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    host = parse.hostname or parse.netloc

    if re.match(LINK_EX, host) is None:
        return True

    for pattern in LINK_BL:
        if re.match(pattern, host) is not None:
            return True
    return False


def get_sitemap(link: str, text: str) -> typing.List[Link]:
    """Fetch link to sitemap."""
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())

    sitemaps = rp.site_maps()
    if sitemaps is None:
        return [parse_link(urllib.parse.urljoin(link, '/sitemap.xml'))]
    return [parse_link(urllib.parse.urljoin(link, sitemap)) for sitemap in sitemaps]


def read_sitemap(link: str, text: str) -> typing.Iterator[str]:
    """Read sitemap."""
    link_list = list()
    soup = bs4.BeautifulSoup(text, 'html5lib')
    for loc in soup.find_all('loc'):
        temp_link = urllib.parse.urljoin(link, loc.text)
        if _match(temp_link):
            continue
        link_list.append(temp_link)
    yield from set(link_list)


def extract_links(link: str, html: typing.Union[str, bytes]) -> typing.Iterator[str]:
    """Extract links from HTML context."""
    soup = bs4.BeautifulSoup(html, 'html5lib')

    link_list = []
    for child in filter(lambda element: isinstance(element, bs4.element.Tag),
                        soup.descendants):
        href = child.get('href')
        if href is None:
            continue
        temp_link = urllib.parse.urljoin(link, href)
        if _match(temp_link):
            continue
        link_list.append(temp_link)
    yield from set(link_list)


###############################################################################
# process

# link regex mapping
LINK_MAP = [
    (r'.*?\.onion', tor_session, tor_driver),
    (r'.*', norm_session, norm_driver),
]


def request_session(link: Link) -> Session:
    """Get requests session."""
    for regex, session, _ in LINK_MAP:
        if re.match(regex, link.host):
            return session()
    raise UnsupportedLink(link)


def request_driver(link: Link) -> Driver:
    """Get selenium driver."""
    for regex, _, driver in LINK_MAP:
        if re.match(regex, link.host):
            return driver()
    raise UnsupportedLink(link)


def fetch_sitemap(link: Link):
    """Fetch sitemap."""
    robots_path = has_robots(link)
    if robots_path is not None:

        with open(robots_path) as file:
            robots_text = file.read()

    else:

        robots_link = parse_link(urllib.parse.urljoin(link.url, '/robots.txt'))
        with request_session(robots_link) as session:
            try:
                response = session.get(robots_link.url)
            except requests.RequestException as error:
                print(render_error(f'Failed on {robots_link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                return

        if response.ok:
            save_robots(robots_link, response.text)
            robots_text = response.text
        else:
            print(render_error(f'Failed on {robots_link.url} [{response.status_code}]',
                               stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
            robots_text = ''

    sitemaps = get_sitemap(link.url, robots_text)
    for sitemap_link in sitemaps:
        sitemap_path = has_sitemap(sitemap_link)
        if sitemap_path is not None:

            with open(sitemap_path) as file:
                sitemap_text = file.read()

        else:

            with request_session(sitemap_link) as session:
                try:
                    response = session.get(sitemap_link.url)
                except requests.RequestException as error:
                    print(render_error(f'Failed on {sitemap_link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    continue

            if not response.ok:
                print(render_error(f'Failed on {sitemap_link.url} [{response.status_code}]',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                continue

            sitemap_text = response.text
            save_sitemap(sitemap_link, sitemap_text)

        # add link to queue
        [QUEUE_REQUESTS.put(url) for url in read_sitemap(link.url, sitemap_text)]  # pylint: disable=expression-not-assigned


def loader(entry: typing.Tuple[Datetime, str]):
    """Single loader for a entry link."""
    timestamp, url = entry
    link = parse_link(url)

    try:
        print(f'Loading {link.url}')

        # retrieve source from Chrome
        with request_driver(link) as driver:
            # wait for page to finish loading
            #driver.implicitly_wait(SE_WAIT)

            try:
                driver.get(link.url)
            except urllib3.exceptions.HTTPError as error:
                print(render_error(f'Fail to load {link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                QUEUE_SELENIUM.put((timestamp, link.url))
                return
            except selenium.common.exceptions.WebDriverException as error:
                print(render_error(f'Fail to load {link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                QUEUE_SELENIUM.put((timestamp, link.url))
                return

            # wait for page to finish loading
            if SE_WAIT is not None:
                time.sleep(SE_WAIT)

            # get HTML source
            html = driver.page_source

            if html == SE_EMPTY:
                print(render_error(f'Empty page from {link.url}',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                QUEUE_SELENIUM.put((timestamp, link.url))
                return

        # save HTML
        save_html(timestamp, link, html)

        # add link to queue
        [QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned

        print(f'Loaded {link.url}')
    except Exception:
        error = f'[Error from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
        QUEUE_SELENIUM.put(link.url)


def crawler(url: str):
    """Single crawler for a entry link."""
    link = parse_link(url)
    try:
        # timestamp
        timestamp = datetime.datetime.now()

        path = has_html(timestamp, link)
        if path is not None:

            print(stem.util.term.format(f'Cached {link.url}', stem.util.term.Color.YELLOW))  # pylint: disable=no-member
            with open(path, 'rb') as file:
                html = file.read()

            # add link to queue
            [QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned

            # load sitemap.xml
            try:
                fetch_sitemap(link)
            except Exception:
                error = f'[Error loading sitemap of {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member

        else:

            # if it's a new host
            new_host = has_folder(link) is None

            print(f'Requesting {link.url}')

            with request_session(link) as session:
                try:
                    response = session.get(link.url)
                except requests.exceptions.InvalidSchema as error:
                    print(render_error(f'Failed on {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    return
                except requests.RequestException as error:
                    print(render_error(f'Failed on {link.url} <{error}>',
                                       stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                    QUEUE_REQUESTS.put(link.url)
                    return

            # fetch sitemap.xml
            if new_host:
                try:
                    fetch_sitemap(link)
                except Exception:
                    error = f'[Error fetching sitemap of {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
                    print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member

            # check content type
            ct_type = response.headers.get('Content-Type', 'undefined').casefold()
            if 'html' not in ct_type:
                # text = response.content
                # save_file(link, text)
                print(render_error(f'Unexpected content type from {link.url} ({ct_type})',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                return

            # save headers
            save_headers(timestamp, link, response)

            html = response.content
            if not html:
                print(render_error(f'Empty response from {link.url}',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                QUEUE_REQUESTS.put((timestamp, link.url))
                return

            # save HTML
            save_html(timestamp, link, html, raw=True)

            # add link to queue
            [QUEUE_REQUESTS.put(href) for href in extract_links(link.url, html)]  # pylint: disable=expression-not-assigned

            if not response.ok:
                print(render_error(f'Failed on {link.url} [{response.status_code}]',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                QUEUE_REQUESTS.put(link.url)
                return

            # add link to queue
            QUEUE_SELENIUM.put((timestamp, link.url))

            print(f'Requested {link.url}')
    except Exception:
        error = f'[Error from {link.url}]' + os.linesep + traceback.format_exc() + '-' * shutil.get_terminal_size().columns  # pylint: disable=line-too-long
        print(render_error(error, stem.util.term.Color.CYAN), file=sys.stderr)  # pylint: disable=no-member
        QUEUE_REQUESTS.put(link.url)


def _load_last_word():
    """Load data to queue."""
    with open(PATH_ID, 'w') as file:
        print(os.getpid(), file=file)

    if os.path.isfile(PATH_QR):
        with open(PATH_QR) as file:
            for line in file:
                QUEUE_REQUESTS.put(line.strip())
        os.remove(PATH_QR)

    if os.path.isfile(PATH_QS):
        with open(PATH_QS) as file:
            for line in file:
                timestamp, link = line.strip().split(maxsplit=1)
                QUEUE_SELENIUM.put((datetime.datetime.fromisoformat(timestamp), link))
        os.remove(PATH_QS)


def _dump_last_word():
    """Dump data in queue."""
    with open(PATH_QR, 'w') as file:
        for link in _get_requests_links():
            print(link, file=file)

    with open(PATH_QS, 'w') as file:
        for timestamp, link in _get_selenium_links():
            print(f'{timestamp.isoformat()} {link}', file=file)

    if os.path.isfile(PATH_ID):
        os.remove(PATH_ID)


def _get_selenium_links() -> typing.Optional[typing.Set[typing.Tuple[Datetime, str]]]:
    """Fetch links from queue."""
    link_list = list()
    while True:
        try:
            link = QUEUE_SELENIUM.get_nowait()
        except queue.Empty:
            break
        link_list.append(link)

    if link_list:
        random.shuffle(link_list)
    return set(link_list)


def _get_requests_links() -> typing.Optional[typing.Set[str]]:
    """Fetch links from queue."""
    link_list = list()
    while True:
        try:
            link = QUEUE_REQUESTS.get_nowait()
        except queue.Empty:
            break
        link_list.append(link)

    if link_list:
        random.shuffle(link_list)

    link_pool = set(link_list)
    if not _TOR_BS_FLAG and has_tor(link_pool):
        tor_bootstrap()
    return link_pool


def process():
    """Main process."""
    try:
        # load remaining links
        _load_last_word()

        # start mainloop
        with multiprocessing.Pool(processes=DARC_CPU) as pool:
            while True:
                # requests crawler
                link_pool = _get_requests_links()
                if link_pool:
                    pool.map(crawler, link_pool)
                else:
                    break

                # selenium loader
                item_pool = _get_selenium_links()
                if item_pool:
                    if FLAG_MP:
                        pool.map(loader, item_pool)
                    elif FLAG_TH and DARC_CPU:
                        thread_list = list()
                        for _ in range(DARC_CPU):
                            try:
                                item = item_pool.pop()
                            except KeyError:
                                break
                            thread = threading.Thread(target=loader, args=(item,))
                            thread_list.append(thread)
                            thread.start()
                        for thread in thread_list:
                            thread.join()
                    else:
                        [loader(item) for item in item_pool]  # pylint: disable=expression-not-assigned
                else:
                    break

                # quit in reboot mode
                if REBOOT:
                    _dump_last_word()
                    break

                # renew Tor session
                renew_tor_session()
                print(stem.util.term.format('Starting next round...', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    except BaseException:
        print(stem.util.term.format('Keeping last words...', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
        _dump_last_word()
        raise
    print(stem.util.term.format('Gracefully existing...', stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


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
    caller(MANAGER, 'shutdown')

    # close Tor processes
    caller(_TOR_CTRL, 'close')
    caller(_TOR_PROC, 'terminate')


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
        QUEUE_REQUESTS.put(link)

    if args.file is not None:
        with open(args.file) as file:
            for line in file:
                QUEUE_REQUESTS.put(line.strip())

    try:
        process()
    except BaseException:
        traceback.print_exc()
    _exit()


if __name__ == "__main__":
    sys.exit(main())
