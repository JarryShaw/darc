Module Constants
================

Auxiliary Function
------------------

.. autofunction:: darc.const.getpid

General Configurations
----------------------

.. data:: darc.const.REBOOT
   :type: bool

   If exit the program after first round, i.e. crawled all links from the
   |requests|_ link database and loaded all links from the |selenium|_
   link database.

   :default: ``False``
   :environ: :data:`DARC_REBOOT`

.. data:: darc.const.DEBUG
   :type: bool

   If run the program in debugging mode.

   :default: ``False``
   :environ: :data:`DARC_DEBUG`

.. data:: darc.const.VERBOSE
   :type: bool

   If run the program in verbose mode. If :data:`~darc.const.DEBUG` is ``True``,
   then the verbose mode will be always enabled.

   :default: ``False``
   :environ: :data:`DARC_VERBOSE`

.. data:: darc.const.FORCE
   :type: bool

   If ignore ``robots.txt`` rules when crawling (c.f. :func:`~darc.crawl.crawler`).

   :default: ``False``
   :environ: :data:`DARC_FORCE`

.. data:: darc.const.CHECK
   :type: bool

   If check proxy and hostname before crawling (when calling
   :func:`~darc.parse.extract_links`, :func:`~darc.parse.read_sitemap`
   and :func:`~darc.proxy.i2p.read_hosts`).

   If :data:`~darc.const.CHECK_NG` is ``True``, then this environment
   variable will be always set as ``True``.

   :default: ``False``
   :environ: :data:`DARC_CHECK`

.. data:: darc.const.CHECK_NG
   :type: bool

   If check content type through ``HEAD`` requests before crawling
   (when calling :func:`~darc.parse.extract_links`,
   :func:`~darc.parse.read_sitemap` and :func:`~darc.proxy.i2p.read_hosts`).

   :default: ``False``
   :environ: :data:`DARC_CHECK_CONTENT_TYPE`

.. data:: darc.const.ROOT
   :type: str

   The root folder of the project.

.. data:: darc.const.CWD
   :value: '.'

   The current working direcory.

.. data:: darc.const.DARC_CPU
   :type: int

   Number of concurrent processes. If not provided, then the number of
   system CPUs will be used.

   :default: ``None``
   :environ: :data:`DARC_CPU`

.. data:: darc.const.FLAG_MP
   :type: bool

   If enable *multiprocessing* support.

   :default: ``True``
   :environ: :data:`DARC_MULTIPROCESSING`

.. data:: darc.const.FLAG_TH
   :type: bool

   If enable *multithreading* support.

   :default: ``False``
   :environ: :data:`DARC_MULTITHREADING`

   .. note::

      :data:`~darc.const.FLAG_MP` and :data:`~darc.const.FLAG_TH` can
      **NOT** be toggled at the same time.

.. data:: darc.const.DARC_USER
   :type: str

   *Non-root* user for proxies.

   :default: current login user (c.f. |getuser|_)
   :environ: :data:`DARC_USER`

   .. |getuser| replace:: :func:`getpass.getuser`
   .. _getuser: https://docs.python.org/3/library/getpass.html#getpass.getuser

Data Storage
------------

.. data:: darc.const.PATH_DB
   :type: str

   Path to data storage.

   :default: ``data``
   :environ: :data:`PATH_DATA`

   .. seealso::

      See :mod:`darc.save` for more information about source saving.

.. data:: darc.const.PATH_MISC
   :value: '{PATH_DB}/misc/'

   Path to miscellaneous data storage, i.e. ``misc`` folder under the
   root of data storage.

   .. seealso::

      * :data:`darc.const.PATH_DB`

.. data:: darc.const.PATH_LN
   :value: '{PATH_DB}/link.csv'

   Path to the link CSV file, ``link.csv``.

   .. seealso::

      * :data:`darc.const.PATH_DB`
      * :data:`darc.save.save_link`

