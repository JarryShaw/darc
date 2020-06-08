# -*- coding: utf-8 -*-
"""I2P Proxy
===============

The :mod:`darc.proxy.i2p` module contains the auxiliary functions
around managing and processing the I2P proxy.

"""

import base64
import getpass
import io
import os
import platform
import pprint
import re
import shlex
import shutil
import subprocess
import sys
import traceback
import warnings

import requests
import selenium.webdriver
import selenium.webdriver.common.proxy
import stem.util.term

import darc.typing as typing
from darc.const import CHECK, DARC_USER, DEBUG, PATH_DB, VERBOSE
from darc.error import I2PBootstrapFailed, UnsupportedPlatform, render_error
from darc.link import Link, parse_link, urljoin
from darc.parse import _check, get_content_type

# I2P args
I2P_ARGS = shlex.split(os.getenv('I2P_ARGS', ''))

# bootstrap wait
BS_WAIT = float(os.getenv('I2P_WAIT', '90'))

# I2P port
I2P_PORT = os.getenv('I2P_PORT', '4444')

# I2P bootstrap retry
I2P_RETRY = int(os.getenv('I2P_RETRY', '3'))

# proxy
I2P_REQUESTS_PROXY = {
    # c.f. https://stackoverflow.com/a/42972942
    'http':  f'http://localhost:{I2P_PORT}',
    'https': f'http://localhost:{I2P_PORT}',
}
I2P_SELENIUM_PROXY = selenium.webdriver.Proxy()
I2P_SELENIUM_PROXY.proxyType = selenium.webdriver.common.proxy.ProxyType.MANUAL
I2P_SELENIUM_PROXY.http_proxy = f'http://localhost:{I2P_PORT}'
I2P_SELENIUM_PROXY.ssl_proxy = f'http://localhost:{I2P_PORT}'

# I2P bootstrapped flag
_I2P_BS_FLAG = False
# I2P daemon process
_I2P_PROC = None
# I2P bootstrap args
_unsupported = False
if getpass.getuser() == 'root':
    _system = platform.system()
    if _system in ['Linux', 'Darwin']:
        _I2P_ARGS = ['su', '-', DARC_USER, 'i2prouter', 'start']
    else:
        _unsupported = True
        _I2P_ARGS = list()
else:
    _I2P_ARGS = ['i2prouter', 'start']
_I2P_ARGS.extend(I2P_ARGS)

