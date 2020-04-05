#!/usr/bin/env bash

set -ex

# archive filename
filename="darc-api-$(hostname -I | awk '{print $1}')-$(date +%Y%m%d-%H%M%S).tar.gz"

# compare API files
tar -cvzf ${filename} ${PATH_API}
rm -r ${PATH_API}

# upload archive
if [ -z ${USER} ]; then
    curl -T ${filename} ${HOST}
else
    curl -T ${filename} ${HOST} --user ${USER}
fi
rm ${filename}
