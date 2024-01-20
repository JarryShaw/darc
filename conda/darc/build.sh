#!/usr/bin/env bash

#set -ex

$PYTHON -m pip install conda/wheels/* --target darc/_extern -vv
$PYTHON -m pip install . -vv
