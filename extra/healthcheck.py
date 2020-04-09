#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Health check running container."""

import argparse
import contextlib
import datetime
import json
import os
import subprocess
import sys
import time


def check_call(*args, **kwargs):
    """Wraps :func:`subprocess.check_call`."""
    while True:
        with contextlib.suppress(subprocess.CalledProcessError):
            return subprocess.check_call(*args, **kwargs)


def check_output(*args, **kwargs):
    """Wraps :func:`subprocess.check_output`."""
    while True:
        with contextlib.suppress(subprocess.CalledProcessError):
            return subprocess.check_output(*args, **kwargs)


def timestamp(container_id):
    """Get timestamp from last line."""
    line = check_output(['docker', 'logs', '--timestamps', '--tail=1', container_id],
                        encoding='utf-8', stderr=subprocess.STDOUT).strip()
    ts = line.split()[0]

    # YYYY-mm-ddTHH:MM:SS.fffffffffZ
    pt = time.strptime(ts.split('.')[0], r'%Y-%m-%dT%H:%M:%S')
    return time.mktime(pt)


def healthcheck(file, interval):
    """Health check."""
    container_id_list = check_output(['docker-compose', '--file', file, 'ps', '--quiet'],
                                     encoding='utf-8').strip().split()
    if not container_id_list:
        return

    ts_dict = dict()
    while True:
        for container_id in container_id_list:
            try:
                inspect = subprocess.check_output(['docker', 'container', 'inspect', container_id],
                                                  encoding='utf-8').strip()
            except subprocess.CalledProcessError:
                container_id_list = check_output(['docker-compose', '--file', file, 'ps', '--quiet'],
                                                 encoding='utf-8').strip().split()
                continue
            info = json.loads(inspect)[0]

            # running / paused / exited
            status = info['State']['Status'].casefold()
            if status == 'paused':
                # uploading...
                continue
                # check_call(['docker-compose', '--file', file, 'unpause'])
                # print(f'[{datetime.datetime.now().isoformat()}] Unpaused container {container_id}')
            if status == 'exited':
                check_call(['docker-compose', '--file', file, 'up', '--detach'])
                print(f'[{datetime.datetime.now().isoformat()}] Started container {container_id}')

            # healthy / unhealthy
            health = info['State']['Health']['Status'].casefold()
            if health == 'unhealthy':
                check_call(['docker-compose', '--file', file, 'restart'])
                print(f'[{datetime.datetime.now().isoformat()}] Restarted container {container_id}')

            # active / inactive
            last_ts = ts_dict.get(container_id)
            then_ts = timestamp(container_id)
            if last_ts is not None:
                if then_ts - last_ts < interval:
                    check_call(['docker-compose', '--file', file, 'restart'])
                    print(f'[{datetime.datetime.now().isoformat()}] Restarted container {container_id}')
            ts_dict[container_id] = then_ts
        time.sleep(interval)


def get_parser():
    """Argument parser."""
    parser = argparse.ArgumentParser('healthcheck',
                                     description='health check running container')

    parser.add_argument('-f', '--file', default='docker-compose.yml', help='path to compose file')
    parser.add_argument('-i', '--interval', default='3600', type=float, help='interval (in seconds) of health check')

    return parser


def main():
    """Entryprocess."""
    parser = get_parser()
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        parser.error('compose file not found')

    if args.interval <= 0:
        parser.error('invalid interval')

    while True:
        try:
            healthcheck(args.file, args.interval)
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
