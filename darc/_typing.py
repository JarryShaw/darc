# -*- coding: utf-8 -*-
"""Typing declrations."""

import os
import re
import sys

from typing_extensions import Literal, TypedDict

#: Flag if running from ``sphinx-build``.
SPHINX_BUILD = bool(
    re.fullmatch(r'(?ai)sphinx-build(?:\.exe)?',
                 os.path.basename(sys.argv[0]))
)  # type: Literal[False] # type: ignore[assignment]


class File(TypedDict):
    """File data structure for :mod:`darc.submit`."""

    #: Relative path to the file.
    path: str
    #: Base64 encoded file content.
    data: str
