# -*- coding: utf-8 -*-
"""Email Addresses
=====================

The :mod:`darc.proxy.mail` module contains the auxiliary functions
around managing and processing the email addresses.

Currently, the :mod:`darc` project directly save the email
addresses extracted to the data storage file
:data:`~darc.proxy.mail.PATH` without further processing.

"""

import os

from darc.const import PATH_MISC, get_lock
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'mail.txt')
LOCK = get_lock()


def save_mail(link: Link) -> None:
    """Save email address.

    The function will save email address to the file
    as defined in :data:`~darc.proxy.mail.PATH`.

    Args:
        link: Link object representing the email address.

    """
    with LOCK:  # type: ignore
        with open(PATH, 'a') as file:
            print(link.url, file=file)
