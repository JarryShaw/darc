.. darc documentation master file, created by
   sphinx-quickstart on Fri Mar  6 22:53:54 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

``darc`` - Darkweb Crawler Project
==================================

.. toctree::
   :maxdepth: 2

   darc/index
   docker
   demo/api
   demo/model
   aux

:mod:`darc` is designed as a swiss army knife for darkweb crawling.
It integrates :mod:`requests` to collect HTTP request and response
information, such as cookies, header fields, etc. It also bundles
:mod:`selenium` to provide a fully rendered web page and screenshot
of such view.

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

.. code:: shell

   pip install darc

Please make sure you have Google Chrome and corresponding version of Chrome
Driver installed on your system.

.. important::

   Starting from version **0.3.0**, we introduced `Redis`_ for the task
   queue database backend. Please make sure you have it installed, configured,
   and running when using the ``darc`` project.

   .. _Redis: https://redis.io

However, the :mod:`darc` project is shipped with Docker and Compose support.
Please see :doc:`/docker`  for more information.

Or, you may refer to and/or install from the `Docker Hub`_ repository:

.. code:: shell

   docker pull jsnbzh/darc[:TAGNAME]

.. _Docker Hub: https://hub.docker.com/r/jsnbzh/darc

-----
Usage
-----

The :mod:`darc` project provides a simple CLI::

   usage: darc [-h] [-f FILE] ...

   the darkweb crawling swiss army knife

   positional arguments:
     link                  links to craw

   optional arguments:
     -h, --help            show this help message and exit
     -f FILE, --file FILE  read links from file

It can also be called through module entrypoint::

   python -m python-darc ...

.. note::

   The link files can contain **comment** lines, which should start with ``#``.
   Empty lines and comment lines will be ignored when loading.

.. _configuration:

-------------
Configuration
-------------

Though simple CLI, the :mod:`darc` project is more configurable by
environment variables.

General Configurations
----------------------

.. envvar:: DARC_REBOOT

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If exit the program after first round, i.e. crawled all links from the
   :mod:`requests` link database and loaded all links from the :mod:`selenium`
   link database.

   This can be useful especially when the capacity is limited and you wish
   to save some space before continuing next round. See
   :doc:`Docker integration </docker>` for more information.

.. envvar:: DARC_DEBUG

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If run the program in debugging mode.

.. envvar:: DARC_VERBOSE

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If run the program in verbose mode. If :data:`DARC_DEBUG` is :data:`True`,
   then the verbose mode will be always enabled.

.. envvar:: DARC_FORCE

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If ignore ``robots.txt`` rules when crawling (c.f. :func:`~darc.crawl.crawler`).

.. envvar:: DARC_CHECK

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If check proxy and hostname before crawling (when calling
   :func:`~darc.parse.extract_links`, :func:`~darc.proxy.null.read_sitemap`
   and :func:`~darc.proxy.i2p.read_hosts`).

   If :data:`DARC_CHECK_CONTENT_TYPE` is :data:`True`, then this environment
   variable will be always set as :data:`True`.

.. envvar:: DARC_CHECK_CONTENT_TYPE

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If check content type through ``HEAD`` requests before crawling
   (when calling :func:`~darc.parse.extract_links`,
   :func:`~darc.proxy.null.read_sitemap` and :func:`~darc.proxy.i2p.read_hosts`).

.. envvar:: DARC_CPU

   :type: :obj:`int`
   :default: :data:`None`

   Number of concurrent processes. If not provided, then the number of
   system CPUs will be used.

.. envvar:: DARC_MULTIPROCESSING

   :type: :obj:`bool` (:obj:`int`)
   :default: ``1``

   If enable *multiprocessing* support.

.. envvar:: DARC_MULTITHREADING

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If enable *multithreading* support.

.. note::

   :data:`DARC_MULTIPROCESSING` and :data:`DARC_MULTITHREADING` can
   **NOT** be toggled at the same time.

.. envvar:: DARC_USER

   :type: :obj:`str`
   :default: current login user (c.f. :func:`getpass.getuser`)

   *Non-root* user for proxies.

Data Storage
------------

.. seealso::

   See :mod:`darc.save` for more information about source saving.

   See :mod:`darc.db` for more information about Redis database integration.

.. envvar:: PATH_DATA

   :type: :obj:`str` (path)
   :default: ``data``

   Path to data storage.

.. envvar:: REDIS_URL

   :type: :obj:`str` (url)
   :default: ``redis://127.0.0.1``

   URL to the Redis database.

.. envvar:: DARC_BULK_SIZE

   :type: :obj:`int`
   :default: ``100``

   *Bulk* size for updating Redis databases.

   .. seealso::

      * :func:`darc.db.save_requests`
      * :func:`darc.db.save_selenium`

.. envvar:: LOCK_TIMEOUT

   :type: ``float``
   :default: ``10``

   Lock blocking timeout.

   .. note::

      If is an infinit ``inf``, no timeout will be applied.

   .. seealso::

      Get a lock from :func:`darc.db.get_lock`.

