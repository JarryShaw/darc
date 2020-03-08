.. automodule:: darc.proxy.i2p
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.i2p.I2P_REQUESTS_PROXY
   :type: Dict[str, Any]

   Proxy for I2P sessions.

   .. seealso::

      * :func:`darc.requests.i2p_session`

.. data:: darc.proxy.i2p.I2P_SELENIUM_PROXY
   :type: selenium.webdriver.Proxy

   Proxy (|Proxy|_) for I2P web drivers.

   .. seealso::

      * :func:`darc.selenium.i2p_driver`

   .. |Proxy| replace:: ``selenium.webdriver.Proxy``
   .. _Proxy: https://www.selenium.dev/selenium/docs/api/py/webdriver/selenium.webdriver.common.proxy.html?highlight=proxy#selenium.webdriver.common.proxy.Proxy

The following constants are configuration through environment variables:

.. data:: darc.proxy.i2p.I2P_PORT
   :type: int

   Port for I2P proxy connection.

   :default: ``4444``
   :environ: :data:`I2P_PORT`

.. data:: darc.proxy.i2p.I2P_RETRY
   :type: int

   Retry times for I2P bootstrap when failure.

   :default: ``3``
   :environ: :data:`I2P_RETRY`

.. data:: darc.proxy.i2p.BS_WAIT
   :type: float

   Time after which the attempt to start I2P is aborted.

   :default: ``90``
   :environ: :data:`I2P_WAIT`

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: darc.proxy.i2p.I2P_ARGS
   :type: List[str]

   I2P bootstrap arguments for ``i2prouter start``.

   If provided, it should be parsed as command
   line arguments (c.f. |split|_).

   :default: ``''``
   :environ: :data:`I2P_ARGS`

   .. note::

      The command will be run as :data:`~darc.const.DARC_USER`,
      if current user (c.f. |getuser|_) is *root*.

.. |split| replace:: ``shlex.split``
.. _split: https://docs.python.org/3/library/shlex.html#shlex.split

.. |getuser| replace:: :func:`getpass.getuser`
.. _getuser: https://docs.python.org/3/library/getpass.html#getpass.getuser

The following constants are defined for internal usage:

.. data:: darc.proxy.i2p._I2P_BS_FLAG
   :type: bool

   If the I2P proxy is bootstrapped.

.. data:: darc.proxy.i2p._I2P_PROC
   :type: subprocess.Popen

   I2P proxy process running in the background.

.. data:: darc.proxy.i2p._I2P_ARGS
   :type: List[str]

   I2P proxy bootstrap arguments.
