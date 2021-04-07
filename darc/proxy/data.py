# -*- coding: utf-8 -*-
"""Data URI Schemes
======================

The :mod:`darc.proxy.data` module contains the auxiliary functions
around managing and processing the data URI schemes.

Currently, the :mod:`darc` project directly save the data URI
schemes extracted to the data storage path
:data:`~darc.proxy.data.PATH` without further processing.

"""

import json
import mimetypes
import os
from typing import TYPE_CHECKING

import datauri

from darc._compat import datetime
from darc.const import PATH_MISC, get_lock

if TYPE_CHECKING:
    import darc.link as darc_link  # Link

LOCK = get_lock()
PATH = os.path.join(PATH_MISC, 'data')
PATH_MAP = os.path.join(PATH, 'data.txt')
os.makedirs(PATH, exist_ok=True)


def save_data(link: 'darc_link.Link') -> None:
    """Save data URI.

    The function will save data URIs to the data storage
    as defined in :data:`~darc.proxy.data.PATH`.

    Args:
        link: Link object representing the data URI.

    """
    data = datauri.DataURI(link.url)
    ext = mimetypes.guess_extension(data.mimetype) or '.dat'
    ts = datetime.now().isoformat()

    path = os.path.join(PATH, f'{link.name}_{ts}{ext}')
    with open(path, 'wb') as file:
        file.write(data.data)

    with LOCK:  # type: ignore[union-attr]
        with open(PATH_MAP, 'a') as data_file:
            print(json.dumps({
                'src': backref.url if (backref := link.url_backref) is not None else None,  # pylint: disable=used-before-assignment
                'url': path,
            }), file=data_file)