.. envvar:: DARC_MAX_POOL

   :type: :obj:`int`
   :default: ``1_000``

   Maximum number of links loaded from the database.

   .. note::

      If is an infinit ``inf``, no limit will be applied.

   .. seealso::

      * :func:`darc.db.load_requests`
      * :func:`darc.db.load_selenium`

.. data:: darc.db.REDIS_LOCK

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If use Redis (Lua) lock to ensure process/thread-safely operations.

   .. seealso::

      Toggles the behaviour of :func:`darc.db.get_lock`.

.. envvar:: REDIS_RETRY

   :type: :obj:`int`
   :default: ``10``

   Retry interval between each Redis command failure.

   .. note::

      If is an infinit ``inf``, no interval will be applied.

   .. seealso::

      Toggles the behaviour of :func:`darc.db.redis_command`.

Web Crawlers
------------

.. envvar:: DARC_WAIT

   :type: ``float``
   :default: ``60``

   Time interval between each round when the :mod:`requests` and/or
   :mod:`selenium` database are empty.

.. envvar:: DARC_SAVE

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If save processed link back to database.

   .. note::

      If :envvar:`DARC_SAVE` is :data:`True`, then :envvar:`DARC_SAVE_REQUESTS`
      and :envvar:`DARC_SAVE_SELENIUM` will be forced to be :data:`True`.

   .. seealso::

      See :mod:`darc.db` for more information about link database.

.. envvar:: DARC_SAVE_REQUESTS

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If save :func:`~darc.crawl.crawler` crawled link back to :mod:`requests` database.

   .. seealso::

      See :mod:`darc.db` for more information about link database.

.. envvar:: DARC_SAVE_SELENIUM

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If save :func:`~darc.crawl.loader` crawled link back to :mod:`selenium` database.

   .. seealso::

      See :mod:`darc.db` for more information about link database.

.. envvar:: TIME_CACHE

   :type: ``float``
   :default: ``60``

   Time delta for caches in seconds.

   The :mod:`darc` project supports *caching* for fetched files.
   :data:`TIME_CACHE` will specify for how log the fetched files
   will be cached and **NOT** fetched again.

   .. note::

      If :data:`TIME_CACHE` is :data:`None` then caching will be marked
      as *forever*.

.. envvar:: SE_WAIT

   :type: ``float``
   :default: ``60``

   Time to wait for :mod:`selenium` to finish loading pages.

   .. note::

      Internally, :mod:`selenium` will wait for the browser to finish
      loading the pages before return (i.e. the web API event
      |event|_). However, some extra scripts may take more time
      running after the event.

   .. |event| replace:: ``DOMContentLoaded``
   .. _event: https://developer.mozilla.org/en-US/docs/Web/API/Window/DOMContentLoaded_event

White / Black Lists
-------------------

.. envvar:: LINK_WHITE_LIST

   :type: ``List[str]`` (JSON)
   :default: ``[]``

   White list of hostnames should be crawled.

   .. note::

      Regular expressions are supported.

.. envvar:: LINK_BLACK_LIST

   :type: ``List[str]`` (JSON)
   :default: ``[]``

   Black list of hostnames should be crawled.

   .. note::

      Regular expressions are supported.

.. envvar:: LINK_FALLBACK

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   Fallback value for :func:`~darc.parse.match_host`.

.. envvar:: MIME_WHITE_LIST

   :type: ``List[str]`` (JSON)
   :default: ``[]``

   White list of content types should be crawled.

   .. note::

      Regular expressions are supported.

.. envvar:: MIME_BLACK_LIST

   :type: ``List[str]`` (JSON)
   :default: ``[]``

   Black list of content types should be crawled.

   .. note::

      Regular expressions are supported.

.. envvar:: MIME_FALLBACK

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   Fallback value for :func:`~darc.parse.match_mime`.

.. envvar:: PROXY_WHITE_LIST

   :type: ``List[str]`` (JSON)
   :default: ``[]``

   White list of proxy types should be crawled.


   .. note::

      The proxy types are **case insensitive**.

.. envvar:: PROXY_BLACK_LIST

   :type: ``List[str]`` (JSON)
   :default: ``[]``

   Black list of proxy types should be crawled.

   .. note::

      The proxy types are **case insensitive**.

.. envvar:: PROXY_FALLBACK

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   Fallback value for :func:`~darc.parse.match_proxy`.

.. note::

   If provided,
   :data:`LINK_WHITE_LIST`, :data:`LINK_BLACK_LIST`,
   :data:`MIME_WHITE_LIST`, :data:`MIME_BLACK_LIST`,
   :data:`PROXY_WHITE_LIST` and :data:`PROXY_BLACK_LIST`
   should all be JSON encoded strings.

Data Submission
---------------

.. envvar:: API_RETRY

   :type: :obj:`int`
   :default: ``3``

   Retry times for API submission when failure.

.. envvar:: API_NEW_HOST

   :type: :obj:`str`
   :default: :data:`None`

   API URL for :func:`~darc.submit.submit_new_host`.

.. envvar:: API_REQUESTS

   :type: :obj:`str`
   :default: :data:`None`

   API URL for :func:`~darc.submit.submit_requests`.

