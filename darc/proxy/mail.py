# -*- coding: utf-8 -*-
"""Email Addresses
=====================

The :mod:`darc.proxy.mail` module contains the auxiliary functions
around managing and processing the email addresses.

Currently, the :mod:`darc` project directly save the email
addresses extracted to the data storage file
:data:`~darc.proxy.mail.PATH` without further processing.

"""

import json
import os
from typing import TYPE_CHECKING

from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    import darc.link as darc_link  # Link

PATH = os.path.join(PATH_MISC, 'mail.txt')
LOCK = get_lock()


def save_mail(link: 'darc_link.Link') -> None:
    """Save email address.

    The function will save email address to the file
    as defined in :data:`~darc.proxy.mail.PATH`.

    Args:
        link: Link object representing the email address.

    """
    with LOCK:  # type: ignore[union-attr]
        with open(PATH, 'a') as file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': link.url,
            }), file=file)
