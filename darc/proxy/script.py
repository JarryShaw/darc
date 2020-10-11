# -*- coding: utf-8 -*-
"""JavaScript Links
======================

The :mod:`darc.proxy.script` module contains the auxiliary functions
around managing and processing the JavaScript links.

Currently, the :mod:`darc` project directly save the JavaScript links
extracted to the data storage path :data:`~darc.proxy.script.PATH`
without further processing.

"""

import os

from darc.const import PATH_MISC, get_lock
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'script.txt')
LOCK = get_lock()


def save_script(link: Link) -> None:
    """Save JavaScript link.

    The function will save JavaScript link to the file
    as defined in :data:`~darc.proxy.script.PATH`.

    Args:
        link: Link object representing the JavaScript link.

    """
    with LOCK:  # type: ignore
        with open(PATH, 'a') as file:
            print(link.url, file=file)
