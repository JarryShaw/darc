# -*- coding: utf-8 -*-
"""IRC address."""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'irc.txt')
LOCK = multiprocessing.Lock()


def save_irc(link: Link):
    """Save irc address."""
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url, file=file)
