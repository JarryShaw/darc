#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Health check running container."""

import argparse
import contextlib
import datetime
import json
import os
import subprocess  # nosec
import sys
import time


def check_call(*args, **kwargs):
    """Wraps :func:`subprocess.check_call`."""
    with open('logs/healthcheck.log', 'at', buffering=1) as file:
        if 'stdout' not in kwargs:
            kwargs['stdout'] = file
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.STDOUT

        for _ in range(3):
            with contextlib.suppress(subprocess.CalledProcessError):
                return subprocess.check_call(*args, **kwargs)  # nosec
            time.sleep(60)

    with contextlib.suppress(subprocess.CalledProcessError):
        return subprocess.check_call(['systemctl', 'restart', 'docker'])  # nosec
    subprocess.run(['reboot'])   # pylint: disable=subprocess-run-check  # nosec


def check_output(*args, **kwargs):
    """Wraps :func:`subprocess.check_output`."""
    for _ in range(3):
        with contextlib.suppress(subprocess.CalledProcessError):
            return subprocess.check_output(*args, **kwargs)  # nosec
        time.sleep(60)

    with contextlib.suppress(subprocess.CalledProcessError):
        return subprocess.check_call(['systemctl', 'restart', 'docker'])  # nosec
    subprocess.run(['reboot'])   # pylint: disable=subprocess-run-check  # nosec


def timestamp(container_id):
    """Get timestamp from last line."""
    line = check_output(['docker', 'logs', '--timestamps', '--tail=1', container_id],
                        encoding='utf-8', stderr=subprocess.STDOUT).strip()
    ts = line.split()[0]

    # YYYY-mm-ddTHH:MM:SS.fffffffffZ
    pt = time.strptime(ts.split('.')[0], r'%Y-%m-%dT%H:%M:%S')
    return time.mktime(pt)


def healthcheck(file, interval, *services):
    """Health check."""
    ps_args = ['docker-compose', '--file', file, 'ps', '--quiet']
    ps_args.extend(services)

    container_id_list = check_output(ps_args, encoding='utf-8').strip().split()
    if not container_id_list:
        return

    ts_dict = dict()
    ps_dict = dict()
    while True:
        for container_id in container_id_list:
            try:
                inspect = subprocess.check_output(['docker', 'container', 'inspect', container_id],  # nosec
                                                  encoding='utf-8').strip()
            except subprocess.CalledProcessError:
                container_id_list = check_output(ps_args, encoding='utf-8').strip().split()
                continue
            info = json.loads(inspect)[0]

            # running / paused / exited
            status = info['State']['Status'].casefold()
            if status == 'paused':
                # uploading...
                last_ts = ps_dict.get(container_id)
                then_ts = timestamp(container_id)
                if last_ts is None:
                    continue
                if then_ts - last_ts >= interval:
                    continue
                del ps_dict[container_id]

                check_call(['docker-compose', '--file', file, 'unpause'])
                print(f'[{datetime.datetime.now().isoformat()}] Unpaused container {container_id}')
            if status == 'exited':
                with open(f'logs/{time.strftime(r"%Y-%m-%d-%H-%M-%S")}.log', 'wb') as log_file:
                    check_call(['docker', 'logs', '-t', '--details', container_id],
                               stdout=log_file, stderr=subprocess.STDOUT)
                check_call(['docker', 'system', 'prune', '--volumes', '-f'])
                check_call(['docker-compose', '--file', file, 'up', '--detach'])
                print(f'[{datetime.datetime.now().isoformat()}] Started container {container_id}')

            # healthy / unhealthy
            health = info['State']['Health']['Status'].casefold()
            if health == 'unhealthy':
                check_call(['docker', 'stop', container_id])
                check_call(['docker', 'system', 'prune', '--volumes', '-f'])
                check_call(['docker-compose', '--file', file, 'up', '--detach'])

                #check_call(['docker-compose', '--file', file, 'restart'])
                print(f'[{datetime.datetime.now().isoformat()}] Restarted container {container_id}')

            # active / inactive
            last_ts = ts_dict.get(container_id)
            then_ts = timestamp(container_id)
            if last_ts is not None:
                if then_ts - last_ts < interval:
                    check_call(['docker', 'stop', container_id])
                    with open(f'logs/{time.strftime(r"%Y-%m-%d-%H-%M-%S")}.log', 'wb') as log_file:
                        check_call(['docker', 'logs', '-t', '--details', container_id],
                                   stdout=log_file, stderr=subprocess.STDOUT)
                    check_call(['docker', 'system', 'prune', '--volumes', '-f'])
                    check_call(['docker-compose', '--file', file, 'up', '--detach'])

                    #check_call(['docker-compose', '--file', file, 'restart'])
                    print(f'[{datetime.datetime.now().isoformat()}] Restarted container {container_id}')
            ts_dict[container_id] = then_ts
        time.sleep(interval)


def get_parser():
    """Argument parser."""
    parser = argparse.ArgumentParser('healthcheck',
                                     description='health check running container')

    parser.add_argument('-f', '--file', default='docker-compose.yml', help='path to compose file')
    parser.add_argument('-i', '--interval', default='3600', type=float, help='interval (in seconds) of health check')
    parser.add_argument('services', nargs=argparse.REMAINDER, help='name of services')

    return parser


def main():
    """Entryprocess."""
    parser = get_parser()
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        parser.error('compose file not found')

    if args.interval <= 0:
        parser.error('invalid interval')

    with open('logs/healthcheck.log', 'at', buffering=1) as file:
        date = datetime.datetime.now().ctime()
        print('-' * len(date), file=file)
        print(date, file=file)
        print('-' * len(date), file=file)

        with contextlib.redirect_stdout(file), contextlib.redirect_stderr(file):
            while True:
                try:
                    healthcheck(args.file, args.interval, *args.services)
                except KeyboardInterrupt:
                    break
                except Exception:
                    time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
