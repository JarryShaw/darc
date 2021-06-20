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
if [ -z "$(ls -A misc)" ]; then
   retry tar -czf ${filename} ${api_path}
else
   retry tar -czf ${filename} ${api_path} misc/*.txt
fi
rm -r ${api_path} misc/*.txt

# upload archive
if [ -z ${USER} ]; then
    retry curl -T ${filename} ${HOST}
else
    retry curl -T ${filename} ${HOST} --user ${USER}
fi
rm ${filename}

# upload outdated archives
for file in $(ls darc-api-*.tar.gz); do
    if [ -f ${file} ]; then
        if [ -z ${USER} ]; then
            retry curl -T ${file} ${HOST}
        else
            retry curl -T ${file} ${HOST} --user ${USER}
        fi
        rm ${file}
    fi
done
