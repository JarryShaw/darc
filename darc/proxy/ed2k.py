# -*- coding: utf-8 -*-
"""ED2K magnet link."""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'ed2k.txt')
LOCK = multiprocessing.Lock()


def save_ed2k(link: Link):
    """Save ed2k magnet link."""
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url, file=file)
