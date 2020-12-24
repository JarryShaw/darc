# -*- coding: utf-8 -*-
"""Redis clinic for releasing memory."""

import argparse
import contextlib
import datetime
import os
import subprocess  # nosec
import sys

from darc.db import _redis_command  # pylint: disable=import-error


def clinic(file: str, timeout: int, *services: str) -> None:
    """Memory clinic."""
    print(f'[{datetime.datetime.now().isoformat()}] Cleaning out task queues')
    _redis_command('delete', 'queue_hostname')
    _redis_command('delete', 'queue_requests')
    _redis_command('delete', 'queue_selenium')
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

    if args.interval <= 0:
        parser.error('invalid interval')

    if args.timeout < 0:
        parser.error('invalid timeout')

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
