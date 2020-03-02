# -*- coding: utf-8 -*-
"""Bitcoin address."""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'bitcoin.txt')
LOCK = multiprocessing.Lock()


def save_bitcoin(link: Link):
    """Save bitcoin address."""
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url_parse.path, file=file)
