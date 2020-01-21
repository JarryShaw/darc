# -*- coding: utf-8 -*-
"""URL utilities."""

import dataclasses
import hashlib
import os
import urllib

import darc.typing as typing
from darc.const import PATH_DB


@dataclasses.dataclass
class Link:
    """Parsed link."""

    # original link
    url: str

    # urllib.parse.urlparse
    url_parse: urllib.parse.ParseResult

    # hostname / netloc
    host: str
    # base folder
    base: str
    # hashed link
    name: str

    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url


def parse_link(link: str, host: typing.Optional[str] = None) -> Link:
    """Parse link."""
    # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    parse = urllib.parse.urlparse(link)
    if host is None:
        host = parse.hostname or parse.netloc

    # <scheme>/<host>/<hash>-<timestamp>.html
    base = os.path.join(PATH_DB, parse.scheme, host)
    name = hashlib.sha256(link.encode()).hexdigest()

    return Link(
        url=link,
        url_parse=parse,
        host=host,
        base=base,
        name=name,
    )
