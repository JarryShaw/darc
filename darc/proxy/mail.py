# -*- coding: utf-8 -*-
"""Email address."""

import multiprocessing
import os

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'mail.txt')
LOCK = multiprocessing.Lock()


def save_mail(link: Link):
    """Save email address."""
    with LOCK:
        with open(PATH, 'a') as file:
            print(link.url, file=file)