if DEBUG:
    print(stem.util.term.format('-*- I2P PROXY -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    if _unsupported:
        print(stem.util.term.format(f'unsupported system: {platform.system()}',
                                    stem.util.term.Color.RED))  # pylint: disable=no-member
    else:
        print(render_error(pprint.pformat(_I2P_ARGS), stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member

# I2P link regular expression
I2P_REGEX = re.compile(r'.*\.i2p', re.IGNORECASE)


def _i2p_bootstrap():
    """I2P bootstrap.

    The bootstrap arguments are defined as :data:`~darc.proxy.i2p._I2P_ARGS`.

    Raises:
        subprocess.CalledProcessError: If the return code of :data:`~darc.proxy.i2p._I2P_PROC` is non-zero.

    See Also:
        * :func:`darc.proxy.i2p.i2p_bootstrap`
        * :data:`darc.proxy.i2p.BS_WAIT`
        * :data:`darc.proxy.i2p._I2P_BS_FLAG`
        * :data:`darc.proxy.i2p._I2P_PROC`

    """
    global _I2P_BS_FLAG, _I2P_PROC

    # launch I2P process
    _I2P_PROC = subprocess.Popen(
        _I2P_ARGS, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    try:
        stdout, stderr = _I2P_PROC.communicate(timeout=BS_WAIT)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout, error.stderr
    if VERBOSE:
        if stdout is not None:
            print(render_error(stdout, stem.util.term.Color.BLUE))  # pylint: disable=no-member
    if stderr is not None:
        print(render_error(stderr, stem.util.term.Color.RED))  # pylint: disable=no-member

    returncode = _I2P_PROC.returncode
    if returncode is not None and returncode != 0:
        raise subprocess.CalledProcessError(returncode, _I2P_ARGS,
                                            _I2P_PROC.stdout,
                                            _I2P_PROC.stderr)

    # update flag
    _I2P_BS_FLAG = True


def i2p_bootstrap():
    """Bootstrap wrapper for I2P.

    The function will bootstrap the I2P proxy. It will retry for
    :data:`~darc.proxy.i2p.I2P_RETRY` times in case of failure.

    Also, it will **NOT** re-bootstrap the proxy as is guaranteed by
    :data:`~darc.proxy.i2p._I2P_BS_FLAG`.

    Warns:
        I2PBootstrapFailed: If failed to bootstrap I2P proxy.

    Raises:
        :exc:`UnsupportedPlatform`: If the system is not supported, i.e. not macOS or Linux.

    See Also:
        * :func:`darc.proxy.i2p._i2p_bootstrap`
        * :data:`darc.proxy.i2p.I2P_RETRY`
        * :data:`darc.proxy.i2p._I2P_BS_FLAG`

    """
    if _unsupported:
        raise UnsupportedPlatform(f'unsupported system: {platform.system()}')

    # don't re-bootstrap
    if _I2P_BS_FLAG:
        return

    print(stem.util.term.format('-*- I2P Bootstrap -*-',
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member
    for _ in range(I2P_RETRY+1):
        try:
            _i2p_bootstrap()
            break
        except Exception as error:
            if DEBUG:
                message = '[Error bootstraping I2P proxy]' + os.linesep + traceback.format_exc()
                print(render_error(message, stem.util.term.Color.RED), end='', file=sys.stderr)  # pylint: disable=no-member

            warning = warnings.formatwarning(error, I2PBootstrapFailed, __file__, 125, 'i2p_bootstrap()')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member
    print(stem.util.term.format('-' * shutil.get_terminal_size().columns,
                                stem.util.term.Color.MAGENTA))  # pylint: disable=no-member


def get_hosts(link: Link) -> typing.Optional[typing.Dict[str, typing.Union[str, typing.ByteString]]]:  # pylint: disable=inconsistent-return-statements
    """Read ``hosts.txt``.

    Args:
        link: Link object to read ``hosts.txt``.

    Returns:
        * If ``hosts.txt`` exists, return the data from ``hosts.txt``.

          * ``path`` -- relative path from ``hosts.txt`` to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/hosts.txt``
          * ``data`` -- *base64* encoded content of ``hosts.txt``

        * If not, return ``None``.

    See Also:
        * :func:`darc.submit.submit_new_host`
        * :func:`darc.proxy.i2p.save_hosts`

    """
    path = os.path.join(link.base, 'hosts.txt')
    if not os.path.isfile(path):
        return
    with open(path, 'rb') as file:
        content = file.read()
    data = dict(
        path=os.path.relpath(path, PATH_DB),
        data=base64.b64encode(content).decode(),
    )
    return data


def has_i2p(link_pool: typing.Set[Link]) -> bool:
    """Check if contain I2P links.

    Args:
        link_pool: Link pool to check.

    Returns:
        If the link pool contains I2P links.

    See Also:
        * :func:`darc.link.parse_link`
        * :func:`darc.link.urlparse`

    """
    for link in link_pool:
        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        parse = link.url_parse

        if re.fullmatch(r'.*?\.i2p', parse.netloc):
            return True
        # c.f. https://geti2p.net/en/docs/api/i2ptunnel
        if parse.netloc in ['127.0.0.1:7657', '127.0.0.1:7658',
                            'localhost:7657', 'localhost:7658']:
            return True
    return False


def has_hosts(link: Link) -> typing.Optional[str]:
    """Check if ``hosts.txt`` already exists.

    Args:
        link: Link object to check if ``hosts.txt`` already exists.

    Returns:
        * If ``hosts.txt`` exists, return the path to ``hosts.txt``,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/hosts.txt``.
        * If not, return ``None``.

    """
    # <proxy>/<scheme>/<host>/hosts.txt
    path = os.path.join(link.base, 'hosts.txt')
    return path if os.path.isfile(path) else None


def save_hosts(link: Link, text: str) -> str:
    """Save ``hosts.txt``.

    Args:
        link: Link object of ``hosts.txt``.
        text: Content of ``hosts.txt``.

    Returns:
        Saved path to ``hosts.txt``, i.e.
        ``<root>/<proxy>/<scheme>/<hostname>/hosts.txt``.

    See Also:
        * :func:`darc.save.sanitise`

    """
    path = os.path.join(link.base, 'hosts.txt')

    root = os.path.split(path)[0]
    os.makedirs(root, exist_ok=True)

    with open(path, 'w') as file:
        print(f'# {link.url}', file=file)
        file.write(text)
    return path


def read_hosts(text: typing.Iterable[str], check: bool = CHECK) -> typing.Iterable[Link]:
    """Read ``hosts.txt``.

    Args:
        text: Content of ``hosts.txt``.
        check: If perform checks on extracted links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of links extracted.

    """
    temp_list = list()
    for line in filter(None, map(lambda s: s.strip(), text)):
        if line.startswith('#'):
            continue

        link = line.split('=', maxsplit=1)[0]
        if I2P_REGEX.fullmatch(link) is None:
            continue
        temp_list.append(parse_link(f'http://{link}'))

    if check:
        link_list = _check(temp_list)
    else:
        link_list = temp_list.copy()
    yield from set(link_list)


def fetch_hosts(link: Link):
    """Fetch ``hosts.txt``.

    Args:
        link: Link object to fetch for its ``hosts.txt``.

    """
    hosts_path = has_hosts(link)
    if hosts_path is not None:

        print(stem.util.term.format(f'[HOSTS] Cached {link.url}',
                                    stem.util.term.Color.YELLOW))  # pylint: disable=no-member
        hosts_file = open(hosts_path)

    else:

        from darc.requests import i2p_session  # pylint: disable=import-outside-toplevel

        hosts_link = parse_link(urljoin(link.url, '/hosts.txt'))
        print(f'[HOSTS] Subscribing {hosts_link.url}')

        with i2p_session() as session:
            try:
                response = session.get(hosts_link.url)
            except requests.RequestException as error:
                print(render_error(f'[HOSTS] Failed on {hosts_link.url} <{error}>',
                                   stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
                return

        if not response.ok:
            print(render_error(f'[HOSTS] Failed on {hosts_link.url} [{response.status_code}]',
                               stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
            return

        ct_type = get_content_type(response)
        if ct_type not in ['text/text', 'text/plain']:
            print(render_error(f'[HOSTS] Unresolved content type on {hosts_link.url} ({ct_type}',
                               stem.util.term.Color.RED), file=sys.stderr)  # pylint: disable=no-member
            return

        save_hosts(hosts_link, response.text)
        hosts_file = io.StringIO(response.text)

        print(f'[HOSTS] Subscribed {hosts_link.url}')

    from darc.db import save_requests  # pylint: disable=import-outside-toplevel

    # add link to queue
    #[QUEUE_REQUESTS.put(url) for url in read_hosts(hosts_file)]  # pylint: disable=expression-not-assigned
    save_requests(read_hosts(hosts_file))