.. data:: darc.const.PATH_QR
   :value: '{PATH_DB}/_queue_requests.txt'

   Path to the |requests|_ database, ``_queue_requests.txt``.

   .. seealso::

      * :data:`darc.const.PATH_DB`
      * :func:`darc.db.load_requests`
      * :func:`darc.db.save_requests`

.. data:: darc.const.PATH_QS
   :value: '{PATH_DB}/_queue_selenium.txt'

   Path to the |selenium|_ database, ``_queue_selenium.txt``.

   .. seealso::

      * :data:`darc.const.PATH_DB`
      * :func:`darc.db.load_selenium`
      * :func:`darc.db.save_selenium`

.. data:: darc.const.PATH_ID
   :value: '{PATH_DB}/darc.pid'

   Path to the process ID file, ``darc.pid``.

   .. seealso::

      * :data:`darc.const.PATH_DB`
      * :func:`darc.const.getpid`

Web Crawlers
------------

.. data:: darc.const.TIME_CACHE
   :type: float

   Time delta for caches in seconds.

   The :mod:`darc` project supports *caching* for fetched files.
   :data:`~darc.const.TIME_CACHE` will specify for how log the
   fetched files will be cached and **NOT** fetched again.

   .. note::

      If :data:`~darc.const.TIME_CACHE` is ``None`` then caching
      will be marked as *forever*.

   :default: ``60``
   :environ: :data:`TIME_CACHE`

.. data:: darc.const.SE_WAIT
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
   :environ: :data:`SE_WAIT`

.. data:: darc.const.SE_EMPTY
   :value: '<html><head></head><body></body></html>'

   The empty page from |selenium|_.

   .. seealso::

      * :func:`darc.crawl.loader`

White / Black Lists
-------------------

.. data:: darc.const.LINK_WHITE_LIST
   :type: List[re.Pattern]

   White list of hostnames should be crawled.

   :default: ``[]``
   :environ: :data:`LINK_WHITE_LIST`

   .. note::

      Regular expressions are supported.

.. data:: darc.const.LINK_BLACK_LIST
   :type: List[re.Pattern]

   Black list of hostnames should be crawled.

   :default: ``[]``
   :environ: :data:`LINK_BLACK_LIST`

   .. note::

      Regular expressions are supported.

.. data:: darc.const.LINK_FALLBACK
   :type: bool

   Fallback value for :func:`~darc.parse.match_host`.

   :default: ``False``
   :environ: :data:`LINK_FALLBACK`

.. data:: darc.const.MIME_WHITE_LIST
   :type: List[re.Pattern]

   White list of content types should be crawled.

   :default: ``[]``
   :environ: :data:`MIME_WHITE_LIST`

   .. note::

      Regular expressions are supported.

.. data:: darc.const.MIME_BLACK_LIST
   :type: List[re.Pattern]

   Black list of content types should be crawled.

   :default: ``[]``
   :environ: :data:`MIME_BLACK_LIST`

   .. note::

      Regular expressions are supported.

.. data:: darc.const.MIME_FALLBACK
   :type: bool

   Fallback value for :func:`~darc.parse.match_mime`.

   :default: ``False``
   :environ: :data:`MIME_FALLBACK`

.. data:: darc.const.PROXY_WHITE_LIST
   :type: List[str]

   White list of proxy types should be crawled.

   :default: ``[]``
   :environ: :data:`PROXY_WHITE_LIST`

   .. note::

      The proxy types are **case insensitive**.

.. data:: darc.const.PROXY_BLACK_LIST
   :type: List[str]

   Black list of proxy types should be crawled.

   :default: ``[]``
   :environ: :data:`PROXY_BLACK_LIST`

   .. note::

      The proxy types are **case insensitive**.

.. data:: darc.const.PROXY_FALLBACK
   :type: bool

   Fallback value for :func:`~darc.parse.match_proxy`.

   :default: ``False``
   :environ: :data:`PROXY_FALLBACK`

.. |requests| replace:: ``requests``
.. _requests: https://requests.readthedocs.io
.. |selenium| replace:: ``selenium``
.. _selenium: https://www.selenium.dev
