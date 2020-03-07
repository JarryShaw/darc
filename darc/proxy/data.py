# -*- coding: utf-8 -*-
"""Data URI scheme."""

import datetime
import mimetypes
import os

import datauri

from darc.const import PATH_MISC
from darc.link import Link

PATH = os.path.join(PATH_MISC, 'data')
os.makedirs(PATH, exist_ok=True)


def save_data(link: Link):
    """Save data URI."""
    data = datauri.DataURI(link.url)
    ext = mimetypes.guess_extension(data.mimetype) or '.dat'
    ts = datetime.datetime.now().isoformat()

    path = os.path.join(PATH, f'{link.name}_{ts}{ext}')
    with open(path, 'wb') as file:
        file.write(data.data)
