#!/usr/bin/env bash

set -ex

function retry() {
    while true; do
        >&2 echo "+ $@"
        $@ && break
        >&2 echo "exit: $?"
    done
    >&2 echo "exit: 0"
}

# archive filename
filename="darc-api-$(hostname -I | awk '{print $1}')-$(date +%Y%m%d-%H%M%S).tar.gz"

# compare API files
retry tar -czf ${filename} api
rm -r api

# upload archive
if [ -z ${USER} ]; then
    retry curl -T ${filename} ${HOST}
else
    retry curl -T ${filename} ${HOST} --user ${USER}
fi
rm ${filename}