.. envvar:: API_SELENIUM

   :type: :obj:`str`
   :default: :data:`None`

   API URL for :func:`~darc.submit.submit_selenium`.

.. note::

   If :data:`API_NEW_HOST`, :data:`API_REQUESTS`
   and :data:`API_SELENIUM` is :data:`None`, the corresponding
   submit function will save the JSON data in the path
   specified by :data:`PATH_DATA`.

Tor Proxy Configuration
-----------------------

.. envvar:: DARC_TOR

   :type: :obj:`bool` (:obj:`int`)
   :default: ``1``

   If manage the Tor proxy through :mod:`darc`.

.. envvar:: TOR_PORT

   :type: :obj:`int`
   :default: ``9050``

   Port for Tor proxy connection.

.. envvar:: TOR_CTRL

   :type: :obj:`int`
   :default: ``9051``

   Port for Tor controller connection.

.. envvar:: TOR_PASS

   :type: :obj:`str`
   :default: :data:`None`

   Tor controller authentication token.

   .. note::

      If not provided, it will be requested at runtime.

.. envvar:: TOR_RETRY

   :type: :obj:`int`
   :default: ``3``

   Retry times for Tor bootstrap when failure.

.. envvar:: TOR_WAIT

   :type: ``float``
   :default: ``90``

   Time after which the attempt to start Tor is aborted.

   .. note::

      If not provided, there will be **NO** timeouts.

.. envvar:: TOR_CFG

   :type: ``Dict[str, Any]`` (JSON)
   :default: ``{}``

   Tor bootstrap configuration for :func:`stem.process.launch_tor_with_config`.

   .. note::

      If provided, it should be a JSON encoded string.

I2P Proxy Configuration
-----------------------

.. envvar:: DARC_I2P

   :type: :obj:`bool` (:obj:`int`)
   :default: ``1``

   If manage the I2P proxy through :mod:`darc`.

.. envvar:: I2P_PORT

   :type: :obj:`int`
   :default: ``4444``

   Port for I2P proxy connection.

.. envvar:: I2P_RETRY

   :type: :obj:`int`
   :default: ``3``

   Retry times for I2P bootstrap when failure.

.. envvar:: I2P_WAIT

   :type: ``float``
   :default: ``90``

   Time after which the attempt to start I2P is aborted.

   .. note::

      If not provided, there will be **NO** timeouts.

.. envvar:: I2P_ARGS

   :type: :obj:`str` (Shell)
   :default: ``''``

   I2P bootstrap arguments for ``i2prouter start``.

   If provided, it should be parsed as command
   line arguments (c.f. :func:`shlex.split`).

   .. note::

      The command will be run as :data:`DARC_USER`, if current
      user (c.f. :func:`getpass.getuser`) is *root*.

ZeroNet Proxy Configuration
---------------------------

.. envvar:: DARC_ZERONET

   :type: :obj:`bool` (:obj:`int`)
   :default: ``1``

   If manage the ZeroNet proxy through :mod:`darc`.

.. envvar:: ZERONET_PORT

   :type: :obj:`int`
   :default: ``4444``

   Port for ZeroNet proxy connection.

.. envvar:: ZERONET_RETRY

   :type: :obj:`int`
   :default: ``3``

   Retry times for ZeroNet bootstrap when failure.

.. envvar:: ZERONET_WAIT

   :type: ``float``
   :default: ``90``

   Time after which the attempt to start ZeroNet is aborted.

   .. note::

      If not provided, there will be **NO** timeouts.

.. envvar:: ZERONET_PATH

   :type: :obj:`str` (path)
   :default: ``/usr/local/src/zeronet``

   Path to the ZeroNet project.

.. envvar:: ZERONET_ARGS

   :type: :obj:`str` (Shell)
   :default: ``''``

   ZeroNet bootstrap arguments for ``ZeroNet.sh main``.

   .. note::

      If provided, it should be parsed as command
      line arguments (c.f. :func:`shlex.split`).

Freenet Proxy Configuration
---------------------------

.. envvar:: DARC_FREENET

   :type: :obj:`bool` (:obj:`int`)
   :default: ``1``

   If manage the Freenet proxy through :mod:`darc`.

.. envvar:: FREENET_PORT

   :type: :obj:`int`
   :default: ``8888``

   Port for Freenet proxy connection.

.. envvar:: FREENET_RETRY

   :type: :obj:`int`
   :default: ``3``

   Retry times for Freenet bootstrap when failure.

.. envvar:: FREENET_WAIT

   :type: ``float``
   :default: ``90``

   Time after which the attempt to start Freenet is aborted.

   .. note::

      If not provided, there will be **NO** timeouts.

.. envvar:: FREENET_PATH

   :type: :obj:`str` (path)
   :default: ``/usr/local/src/freenet``

   Path to the Freenet project.

.. envvar:: FREENET_ARGS

   :type: :obj:`str` (Shell)
   :default: ``''``

   Freenet bootstrap arguments for ``run.sh start``.

   If provided, it should be parsed as command
   line arguments (c.f. :func:`shlex.split`).

   .. note::

      The command will be run as :data:`DARC_USER`, if current
      user (c.f. :func:`getpass.getuser`) is *root*.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
