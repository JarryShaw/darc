.. darc documentation master file, created by
   sphinx-quickstart on Fri Mar  6 22:53:54 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

``darc`` - Darkweb Crawler Project
==================================

.. important::

   Starting from version ``1.0.0``, new features of the project will not be
   developed into this public repository. Only bugfix and security patches will be
   applied to the update and new releases.

:mod:`darc` is designed as a swiss army knife for darkweb crawling.
It integrates :mod:`requests` to collect HTTP request and response
information, such as cookies, header fields, etc. It also bundles
:mod:`selenium` to provide a fully rendered web page and screenshot
of such view.

.. image:: ../img/darc.jpeg

.. toctree::
   :maxdepth: 2

   howto/index
   darc/index
   config
   custom
   docker
   demo/api
   demo/model
   demo/schema
   aux

---------
Rationale
---------

There are two types of *workers*:

* ``crawler`` -- runs the :func:`darc.crawl.crawler` to provide a
  fresh view of a link and test its connectability
* ``loader`` -- run the :func:`darc.crawl.loader` to provide an
  in-depth view of a link and provide more visual information

The general process can be described as following for *workers* of ``crawler`` type:

1. :func:`~darc.process.process_crawler`: obtain URLs from the :mod:`requests`
   link database (c.f. :func:`~darc.db.load_requests`), and feed such URLs to
   :func:`~darc.crawl.crawler`.

   .. note::

      If :data:`~darc.const.FLAG_MP` is :data:`True`, the function will be
      called with *multiprocessing* support; if :data:`~darc.const.FLAG_TH`
      if :data:`True`, the function will be called with *multithreading*
      support; if none, the function will be called in single-threading.

