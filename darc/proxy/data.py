# -*- coding: utf-8 -*-
"""Data URI scheme."""

import mimetypes
import os

import datauri

from darc.link import Link
from darc.save import sanitise


def save_data(link: Link):
    """Save data URI."""
    data = datauri.DataURI(link.url)

    path = sanitise(link, data=True)
    with open(path, 'wb') as file:
        file.write(data.data)

    ext = mimetypes.guess_extension(data.mimetype) or '.dat'
    dst = os.path.join(link.base, f'{link.name}{ext}')
    os.symlink(path, dst)
