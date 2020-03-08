.. automodule:: darc.proxy.tor
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.tor.TOR_REQUESTS_PROXY
   :type: Dict[str, Any]

   Proxy for Tor sessions.

   .. seealso::

      * :func:`darc.requests.tor_session`

.. data:: darc.proxy.tor.TOR_SELENIUM_PROXY
   :type: selenium.webdriver.Proxy

   Proxy (|Proxy|_) for Tor web drivers.

   .. seealso::

      * :func:`darc.selenium.tor_driver`

   .. |Proxy| replace:: ``selenium.webdriver.Proxy``
   .. _Proxy: https://www.selenium.dev/selenium/docs/api/py/webdriver/selenium.webdriver.common.proxy.html?highlight=proxy#selenium.webdriver.common.proxy.Proxy

The following constants are configuration through environment variables:

.. data:: darc.proxy.tor.TOR_PORT
   :type: int

   Port for Tor proxy connection.

   :default: ``9050``
   :environ: :data:`TOR_PORT`

.. data:: darc.proxy.tor.TOR_CTRL
   :type: int

   Port for Tor controller connection.

   :default: ``9051``
   :environ: :data:`TOR_CTRL`

.. data:: darc.proxy.tor.TOR_STEM
   :type: bool

   If manage the Tor proxy through |stem|_.

   .. |stem| replace:: ``stem``
   .. _stem: https://stem.torproject.org

   :default: ``True``
   :environ: :data:`TOR_STEM`

.. data:: darc.proxy.tor.TOR_PASS
   :type: str

   Tor controller authentication token.

   :default: ``None``
   :environ: :data:`TOR_PASS`

   .. note::

      If not provided, it will be requested at runtime.

.. data:: darc.proxy.tor.TOR_RETRY
   :type: int

   Retry times for Tor bootstrap when failure.

   :default: ``3``
   :environ: :data:`TOR_RETRY`

.. data:: darc.proxy.tor.BS_WAIT
   :type: float

   Time after which the attempt to start Tor is aborted.

   :default: ``90``
   :environ: :data:`TOR_WAIT`

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: darc.proxy.tor.TOR_CFG
   :type: Dict[str, Any]

   Tor bootstrap configuration for |launch_tor_with_config|_.

   :default: ``{}``
   :environ: :data:`TOR_CFG`

   .. note::

      If provided, it will be parsed from a JSON encoded string.

The following constants are defined for internal usage:

.. data:: darc.proxy.tor._TOR_BS_FLAG
   :type: bool

   If the Tor proxy is bootstrapped.

.. data:: darc.proxy.tor._TOR_PROC
   :type: subprocess.Popen

   Tor proxy process running in the background.

.. data:: darc.proxy.tor._TOR_CTRL
   :type: stem.control.Controller

   Tor controller process (|Controller|_) running in the background.

.. |Controller| replace:: :class:`stem.control.Controller`
.. _Controller: https://stem.torproject.org/api/control.html#stem.control.Controller

.. data:: darc.proxy.tor._TOR_CONFIG
   :type: List[str]

   Tor bootstrap configuration for |launch_tor_with_config|_.

.. |launch_tor_with_config| replace:: :func:`stem.process.launch_tor_with_config`
.. _launch_tor_with_config: https://stem.torproject.org/api/process.html#stem.process.launch_tor_with_config
