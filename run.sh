#!/usr/bin/env bash

set -e

# signal handlers
trap '[ -f ${PATH_DATA}/darc.pid ] && kill -2 $(cat ${PATH_DATA}/darc.pid)' SIGINT SIGTERM SIGKILL

# initialise
echo "+ Starting application..."
python3 -m darc $@

# mainloop
while true; do
    echo "+ Restarting application..."
    python3 -m darc
done
