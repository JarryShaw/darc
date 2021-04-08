-------------
Configuration
-------------

The :mod:`darc` project is generally configurable through numerous
environment variables. Below is the full list of supported environment
variables you may use to configure the behaviour of :mod:`darc`.

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

.. envvar:: DARC_URL_PAT

   :type: List[Tuple[:obj:`str`, :obj:`str`, :obj:`int`]] (JSON)
   :default: ``[]``

   Regular expression patterns to match all reasonable URLs.

   The environment variable should be **JSON** encoded, as an *array* of
   *three-element pairs*. In each pair, it contains one scheme (:obj:`str`)
   as the fallback default scheme for matched URL, one Python regular
   expression string (:obj:`str`) as described in the builtin :mod:`re`
   module and one numeric value (:obj:`int`) representing the flags
   as defined in the builtin :mod:`re` module as well.

   .. important::

      The patterns **must** have a named match group ``url``, e.g.
      ``(?P<url>bitcoin:\w+)`` so that the function can extract matched
      URLs from the given pattern.

      And the regular expression will always be used in **ASCII** mode,
      i.e., with :data:`re.ASCII` flag to compile.

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

   See :mod:`darc.db` for more information about database integration.

.. envvar:: PATH_DATA

   :type: :obj:`str` (path)
   :default: ``data``

   Path to data storage.

.. envvar:: REDIS_URL

   :type: :obj:`str` (url)
   :default: ``redis://127.0.0.1``

   URL to the Redis database.

.. envvar:: DB_URL

   :type: :obj:`str` (url)

   URL to the RDS storage.

   .. important::

      The task queues will be saved to ``darc`` database;
      the data submittsion will be saved to ``darcweb`` database.

      Thus, when providing this environment variable, please do
      **NOT** specify the database name.

.. envvar:: DARC_BULK_SIZE

   :type: :obj:`int`
   :default: ``100``

   *Bulk* size for updating databases.

   .. seealso::

      * :func:`darc.db.save_requests`
      * :func:`darc.db.save_selenium`

.. envvar:: LOCK_TIMEOUT

   :type: :obj:`float`
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

.. envvar:: REDIS_LOCK

   :type: :obj:`bool` (:obj:`int`)
   :default: ``0``

   If use Redis (Lua) lock to ensure process/thread-safely operations.

   .. seealso::

      Toggles the behaviour of :func:`darc.db.get_lock`.

.. envvar:: RETRY_INTERVAL

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

   :type: :obj:`float`
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

   :type: :obj:`float`
   :default: ``60``

   Time delta for caches in seconds.

   The :mod:`darc` project supports *caching* for fetched files.
   :data:`TIME_CACHE` will specify for how log the fetched files
   will be cached and **NOT** fetched again.

   .. note::

      If :data:`TIME_CACHE` is :data:`None` then caching will be marked
      as *forever*.

.. envvar:: SE_WAIT

   :type: :obj:`float`
   :default: ``60``

   Time to wait for :mod:`selenium` to finish loading pages.

   .. note::

      Internally, :mod:`selenium` will wait for the browser to finish
      loading the pages before return (i.e. the web API event
      |event|_). However, some extra scripts may take more time
      running after the event.

   .. |event| replace:: ``DOMContentLoaded``
   .. _event: https://developer.mozilla.org/en-US/docs/Web/API/Window/DOMContentLoaded_event

.. envvar:: CHROME_BINARY_LOCATION

   :type: :obj:`str`
   :default: ``google-chrome``

   Path to the Google Chrome binary location.

   .. note::

      This environment variable is mandatory for non *macOS* and/or *Linux* systems.

   .. seealso::

      See :mod:`darc.selenium` for more information.

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

.. envvar:: SAVE_DB

   :type: :obj:`bool`
   :default: :data:`True`

   Save submitted data to database.

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

   :type: :obj:`float`
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

   :type: :obj:`float`
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

   :type: :obj:`float`
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

   :type: :obj:`float`
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
