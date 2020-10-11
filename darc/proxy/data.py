# -*- coding: utf-8 -*-
"""Data URI Schemes
======================

The :mod:`darc.proxy.data` module contains the auxiliary functions
around managing and processing the data URI schemes.

Currently, the :mod:`darc` project directly save the data URI
schemes extracted to the data storage path
:data:`~darc.proxy.data.PATH` without further processing.

"""

import mimetypes
import os

import datauri

from darc._compat import datetime
from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'data')
os.makedirs(PATH, exist_ok=True)


def save_data(link: Link) -> None:
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
