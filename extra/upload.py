#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload API submission files."""

import argparse
import contextlib
import datetime
import os
import shutil
import subprocess  # nosec
import sys
import time

# root path
ROOT = os.path.dirname(os.path.abspath(__file__))
# script path
SCPT = os.path.join(ROOT, 'upload.sh')
# time delta
ONEDAY = datetime.timedelta(days=1)


def upload(path, host, user):
    """Upload files."""
    today = datetime.date.today()
    today_str = today.isoformat()
    yesterday = (today - ONEDAY).isoformat()

    path_api = os.path.join(path, 'api')
    if not os.path.isdir(os.path.join(path_api, today_str)):
        print(f'[{datetime.datetime.now().isoformat()}] Today\'s API submission files not found...')
        return
    if not os.path.isdir(os.path.join(path_api, yesterday)):
        print(f'[{datetime.datetime.now().isoformat()}] Yesterday\'s API submission files not found...')
        return

    print(f'[{datetime.datetime.now().isoformat()}] Archiving & uploading API submission files...')
    with open('logs/upload.log', 'at', buffering=1) as log_file:
        with contextlib.suppress(subprocess.CalledProcessError):
            subprocess.check_call(['bash', SCPT], env=os.environ.update(dict(  # nosec
                HOST=host,
                USER=user,
                DATE=yesterday,
            )), cwd=path, stdout=log_file, stderr=subprocess.STDOUT)
    print(f'[{datetime.datetime.now().isoformat()}] Uploaded API submission files...')


def get_parser():
    """Argument parser."""
    parser = argparse.ArgumentParser('upload',
                                     description='upload API submission files')

    parser.add_argument('-p', '--path', default='data', help='path to data storage')
    parser.add_argument('-H', '--host', required=True, help='upstream hostname')
    parser.add_argument('-U', '--user', default='', help='upstream user credential')

    return parser


def main():
    """Entryprocess."""
    parser = get_parser()
    args = parser.parse_args()

    if shutil.which('bash') is None:
        parser.error('bash: command not found')

    if shutil.which('curl') is None:
        parser.error('curl: command not found')

    os.makedirs('logs', exist_ok=True)
    if os.path.isfile('logs/upload.log'):
        os.rename('logs/upload.log', f'logs/upload-{time.strftime(r"%Y%m%d-%H%M%S")}.log')

    with open('logs/upload.log', 'at', buffering=1) as file:
        date = datetime.datetime.now().ctime()
        print('-' * len(date), file=file)
        print(date, file=file)
        print('-' * len(date), file=file)

        with contextlib.redirect_stdout(file), contextlib.redirect_stderr(file):
            upload(args.path, args.host, args.user)
    return 0


if __name__ == "__main__":
    sys.exit(main())