2. :func:`~darc.crawl.crawler`: parse the URL using
   :func:`~darc.link.parse_link`, and check if need to crawl the
   URL (c.f. :data:`~darc.const.PROXY_WHITE_LIST`, :data:`~darc.const.PROXY_BLACK_LIST`,
   :data:`~darc.const.LINK_WHITE_LIST` and :data:`~darc.const.LINK_BLACK_LIST`);
   if true, then crawl the URL with :mod:`requests`.

   If the URL is from a brand new host, :mod:`darc` will first try
   to fetch and save ``robots.txt`` and sitemaps of the host
   (c.f. :func:`~darc.proxy.null.save_robots` and :func:`~darc.proxy.null.save_sitemap`),
   and extract then save the links from sitemaps (c.f. :func:`~darc.proxy.null.read_sitemap`)
   into link database for future crawling (c.f. :func:`~darc.db.save_requests`).
   Also, if the submission API is provided, :func:`~darc.submit.submit_new_host`
   will be called and submit the documents just fetched.

   If ``robots.txt`` presented, and :data:`~darc.const.FORCE` is
   :data:`False`, :mod:`darc` will check if allowed to crawl the URL.

   .. note::

      The root path (e.g. ``/`` in https://www.example.com/) will always
      be crawled ignoring ``robots.txt``.

   At this point, :mod:`darc` will call the customised hook function
   from :mod:`darc.sites` to crawl and get the final response object.
   :mod:`darc` will save the session cookies and header information,
   using :func:`~darc.save.save_headers`.

   .. note::

      If :exc:`requests.exceptions.InvalidSchema` is raised, the link
      will be saved by :func:`~darc.proxy.null.save_invalid`. Further
      processing is dropped.

   If the content type of response document is not ignored (c.f.
   :data:`~darc.const.MIME_WHITE_LIST` and :data:`~darc.const.MIME_BLACK_LIST`),
   :func:`~darc.submit.submit_requests` will be called and submit the document
   just fetched.

   If the response document is HTML (``text/html`` and ``application/xhtml+xml``),
   :func:`~darc.parse.extract_links` will be called then to extract all possible
   links from the HTML document and save such links into the database
   (c.f. :func:`~darc.db.save_requests`).

   And if the response status code is between ``400`` and ``600``,
   the URL will be saved back to the link database
   (c.f. :func:`~darc.db.save_requests`). If **NOT**, the URL will
   be saved into :mod:`selenium` link database to proceed next steps
   (c.f. :func:`~darc.db.save_selenium`).

The general process can be described as following for *workers* of ``loader`` type:

1. :func:`~darc.process.process_loader`: in the meanwhile, :mod:`darc` will
   obtain URLs from the :mod:`selenium` link database (c.f. :func:`~darc.db.load_selenium`),
   and feed such URLs to :func:`~darc.crawl.loader`.

   .. note::

      If :data:`~darc.const.FLAG_MP` is :data:`True`, the function will be
      called with *multiprocessing* support; if :data:`~darc.const.FLAG_TH`
      if :data:`True`, the function will be called with *multithreading*
      support; if none, the function will be called in single-threading.

2. :func:`~darc.crawl.loader`: parse the URL using
   :func:`~darc.link.parse_link` and start loading the URL using
   :mod:`selenium` with Google Chrome.

   At this point, :mod:`darc` will call the customised hook function
   from :mod:`darc.sites` to load and return the original
   :class:`~selenium.webdriver.chrome.webdriver.WebDriver` object.

   If successful, the rendered source HTML document will be saved, and a
   full-page screenshot will be taken and saved.

   If the submission API is provided, :func:`~darc.submit.submit_selenium`
   will be called and submit the document just loaded.

   Later, :func:`~darc.parse.extract_links` will be called then to
   extract all possible links from the HTML document and save such
   links into the :mod:`requests` database (c.f. :func:`~darc.db.save_requests`).

.. important::

   For more information about the hook functions, please refer
   to the :doc:`customisation <custom>` documentations.

------------
Installation
------------

.. note::

   :mod:`darc` supports Python all versions above and includes **3.6**.
   Currently, it only supports and is tested on Linux (*Ubuntu 18.04*)
   and macOS (*Catalina*).

   When installing in Python versions below **3.8**, :mod:`darc` will
   use |walrus|_ to compile itself for backport compatibility.

   .. |walrus| replace:: ``walrus``
   .. _walrus: https://github.com/pybpc/walrus

.. code-block:: shell

   pip install darc

Please make sure you have Google Chrome and corresponding version of Chrome
Driver installed on your system.

.. important::

   Starting from version **0.3.0**, we introduced `Redis`_ for the task
   queue database backend.

   .. _Redis: https://redis.io

   Since version **0.6.0**, we introduced relationship database storage
   (e.g. `MySQL`_, `SQLite`_, `PostgreSQL`_, etc.) for the task queue database
   backend, besides the `Redis`_ database, since it can be too much memory-costly
   when the task queue becomes vary large.

   .. _MySQL: https://mysql.com/
   .. _SQLite: https://www.sqlite.org/
   .. _PostgreSQL: https://www.postgresql.org/

   Please make sure you have one of the backend database installed, configured,
   and running when using the :mod:`darc` project.

However, the :mod:`darc` project is shipped with Docker and Compose support.
Please see :doc:`/docker`  for more information.

Or, you may refer to and/or install from the `Docker Hub`_ repository:

.. code-block:: shell

   docker pull jsnbzh/darc[:TAGNAME]

.. _Docker Hub: https://hub.docker.com/r/jsnbzh/darc

or GitHub Container Registry, with more updated and comprehensive images:

.. code-block:: shell

   docker pull ghcr.io/jarryshaw/darc[:TAGNAME]
   # or the debug image
   docker pull ghcr.io/jarryshaw/darc-debug[:TAGNAME]

-----
Usage
-----

.. important::

   Though simple CLI, the :mod:`darc` project is more configurable by
   environment variables. For more information, please refer to the
   :doc:`environment variable configuration <config>` documentations.

The :mod:`darc` project provides a simple CLI::

   usage: darc [-h] [-v] -t {crawler,loader} [-f FILE] ...

   the darkweb crawling swiss army knife

   positional arguments:
     link                  links to craw

   optional arguments:
     -h, --help            show this help message and exit
     -v, --version         show program's version number and exit
     -t {crawler,loader}, --type {crawler,loader}
                           type of worker process
     -f FILE, --file FILE  read links from file

It can also be called through module entrypoint::

   python -m python-darc ...

.. note::

   The link files can contain **comment** lines, which should start with ``#``.
   Empty lines and comment lines will be ignored when loading.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
