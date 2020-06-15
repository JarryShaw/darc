Darkweb Crawler Project
=======================

.. module:: darc

:mod:`darc` is designed as a swiss army knife for darkweb crawling.
It integrates :mod:`requests` to collect HTTP request and response
information, such as cookies, header fields, etc. It also bundles
:mod:`selenium` to provide a fully rendered web page and screenshot
of such view.

.. toctree::

   process
   crawl
   link
   parse
   save
   db
   submit
   requests
   selenium
   proxy/index
   sites/index
   const
   error

As the websites can be sometimes irritating for their anti-robots
verification, login requirements, etc., the :mod:`darc` project
also privides hooks to customise crawling behaviours around both
:mod:`requests` and :mod:`selenium`.

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

   When rendering the target website using :mod:`selenium` powered by
   the renown Google Chrome, it will require much memory to run.
   Thus, the three solutions mentioned above would only toggle the
   behaviour around the use of :mod:`selenium`.

To keep the :mod:`darc` project as it is a swiss army knife, only the
main entrypoint function :func:`darc.process.process` is exported
in global namespace (and renamed to :func:`darc.darc`), see below:

.. autofunction:: darc.darc
