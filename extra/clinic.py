# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports
"""Redis clinic for releasing memory."""

import argparse
import contextlib
import datetime
import math
import os
import shutil
import subprocess  # nosec
import sys
import textwrap
import time
import warnings
from typing import TYPE_CHECKING

import redis
import stem.util.term

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from typing import Any, AnyStr

    from stem.util.term import Color

# Redis client
REDIS: redis.Redis = None  # type: ignore[assignment]
# script object
SCPT: redis.client.Script = None  # type: ignore[assignment]

# Redis retry interval
RETRY_INTERVAL = float(os.getenv('DARC_RETRY', '10'))
if not math.isfinite(RETRY_INTERVAL):
    RETRY_INTERVAL = None  # type: ignore

# max pool
#MAX_POOL = float(os.getenv('DARC_MAX_POOL', '500'))
#if math.isfinite(MAX_POOL):
#    MAX_POOL = math.floor(MAX_POOL)

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))
# script path
SCPT_PATH = os.path.join(ROOT, 'clinic.lua')
with open(SCPT_PATH) as scpt_file:
    SCPT_TEXT = scpt_file.read()
# link path
POOL_PATH = os.path.join(ROOT, '..', 'text', 'clinic.txt')


class RedisCommandFailed(Warning):
    """Redis command execution failed."""


def render_error(message: 'AnyStr', colour: 'Color') -> str:
    """Render error message.

    The function wraps the :func:`stem.util.term.format` function to
    provide multi-line formatting support.

    Args:
        message: Multi-line message to be rendered with ``colour``.
        colour (stem.util.term.Color): Front colour of text, c.f.
            :class:`stem.util.term.Color`.

    Returns:
        The rendered error message.

    """
    return ''.join(
        stem.util.term.format(line, colour) for line in message.splitlines(True)
    )


def _gen_arg_msg(*args: 'Any', **kwargs: 'Any') -> str:
    """Sanitise arguments representation string.

    Args:
        *args: Arbitrary arguments.

    Keyword Args:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        Sanitised arguments representation string.

    """
    _args = ', '.join(map(repr, args))
    _kwargs = ', '.join(f'{k}={v!r}' for k, v in kwargs.items())
    if _kwargs:
        if _args:
            _args += ', '
        _args += _kwargs
    return textwrap.shorten(_args, shutil.get_terminal_size().columns)


def _redis_command(command: str, *args: 'Any', **kwargs: 'Any') -> 'Any':
    """Wrapper function for Redis command.

    Args:
        command: Command name.
        *args: Arbitrary arguments for the Redis command.

    Keyword Args:
        **kwargs: Arbitrary keyword arguments for the Redis command.

    Return:
        Values returned from the Redis command.

    Warns:
        RedisCommandFailed: Warns at each round when the command failed.

    See Also:
        Between each retry, the function sleeps for :data:`~darc.db.RETRY_INTERVAL`
        second(s) if such value is **NOT** :data:`None`.

    """
    _arg_msg = None

    method = getattr(REDIS, command)
    while True:
        try:
            value = method(*args, **kwargs)
        except Exception as error:
            if _arg_msg is None:
                _arg_msg = _gen_arg_msg(*args, **kwargs)

            warning = warnings.formatwarning(str(error), RedisCommandFailed, __file__, 123,
                                             f'value = redis.{command}({_arg_msg})')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member

            if RETRY_INTERVAL is not None:
                time.sleep(RETRY_INTERVAL)
            continue
        break
    return value


def check_call(*args: 'Any', **kwargs: 'Any') -> int:
    """Wraps :func:`subprocess.check_call`."""
    with open('logs/clinic.log', 'at', buffering=1) as file:
        if 'stdout' not in kwargs:
            kwargs['stdout'] = file
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.STDOUT

        for _ in range(3):
            with contextlib.suppress(subprocess.CalledProcessError):
                return subprocess.check_call(*args, **kwargs)  # nosec
            time.sleep(60)

    with contextlib.suppress(subprocess.CalledProcessError):
        subprocess.check_call(['systemctl', 'restart', 'docker'])  # nosec
        raise RuntimeError
    subprocess.run(['reboot'])   # pylint: disable=subprocess-run-check  # nosec
    raise RuntimeError


