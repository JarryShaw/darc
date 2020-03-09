# -*- coding: utf-8 -*-
"""Darkweb Crawler Project
=============================

:mod:`darc` is designed as a swiss-knife for darkweb crawling.
It integrates |requests|_ to collect HTTP request and response
information, such as cookies, header fields, etc. It also bundles
|selenium|_ to provide a fully rendered web page and screenshot
of such view.

As the websites can be sometimes irritating for their anti-robots
verification, login requirements, etc., the :mod:`darc` project
also privides hooks to customise crawling behaviours around both
|requests|_ and |selenium|_.

.. seealso::

   Such customisation, as called in the :mod:`darc` project, site
   hooks, is site specific, user can set up your own hooks unto a
   certain site, c.f. :mod:`darc.sites` for more information.

Still, since the network is a world full of mysteries and miracles,
the speed of crawling will much depend on the response speed of
the target website. To boost up, as well as meet the system capacity,
the :mod:`darc` project introduced multiprocessing, multithreading
and the fallback slowest single-threaded solutions when crawling.

.. note::

   When rendering the target website using |selenium|_ powered by
   the renown Google Chrome, it will require much memory to run.
   Thus, the three solutions mentioned above would only toggle the
   behaviour around the use of |selenium|_.

"""

from darc.process import process as darc  # pylint: disable=unused-import

__all__ = ['darc']
__version__ = '0.1.2'
