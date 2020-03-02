# -*- coding: utf-8 -*-
"""Magnet link."""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'magnet.txt')
LOCK = multiprocessing.Lock()


def save_magnet(link: Link):
    """Save magnet link."""
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url, file=file)
