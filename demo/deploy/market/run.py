# -*- coding: utf-8 -*-
#: pylint: disable=import-error
"""Entrypoint for the market module.

Important:
    :class:`MarketSite` is registered as the default sites
    customisation for such scenario. And all other default
    sites customisations will then be removed.

You may simply use this file as the new entrypoint for your
:mod:`darc` worker.

"""

import sys

from dummy import DummySite
from market import MarketSite

from darc.__main__ import main
from darc.sites import SITEMAP, register

# register ``MarketSite`` as the default hook
SITEMAP.default_factory = lambda: MarketSite
# empty existing hooks
SITEMAP.clear()

# register ``DummySite`` since it has ``hostname`` set
register(DummySite)
# or in case it has none...
register(DummySite, 'dummy.onion', 'dummy.com', 'dummy.io')

if __name__ == "__main__":
    sys.exit(main())
