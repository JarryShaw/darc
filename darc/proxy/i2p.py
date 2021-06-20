# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""I2P Proxy
===============

The :mod:`darc.proxy.i2p` module contains the auxiliary functions
around managing and processing the I2P proxy.

"""

import base64
import getpass
import os
import platform
import re
import shlex
import signal
import subprocess  # nosec: B404
from typing import TYPE_CHECKING, cast

import requests
import selenium.webdriver.common.proxy as selenium_proxy

from darc.const import CHECK, DARC_USER, DEBUG, PATH_DB
from darc.error import I2PBootstrapFailed, UnsupportedPlatform
from darc.link import parse_link, urljoin
from darc.logging import DEBUG as LOG_DEBUG
from darc.logging import ERROR as LOG_ERROR
from darc.logging import INFO as LOG_INFO
from darc.logging import VERBOSE as LOG_VERBOSE
from darc.logging import WARNING as LOG_WARNING
from darc.logging import logger
from darc.parse import _check, get_content_type

if TYPE_CHECKING:
    from io import IO  # type: ignore[attr-defined] # pylint: disable=no-name-in-module
    from signal import Signals  # pylint: disable=no-name-in-module
    from subprocess import Popen  # nosec: B404
    from types import FrameType
    from typing import List, NoReturn, Optional, Union

    import darc.link as darc_link  # Link
    from darc._typing import File

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
I2P_SELENIUM_PROXY = selenium_proxy.Proxy()
I2P_SELENIUM_PROXY.proxyType = selenium_proxy.ProxyType.MANUAL
I2P_SELENIUM_PROXY.http_proxy = f'http://localhost:{I2P_PORT}'
I2P_SELENIUM_PROXY.ssl_proxy = f'http://localhost:{I2P_PORT}'

# manage I2P through darc?
_MNG_I2P = bool(int(os.getenv('DARC_I2P', '1')))

# I2P bootstrapped flag
_I2P_BS_FLAG = not _MNG_I2P
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
        _I2P_ARGS = []
else:
    _I2P_ARGS = ['i2prouter', 'start']
_I2P_ARGS.extend(I2P_ARGS)

if _unsupported:
    if DEBUG:
        logger.debug('-*- FREENET PROXY -*-')
        logger.pline(LOG_ERROR, 'unsupported system: %s', platform.system())
        logger.pline(LOG_DEBUG, logger.horizon)
else:
    logger.plog(LOG_DEBUG, '-*- FREENET PROXY -*-', object=_I2P_ARGS)


# I2P link regular expression
I2P_REGEX = re.compile(r'.*\.i2p', re.IGNORECASE)


def launch_i2p() -> 'Popen[bytes]':
    """Launch I2P process.

    See Also:
        This function mocks the behaviour of :func:`stem.process.launch_tor`.

    """
    i2p_process = None
    try:
        i2p_process = subprocess.Popen(  # pylint: disable=consider-using-with # nosec
            _I2P_ARGS, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )

        def timeout_handlet(signum: 'Optional[Union[int, Signals]]' = None,
                            frame: 'Optional[FrameType]' = None) -> 'NoReturn':
            raise OSError('reached a %i second timeout without success' % BS_WAIT)

        signal.signal(signal.SIGALRM, timeout_handlet)
        signal.setitimer(signal.ITIMER_REAL, BS_WAIT)

        while True:
            init_line = cast(
                'IO[bytes]', i2p_process.stdout
            ).readline().decode('utf-8', 'replace').strip()
            logger.pline(LOG_VERBOSE, init_line)

            if not init_line:
                raise OSError('Process terminated: Timed out')

            if 'running: PID:' in init_line:
                return i2p_process
            if 'I2P Service is already running.' in init_line:
                return i2p_process
    except BaseException:
        if i2p_process is not None:
            i2p_process.kill()  # don't leave a lingering process
            i2p_process.wait()
        raise
    finally:
        signal.alarm(0)  # stop alarm


def _i2p_bootstrap() -> None:
    """I2P bootstrap.

    The bootstrap arguments are defined as :data:`~darc.proxy.i2p._I2P_ARGS`.

    Raises:
        subprocess.CalledProcessError: If the return code of :data:`~darc.proxy.i2p._I2P_PROC` is non-zero.

    See Also:
        * :func:`darc.proxy.i2p.i2p_bootstrap`
        * :func:`darc.proxy.i2p.launch_i2p`
        * :data:`darc.proxy.i2p.BS_WAIT`
        * :data:`darc.proxy.i2p._I2P_BS_FLAG`
        * :data:`darc.proxy.i2p._I2P_PROC`

    """
    global _I2P_BS_FLAG, _I2P_PROC  # pylint: disable=global-statement

    # launch I2P process
    _I2P_PROC = launch_i2p()

    # update flag
    _I2P_BS_FLAG = True


def i2p_bootstrap() -> None:
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

    logger.info('-*- I2P Bootstrap -*-')
    for _ in range(I2P_RETRY+1):
        try:
            _i2p_bootstrap()
            break
        except Exception:
            if DEBUG:
                logger.ptb('[Error bootstraping I2P proxy]')
            logger.pexc(LOG_WARNING, category=I2PBootstrapFailed, line='i2p_bootstrap()')
    logger.pline(LOG_INFO, logger.horizon)


def get_hosts(link: 'darc_link.Link') -> 'Optional[File]':
    """Read ``hosts.txt``.

    Args:
        link: Link object to read ``hosts.txt``.

    Returns:
        * If ``hosts.txt`` exists, return the data from ``hosts.txt``.

          * ``path`` -- relative path from ``hosts.txt`` to root of data storage
            :data:`~darc.const.PATH_DB`, ``<proxy>/<scheme>/<hostname>/hosts.txt``
          * ``data`` -- *base64* encoded content of ``hosts.txt``

        * If not, return :data:`None`.

    See Also:
        * :func:`darc.submit.submit_new_host`
        * :func:`darc.proxy.i2p.save_hosts`

    """
    path = os.path.join(link.base, 'hosts.txt')
    if not os.path.isfile(path):
        return None
    with open(path, 'rb') as file:
        content = file.read()
    return {
        'path': os.path.relpath(path, PATH_DB),
        'data': base64.b64encode(content).decode(),
    }


def have_hosts(link: 'darc_link.Link') -> 'Optional[str]':
    """Check if ``hosts.txt`` already exists.

    Args:
        link: Link object to check if ``hosts.txt`` already exists.

    Returns:
        * If ``hosts.txt`` exists, return the path to ``hosts.txt``,
          i.e. ``<root>/<proxy>/<scheme>/<hostname>/hosts.txt``.
        * If not, return :data:`None`.

    """
    # <proxy>/<scheme>/<host>/hosts.txt
    path = os.path.join(link.base, 'hosts.txt')
    return path if os.path.isfile(path) else None


def save_hosts(link: 'darc_link.Link', text: str) -> str:
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


def read_hosts(link: 'darc_link.Link', text: str, check: bool = CHECK) -> 'List[darc_link.Link]':
    """Read ``hosts.txt``.

    Args:
        link: Link object to fetch for its ``hosts.txt``.
        text: Content of ``hosts.txt``.
        check: If perform checks on extracted links,
            default to :data:`~darc.const.CHECK`.

    Returns:
        List of links extracted.

    """
    temp_list = []
    for line in filter(None, map(lambda s: s.strip(), text.splitlines())):
        if line.startswith('#'):
            continue

        host = line.split('=', maxsplit=1)[0]
        if I2P_REGEX.fullmatch(host) is None:
            continue
        temp_list.append(parse_link(f'http://{host}', backref=link))

    if check:
        return _check(temp_list)
    return temp_list


def fetch_hosts(link: 'darc_link.Link', force: bool = False) -> None:
    """Fetch ``hosts.txt``.

    Args:
        link: Link object to fetch for its ``hosts.txt``.
        force: Force refetch ``hosts.txt``.

    Returns:
        Content of the ``hosts.txt`` file.

    """
    if force:
        logger.warning('[HOSTS] Force refetch %s', link.url)

    hosts_path = None if force else have_hosts(link)
    if hosts_path is not None:

        logger.warning('[HOSTS] Cached %s', link.url)  # pylint: disable=no-member
        with open(hosts_path) as hosts_file:
            hosts_text = hosts_file.read()

    else:

        from darc.requests import i2p_session  # pylint: disable=import-outside-toplevel

        hosts_link = parse_link(urljoin(link.url, '/hosts.txt'), backref=link)
        logger.info('[HOSTS] Subscribing %s', hosts_link.url)

        with i2p_session() as session:
            try:
                response = session.get(hosts_link.url)
            except requests.RequestException:
                logger.pexc(message=f'[HOSTS] Failed on {hosts_link.url}')
                return

        if not response.ok:
            logger.error('[HOSTS] Failed on %s [%d]', hosts_link.url, response.status_code)
            return

        ct_type = get_content_type(response)
        if ct_type not in ['text/text', 'text/plain']:
            logger.error('[HOSTS] Unresolved content type on %s (%s)', hosts_link.url, ct_type)
            return

        hosts_text = response.text
        save_hosts(hosts_link, hosts_text)

        logger.info('[HOSTS] Subscribed %s', hosts_link.url)

    from darc.db import save_requests  # pylint: disable=import-outside-toplevel

    # add link to queue
    save_requests(read_hosts(link, hosts_text))
