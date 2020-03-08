.. darc documentation master file, created by
   sphinx-quickstart on Fri Mar  6 22:53:54 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

``darc`` - Darkweb Crawler Project
==================================

.. toctree::
   :maxdepth: 4

   darc

:mod:`darc` is designed as a swiss-knife for darkweb crawling.
It integrates |requests|_ to collect HTTP request and response
information, such as cookies, header fields, etc. It also bundles
|selenium|_ to provide a fully rendered web page and screenshot
of such view.

The general process of :mod:`darc` can be described as following:

0. :func:`~darc.process.process`: obtain URLs from the |requests|_
   link database (c.f. :func:`~darc.db.load_requests`), and feed
   such URLs to :func:`~darc.crawl.crawler` with *multiprocessing*
   support.

1. :func:`~darc.crawl.crawler`: parse the URL using
   :func:`~darc.link.parse_link`, and check if need to crawl the
   URL (c.f. :data:`~darc.const.PROXY_WHITE_LIST`, :data:`~darc.const.PROXY_BLACK_LIST`
   , :data:`~darc.const.LINK_WHITE_LIST` and :data:`~darc.const.LINK_BLACK_LIST`);
   if true, then crawl the URL with |requests|_.

   If the URL is from a brand new host, :mod:`darc` will first try
   to fetch and save ``robots.txt`` and sitemaps of the host
   (c.f. :func:`~darc.save.save_robots` and :func:`~darc.save.save_sitemap`),
   and extract then save the links from sitemaps (c.f. :func:`~darc.parse.read_sitemap`)
   into link database for future crawling (c.f. :func:`~darc.db.save_requests`).
   Also, if the submission API is provided, :func:`~darc.submit.submit_new_host`
   will be called and submit the documents just fetched.

   If ``robots.txt`` presented, and :data:`~darc.const.FORCE` is
   ``False``, :mod:`darc` will check if allowed to crawl the URL.

   .. note::

      The root path (e.g. ``/`` in https://www.example.com/) will always
      be crawled ignoring ``robots.txt``.

   At this point, :mod:`darc` will call the customised hook function
   from :mod:`darc.sites` to crawl and get the final response object.
   :mod:`darc` will save the session cookies and header information,
   using :func:`~darc.save.save_headers`.

   .. note::

      If :exc:`requests.exceptions.InvalidSchema` is raised, the link
      will be saved by :func:`~darc.save.save_invalid`. Further
      processing is dropped.

   If the content type of response document is not ignored (c.f.
   :data:`~darc.const.MIME_WHITE_LIST` and :data:`~darc.const.MIME_BLACK_LIST`),
   :mod:`darc` will save the document using :func:`~darc.save.save_html` or
   :func:`~darc.save.save_file` accordingly. And if the submission API
   is provided, :func:`~darc.submit.submit_requests` will be called and
   submit the document just fetched.

   If the response document is HTML (``text/html`` and ``application/xhtml+xml``),
   :func:`~darc.parse.extract_links` will be called then to extract all possible
   links from the HTML document and save such links into the database
   (c.f. :func:`~darc.db.save_requests`).

   And if the response status code is between ``400`` and ``600``,
   the URL will be saved back to the link database
   (c.f. :func:`~darc.db.save_requests`). If **NOT**, the URL will
   be saved into |selenium|_ link database to proceed next steps
   (c.f. :func:`~darc.db.save_selenium`).

2. :func:`~darc.process.process`: after the obtained URLs have all been
   crawled, :mod:`darc` will obtain URLs from the |selenium|_ link database
   (c.f. :func:`~darc.db.load_selenium`), and feed such URLs to
   :func:`~darc.crawl.loader`.

   .. note::

      If :data:`~darc.const.FLAG_MP` is ``True``, the function will be
      called with *multiprocessing* support; if :data:`~darc.const.FLAG_TH`
      if ``True``, the function will be called with *multithreading*
      support; if none, the function will be called in single-threading.

3. :func:`~darc.crawl.loader`: parse the URL using
   :func:`~darc.link.parse_link` and start loading the URL using
   |selenium|_ with Google Chrome.

   At this point, :mod:`darc` will call the customised hook function
   from :mod:`darc.sites` to load and return the original
   |Chrome|_ object.

   .. |Chrome| replace:: ``selenium.webdriver.Chrome``
   .. _Chrome: https://www.selenium.dev/selenium/docs/api/py/webdriver_chrome/selenium.webdriver.chrome.webdriver.html#selenium.webdriver.chrome.webdriver.WebDriver

   If successful, the rendered source HTML document will be saved
   using :func:`~darc.save.save_html`, and a full-page screenshot
   will be taken and saved.

   If the submission API is provided, :func:`~darc.submit.submit_selenium`
   will be called and submit the document just loaded.

   Later, :func:`~darc.parse.extract_links` will be called then to
   extract all possible links from the HTML document and save such
   links into the |requests|_ database (c.f. :func:`~darc.db.save_requests`).

.. |requests| replace:: ``requests``
.. _requests: https://requests.readthedocs.io
.. |selenium| replace:: ``selenium``
.. _selenium: https://www.selenium.dev

------------
Installation
------------

.. note::

   :mod:`darc` supports Python all versions above and includes **3.8**.
   Currently, it only supports and is tested on Linux (Ubuntu 18.04)
   and macOS (Catalina).

.. code:: shell

   pip install darc

Please make sure you have Google Chrome and corresponding version of Chrome
Driver installed on your system.

However, the :mod:`darc` project is shipped with Docker and Compose support.
Please see the project root for relevant files and more information.

-----
Usage
-----

The :mod:`darc` project provides a simple CLI::

   usage: darc [-h] [-f FILE] ...

   darkweb swiss knife crawler

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

-------------
Configuration
-------------

Though simple CLI, the :mod:`darc` project is more configurable by
environment variables.

General Configurations
----------------------

.. data:: DARC_REBOOT
   :type: bool (int)

   If exit the program after first round, i.e. crawled all links from the
   |requests|_ link database and loaded all links from the |selenium|_
   link database.

   :default: ``0``

.. data:: DARC_DEBUG
   :type: bool (int)

   If run the program in debugging mode.

   :default: ``0``

.. data:: DARC_VERBOSE
   :type: bool (int)

   If run the program in verbose mode. If :data:`DARC_DEBUG` is ``True``,
   then the verbose mode will be always enabled.

   :default: ``0``

.. data:: DARC_FORCE
   :type: bool (int)

   If ignore ``robots.txt`` rules when crawling (c.f. :func:`~darc.crawl.crawler`).

   :default: ``0``

.. data:: DARC_CHECK
   :type: bool (int)

   If check proxy and hostname before crawling (when calling
   :func:`~darc.parse.extract_links`, :func:`~darc.parse.read_sitemap`
   and :func:`~darc.proxy.i2p.read_hosts`).

   If :data:`DARC_CHECK_CONTENT_TYPE` is ``True``, then this environment
   variable will be always set as ``True``.

   :default: ``0``

.. data:: DARC_CHECK_CONTENT_TYPE
   :type: bool (int)

   If check content type through ``HEAD`` requests before crawling
   (when calling :func:`~darc.parse.extract_links`,
   :func:`~darc.parse.read_sitemap` and :func:`~darc.proxy.i2p.read_hosts`).

   :default: ``0``

.. data:: DARC_CPU
   :type: int

   Number of concurrent processes. If not provided, then the number of
   system CPUs will be used.

   :default: ``None``

.. data:: DARC_MULTIPROCESSING
   :type: bool (int)

   If enable *multiprocessing* support.

   :default: ``1``

.. data:: DARC_MULTITHREADING
   :type: bool (int)

   If enable *multithreading* support.

   :default: ``0``

   .. note::

      :data:`DARC_MULTIPROCESSING` and :data:`DARC_MULTITHREADING` can
      **NOT** be toggled at the same time.

.. data:: DARC_USER
   :type: str

   *Non-root* user for proxies.

   :default: current login user (c.f. |getuser|_)

Data Storage
------------

.. data:: PATH_DATA
   :type: str (path)

   Path to data storage.

   :default: ``data``

   .. seealso::

      See :mod:`darc.save` for more information about source saving.

Web Crawlers
------------

.. data:: TIME_CACHE
   :type: float

   Time delta for caches in seconds.

   The :mod:`darc` project supports *caching* for fetched files.
   :data:`TIME_CACHE` will specify for how log the fetched files
   will be cached and **NOT** fetched again.

   .. note::

      If :data:`TIME_CACHE` is ``None`` then caching will be marked
      as *forever*.

   :default: ``60``

.. data:: SE_WAIT
   :type: float

   Time to wait for |selenium|_ to finish loading pages.

   .. note::

      Internally, |selenium|_ will wait for the browser to finish
      loading the pages before return (i.e. the web API event
      |event|_). However, some extra scripts may take more time
      running after the event.

   .. |event| replace:: ``DOMContentLoaded``
   .. _event: https://developer.mozilla.org/en-US/docs/Web/API/Window/DOMContentLoaded_event

   :default: ``60``

White / Black Lists
-------------------

.. data:: LINK_WHITE_LIST
   :type: List[str] (json)

   White list of hostnames should be crawled.

   :default: ``[]``

   .. note::

      Regular expressions are supported.

.. data:: LINK_BLACK_LIST
   :type: List[str] (json)

   Black list of hostnames should be crawled.

   :default: ``[]``

   .. note::

      Regular expressions are supported.

.. data:: MIME_WHITE_LIST
   :type: List[str] (json)

   White list of content types should be crawled.

   :default: ``[]``

   .. note::

      Regular expressions are supported.

.. data:: MIME_BLACK_LIST
   :type: List[str] (json)

   Black list of content types should be crawled.

   :default: ``[]``

   .. note::

      Regular expressions are supported.

.. data:: PROXY_WHITE_LIST
   :type: List[str] (json)

   White list of proxy types should be crawled.

   :default: ``[]``

   .. note::

      Regular expressions are supported.

.. data:: PROXY_BLACK_LIST
   :type: List[str] (json)

   Black list of proxy types should be crawled.

   :default: ``[]``

   .. note::

      Regular expressions are supported.

.. note::

   If provided,
   :data:`LINK_WHITE_LIST`, :data:`LINK_BLACK_LIST`,
   :data:`MIME_WHITE_LIST`, :data:`MIME_BLACK_LIST`,
   :data:`PROXY_WHITE_LIST` and :data:`PROXY_BLACK_LIST`
   should all be JSON encoded strings.

Data Submission
---------------

.. data:: API_RETRY
   :type: int

   Retry times for API submission when failure.

   :default: ``3``

.. data:: API_NEW_HOST
   :type: str

   API URL for :func:`~darc.submit.submit_new_host`.

   :default: ``None``

.. data:: API_REQUESTS
   :type: str

   API URL for :func:`~darc.submit.submit_requests`.

   :default: ``None``

.. data:: API_SELENIUM
   :type: str

   API URL for :func:`~darc.submit.submit_selenium`.

   :default: ``None``

.. note::

   If :data:`API_NEW_HOST`, :data:`API_REQUESTS`
   and :data:`API_SELENIUM` is ``None``, the corresponding
   submit function will save the JSON data in the path
   specified by :data:`PATH_DATA`.

Tor Proxy Configuration
-----------------------

.. data:: TOR_PORT
   :type: int

   Port for Tor proxy connection.

   :default: ``9050``

.. data:: TOR_CTRL
   :type: int

   Port for Tor controller connection.

   :default: ``9051``

.. data:: TOR_STEM
   :type: bool (int)

   If manage the Tor proxy through |stem|_.

   .. |stem| replace:: ``stem``
   .. _stem: https://stem.torproject.org

   :default: ``1``

.. data:: TOR_PASS
   :type: str

   Tor controller authentication token.

   :default: ``None``

   .. note::

      If not provided, it will be requested at runtime.

.. data:: TOR_RETRY
   :type: int

   Retry times for Tor bootstrap when failure.

   :default: ``3``

.. data:: TOR_WAIT
   :type: float

   Time after which the attempt to start Tor is aborted.

   :default: ``90``

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: TOR_CFG
   :type: Dict[str, Any] (json)

   Tor bootstrap configuration for :func:`stem.process.launch_tor_with_config`.

   :default: ``{}``

   .. note::

      If provided, it should be a JSON encoded string.

I2P Proxy Configuration
-----------------------

.. data:: I2P_PORT
   :type: int

   Port for I2P proxy connection.

   :default: ``4444``

.. data:: I2P_RETRY
   :type: int

   Retry times for I2P bootstrap when failure.

   :default: ``3``

.. data:: I2P_WAIT
   :type: float

   Time after which the attempt to start I2P is aborted.

   :default: ``90``

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: I2P_ARGS
   :type: str (shell)

   I2P bootstrap arguments for ``i2prouter start``.

   If provided, it should be parsed as command
   line arguments (c.f. |split|_).

   :default: ``''``

   .. note::

      The command will be run as :data:`DARC_USER`, if current
      user (c.f. |getuser|_) is *root*.

ZeroNet Proxy Configuration
---------------------------

.. data:: ZERONET_PORT
   :type: int

   Port for ZeroNet proxy connection.

   :default: ``4444``

.. data:: ZERONET_RETRY
   :type: int

   Retry times for ZeroNet bootstrap when failure.

   :default: ``3``

.. data:: ZERONET_WAIT
   :type: float

   Time after which the attempt to start ZeroNet is aborted.

   :default: ``90``

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: ZERONET_PATH
   :type: str (path)

   Path to the ZeroNet project.

   :default: ``/usr/local/src/zeronet``

.. data:: ZERONET_ARGS
   :type: str (shell)

   ZeroNet bootstrap arguments for ``ZeroNet.sh main``.

   :default: ``''``

   .. note::

      If provided, it should be parsed as command
      line arguments (c.f. |split|_).

Freenet Proxy Configuration
---------------------------

.. data:: FREENET_PORT
   :type: int

   Port for Freenet proxy connection.

   :default: ``8888``

.. data:: FREENET_RETRY
   :type: int

   Retry times for Freenet bootstrap when failure.

   :default: ``3``

.. data:: FREENET_WAIT
   :type: float

   Time after which the attempt to start Freenet is aborted.

   :default: ``90``

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: FREENET_PATH
   :type: str (path)

   Path to the Freenet project.

   :default: ``/usr/local/src/freenet``

.. data:: FREENET_ARGS
   :type: str (shell)

   Freenet bootstrap arguments for ``run.sh start``.

   If provided, it should be parsed as command
   line arguments (c.f. |split|_).

   :default: ``''``

   .. note::

      The command will be run as :data:`DARC_USER`, if current
      user (c.f. |getuser|_) is *root*.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |split| replace:: ``shlex.split``
.. _split: https://docs.python.org/3/library/shlex.html#shlex.split

.. |getuser| replace:: :func:`getpass.getuser`
.. _getuser: https://docs.python.org/3/library/getpass.html#getpass.getuser
