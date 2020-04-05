#!/usr/bin/env bash

set -e

# time lapse
WAIT=${DARC_WAIT=10}

# signal handlers
trap '[ -f ${PATH_DATA}/darc.pid ] && kill -2 $(cat ${PATH_DATA}/darc.pid)' SIGINT SIGTERM SIGKILL

function review() {
    (
        if [ -f "${PATH_DATA}/_queue_requests.txt.tmp" ]; then
            cat "${PATH_DATA}/_queue_requests.txt.tmp" | sort | uniq >> /tmp/_queue_requests.txt
            rm "${PATH_DATA}/_queue_requests.txt.tmp"
        fi

        if [ -f "${PATH_DATA}/_queue_requests.txt" ]; then
            cat "${PATH_DATA}/_queue_requests.txt" | sort | uniq >> /tmp/_queue_requests.txt
            rm "${PATH_DATA}/_queue_requests.txt"
        fi

        if [ -f /tmp/_queue_requests.txt ]; then
            cat /tmp/_queue_requests.txt | sort | uniq | shuf > "${PATH_DATA}/_queue_requests.txt"
            rm /tmp/_queue_requests.txt
        fi

        if [ -f "${PATH_DATA}/_queue_selenium.txt.tmp" ]; then
            cat "${PATH_DATA}/_queue_selenium.txt.tmp" | sort | uniq >> /tmp/_queue_selenium.txt
            rm "${PATH_DATA}/_queue_selenium.txt.tmp"
        fi

        if [ -f "${PATH_DATA}/_queue_selenium.txt" ]; then
            cat "${PATH_DATA}/_queue_selenium.txt" | sort | uniq >> /tmp/_queue_selenium.txt
            rm "${PATH_DATA}/_queue_selenium.txt"
        fi

        if [ -f /tmp/_queue_selenium.txt ]; then
            cat /tmp/_queue_selenium.txt | sort | uniq | shuf > "${PATH_DATA}/_queue_selenium.txt"
            rm /tmp/_queue_selenium.txt
        fi
    )
}

# compress link database
review || true

# initialise
echo "+ Starting application..."
python3 -m darc $@
sleep ${WAIT}

# mainloop
while true; do
    # compress link database
    review || true

    echo "+ Restarting application..."
    python3 -m darc
    sleep ${WAIT}
done
