# -*- coding: utf-8 -*-
"""Redis clinic for releasing memory."""

import argparse
import contextlib
import datetime
import math
import os
import subprocess  # nosec
import sys
import textwrap
import shutil
import warnings
import time
from typing import Any, AnyStr

import redis
import stem.util.term

# Redis retry interval
RETRY_INTERVAL = float(os.getenv('DARC_RETRY', '10'))
if not math.isfinite(RETRY_INTERVAL):
    RETRY_INTERVAL = None  # type: ignore


class RedisCommandFailed(Warning):
    """Redis command execution failed."""


def render_error(message: AnyStr, colour: stem.util.term.Color) -> str:
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


def _gen_arg_msg(*args, **kwargs) -> str:  # type: ignore
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


def _redis_command(client: redis.Redis, command: str, *args: Any, **kwargs: Any) -> Any:
    """Wrapper function for Redis command.

    Args:
        client: Redis client.
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

    method = getattr(client, command)
    while True:
        try:
            value = method(*args, **kwargs)
        except Exception as error:
            if _arg_msg is None:
                _arg_msg = _gen_arg_msg(*args, **kwargs)

            warning = warnings.formatwarning(str(error), RedisCommandFailed, __file__, 131,
                                             f'value = redis.{command}({_arg_msg})')
            print(render_error(warning, stem.util.term.Color.YELLOW), end='', file=sys.stderr)  # pylint: disable=no-member

            if RETRY_INTERVAL is not None:
                time.sleep(RETRY_INTERVAL)
            continue
        break
    return value


def clinic(client: redis.Redis, file: str, timeout: int, *services: str) -> None:
    """Memory clinic."""
    print(f'[{datetime.datetime.now().isoformat()}] Cleaning out task queues')
    _redis_command(client, 'delete', 'queue_hostname')
    _redis_command(client, 'delete', 'queue_requests')
    _redis_command(client, 'delete', 'queue_selenium')
    print(f'[{datetime.datetime.now().isoformat()}] Cleaned out task queues')

    print(f'[{datetime.datetime.now().isoformat()}] Restarting DARC services')
    subprocess.check_call([  # nosec
        'docker-compose', '--file', file, 'restart', '--timeout', str(timeout), *services,
    ])
    print(f'[{datetime.datetime.now().isoformat()}] Restarted DARC services')


def get_parser() -> argparse.ArgumentParser:
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
    parser = get_parser()
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        parser.error('compose file not found')

    if args.timeout <= 0:
        parser.error('invalid timeout')

    client = redis.Redis.from_url(args.redis, decode_components=True)
    with open('logs/clinic.log', 'at', buffering=1) as file:
        date = datetime.datetime.now().ctime()
        print('-' * len(date), file=file)
        print(date, file=file)
        print('-' * len(date), file=file)

        with contextlib.redirect_stdout(file), contextlib.redirect_stderr(file):
            clinic(client, args.file, args.timeout, *args.services)
    return 0


if __name__ == "__main__":
    sys.exit(main())
