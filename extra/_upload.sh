#!/usr/bin/env bash

set -e

pushd /root/darc/data/

TODAY="$(date +%Y-%m-%d)"

for date in $(ls -A /root/darc/data/api/ 2>/dev/null); do
    if [ $date != $TODAY ]; then
        export HOST="ftp://202.120.1.153:21"
        export USER="darkcrawler:zft13917331612"
        export DATE="$date"
        /root/darc/extra/upload.sh
    fi
done

popd
