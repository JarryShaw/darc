#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload API submission files."""

import argparse
import contextlib
import datetime
import os
import shutil
import subprocess
import sys
import time

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))
# script path
SCPT = os.path.join(ROOT, 'upload.sh')


def check_call(*args, **kwargs):
    """Wraps :func:`subprocess.check_call`."""
    with open('logs/upload.log', 'at', buffering=1) as file:
        if 'stdout' not in kwargs:
            kwargs['stdout'] = file
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.STDOUT

        for _ in range(3):
            with contextlib.suppress(subprocess.CalledProcessError):
                return subprocess.check_call(*args, **kwargs)
            time.sleep(60)


def upload(file, path, host, user):
    """Upload files."""
    path_api = os.path.join(path, 'api')
    if not os.path.isdir(path_api):
        return
    print(f'[{datetime.datetime.now().isoformat()}] Archiving & uploading APi submission files...')

    check_call(['docker-compose', '--file', file, 'pause'])
    with open('logs/upload.log', 'at', buffering=1) as log_file:
        with contextlib.suppress(subprocess.CalledProcessError):
            subprocess.check_call(['bash', SCPT], env=os.environ.update(dict(
                HOST=host,
                USER=user,
            )), cwd=path, stdout=log_file, stderr=subprocess.STDOUT)
    os.makedirs(path_api, exist_ok=True)
    check_call(['docker-compose', '--file', file, 'unpause'])

    print(f'[{datetime.datetime.now().isoformat()}] Uploaded APi submission files...')


def get_parser():
    """Argument parser."""
    parser = argparse.ArgumentParser('upload',
                                     description='upload API submission files')

    parser.add_argument('-f', '--file', default='docker-compose.yml', help='path to compose file')

    parser.add_argument('-p', '--path', default='data', help='path to data storage')
    parser.add_argument('-i', '--interval', default='3600', type=float, help='interval (in seconds) to upload')

    parser.add_argument('-H', '--host', required=True, help='upstream hostname')
    parser.add_argument('-U', '--user', default='', help='upstream user credential')

    return parser


def main():
    """Entryprocess."""
    parser = get_parser()
    args = parser.parse_args()

    if shutil.which('curl') is None:
        parser.error('curl: command not found')

    if not os.path.isfile(args.file):
        parser.error('compose file not found')

    if args.interval <= 0:
        parser.error('invalid interval')

    os.makedirs('logs', exist_ok=True)
    if os.path.isfile('logs/upload.log'):
        os.rename('logs/upload.log', f'logs/upload-{time.strftime(r"%Y%m%d-%H%M%S")}.log')

    with open('logs/upload.log', 'at', buffering=1) as file:
        date = datetime.datetime.now().ctime()
        print('-' * len(date), file=file)
        print(date, file=file)
        print('-' * len(date), file=file)

        with contextlib.redirect_stdout(file), contextlib.redirect_stderr(file):
            ## sleep before first round
            #time.sleep(args.interval)

            while True:
                try:
                    with contextlib.suppress(Exception):
                        upload(args.file, args.path, args.host, args.user)
                except KeyboardInterrupt:
                    break
                time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
