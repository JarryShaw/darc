# -*- coding: utf-8 -*-
"""Health check running container."""

import argparse
import json
import os
import subprocess
import sys
import time


def healthcheck(file, interval):
    """Health check."""
    container_id_list = subprocess.check_output(['docker-compose', '--file', file,
                                                 'ps', '--quiet'], encoding='utf-8').strip().split()
    if not container_id_list:
        return

    while True:
        for container_id in container_id_list:
            inspect = subprocess.check_output(['docker', 'container', 'inspect',
                                               container_id], encoding='utf-8').strip()
            info = json.loads(inspect)[0]

            # running / paused / exited
            status = info['State']['Status'].casefold()
            if status == 'paused':
                subprocess.check_call(['docker-compose', '--file', file, 'unpause'])
                print(f'Unpaused container {container_id}', file=sys.stderr)
            if status == 'exited':
                subprocess.check_call(['docker-compose', '--file', file, 'up', '--detach'])
                print(f'Started container {container_id}', file=sys.stderr)

            # healthy / unhealthy
            health = info['State']['Health']['Status'].casefold()
            if health == 'unhealthy':
                subprocess.check_call(['docker-compose', '--file', file, 'restart'])
                print(f'Restarted container {container_id}', file=sys.stderr)
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

    return healthcheck(args.file, args.interval)


if __name__ == "__main__":
    sys.exit(main())
