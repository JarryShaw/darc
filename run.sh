#!/usr/bin/env bash

set -e

while true; do
    echo "+ Starting application..."
    python3 -m darc $@
done
