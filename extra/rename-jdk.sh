#!/usr/bin/env sh

# get version
version=$(apt-cache show oracle-java11-installer-local | grep Version | cut -d' ' -f2 | cut -d'-' -f1)
echo "Target version: $version"

# rename file
mov /var/cache/oracle-jdk11-installer-local/jdk-11.*.*_linux-x64_bin.tar.gz \
  /var/cache/oracle-jdk11-installer-local/jdk-${version}_linux-x64_bin.tar.gz
