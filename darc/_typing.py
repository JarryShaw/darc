# -*- coding: utf-8 -*-
"""Typing declrations."""

from typing_extensions import TypedDict


class File(TypedDict):
    """File data structure for :mod:`darc.submit`."""

    #: Relative path to the file.
    path: str
    #: Base64 encoded file content.
    data: str
