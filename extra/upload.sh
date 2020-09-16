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

# target folder path
api_path="api/${DATE}"

# compare API files
retry tar -czf ${filename} ${api_path}
rm -r ${api_path}

# upload archive
if [ -z ${USER} ]; then
    retry curl -T ${filename} ${HOST}
else
    retry curl -T ${filename} ${HOST} --user ${USER}
fi
rm ${filename}
