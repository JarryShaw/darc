#!/usr/bin/env bash

set -e

trap '[ -f ${PATH_DATA}/darc.pid ] && kill -2 $(cat ${PATH_DATA}/darc.pid)' SIGINT SIGTERM SIGKILL

while true; do
    echo "+ Starting application..."
    python3 -m darc $@
done
