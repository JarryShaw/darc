#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import tempfile


def is_in(line: str, dest: str) -> bool:
    if os.path.isfile(dest):
        with open(dest) as file:
            for content in filter(None, map(lambda s: s.strip(), file)):
                if line == content:
                    return True
    return False


def uniq(path: str, tempdir: str) -> None:
    name = os.path.split(path)[1]
    dest = os.path.join(tempdir, '%s.tmp' % name)

    with open(path) as file:
        for line in filter(None, map(lambda s: s.strip(), file)):
            if line.startswith('#'):
                continue
            if is_in(line, dest):
                continue
            with open(dest, 'at') as out_file:
                print(line, file=out_file)
    os.rename(dest, path)


def main() -> int:
    with tempfile.TemporaryDirectory() as tempdir:
        for path in sys.argv[1:]:
            uniq(path, tempdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