def clinic(file: str, timeout: int, *services: str) -> None:
    """Memory clinic."""
    print(f'[{datetime.datetime.now().isoformat()}] Stopping DARC services')
    check_call(['docker-compose', '--file', file, 'stop', '--timeout', str(timeout), *services])
    check_call(['docker', 'system', 'prune', '--volumes', '-f'])
    print(f'[{datetime.datetime.now().isoformat()}] Stopped DARC services')

    print(f'[{datetime.datetime.now().isoformat()}] Cleaning out task queues')
    number_requests = _redis_command('eval', SCPT, 1, 'queue_requests', 0, time.time())
    number_selenium = _redis_command('eval', SCPT, 1, 'queue_selenium', 0, time.time())
    #while True:
    #    pool: List[bytes] = [_redis_command('get', name) for name in _redis_command('zrangebyscore', 'queue_requests',  # pylint: disable=line-too-long
    #                                                                                min=0, max=time.time(), start=0, num=MAX_POOL)]  # pylint: disable=line-too-long
    #    if not pool:
    #        break
    #    _redis_command('delete', *pool)
    #while True:
    #    pool: List[bytes] = [_redis_command('get', name) for name in _redis_command('zrangebyscore', 'queue_selenium',  # type: ignore[no-redef] # pylint: disable=line-too-long
    #                                                                                min=0, max=time.time(), start=0, num=MAX_POOL)]  # pylint: disable=line-too-long
    #    if not pool:
    #        break
    #    _redis_command('delete', *pool)
    _redis_command('delete', 'queue_requests', 'queue_selenium')

    with open(POOL_PATH, 'w') as pool_file:
        maxn = _redis_command('zcard',  'queue_hostname')
        for hostname in _redis_command('zrange', 'queue_hostname', 0, maxn):
            print(f'http://{hostname}', file=pool_file)
    print(f'[{datetime.datetime.now().isoformat()}] Cleaned out task queues: {maxn} hostnames, {number_requests} crawler URLs, {number_selenium} loader URLs')

    print(f'[{datetime.datetime.now().isoformat()}] Starting DARC services')
    check_call(['docker-compose', '--file', file, 'up', '--detach', *services])
    print(f'[{datetime.datetime.now().isoformat()}] Started DARC services')


def get_parser() -> 'ArgumentParser':
    """Argument parser."""
    parser = argparse.ArgumentParser('clinic',
                                     description='memory clinic for Redis')

    parser.add_argument('-r', '--redis', required=True, help='URI to the Redis server')
    parser.add_argument('-f', '--file', default='docker-compose.yml', help='path to compose file')
    parser.add_argument('-t', '--timeout', default='10', type=int, help='shutdown timeout in seconds')
    parser.add_argument('services', nargs=argparse.REMAINDER, help='name of services')

    return parser


def main() -> int:
    """Entrypoint."""
    global REDIS, SCPT  # pylint: disable=global-statement

    parser = get_parser()
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        parser.error('compose file not found')

    if args.timeout <= 0:
        parser.error('invalid timeout')

    REDIS = redis.Redis.from_url(args.redis, decode_components=True)
    SCPT = REDIS.register_script(SCPT_TEXT)
    with open('logs/clinic.log', 'at', buffering=1) as file:
        date = datetime.datetime.now().ctime()
        print('-' * len(date), file=file)
        print(date, file=file)
        print('-' * len(date), file=file)

        with contextlib.redirect_stdout(file), contextlib.redirect_stderr(file):
            clinic(args.file, args.timeout, *args.services)
    return 0


if __name__ == "__main__":
    sys.exit(main())
