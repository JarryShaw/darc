Proxy Utilities
===============

.. module:: darc.proxy

The :mod:`darc.proxy` module provides various proxy support
to the :mod:`darc` project.

.. toctree::

   bitcoin
   data
   ed2k
   ethereum
   freenet
   i2p
   irc
   magnet
   mail
   null
   script
   tel
   tor
   zeronet

To tell the :mod:`darc` project which proxy settings to be used for the
:class:`requests.Session` objects and :class:`~selenium.webdriver.chrome.webdriver.WebDriver`
objects, you can specify such information in the :data:`darc.proxy.LINK_MAP`
mapping dictionarty.

.. data:: darc.proxy.LINK_MAP
   :type: DefaultDict[str, Tuple[types.FunctionType, types.FunctionType]]

   .. code-block:: python

      LINK_MAP = collections.defaultdict(
          lambda: (darc.requests.null_session, darc.selenium.null_driver),
          {
              'tor': (darc.requests.tor_session, darc.selenium.tor_driver),
              'i2p': (darc.requests.i2p_session, darc.selenium.i2p_driver),
          }
      )

   The mapping dictionary for proxy type to its corresponding :class:`requests.Session`
   factory function and :class:`~selenium.webdriver.chrome.webdriver.WebDriver` factory function.

   The fallback value is the no proxy :class:`requests.Session` object
   (:func:`~darc.requests.null_session`) and :class:`~selenium.webdriver.chrome.webdriver.WebDriver` object
   (:func:`~darc.selenium.null_driver`).

   .. seealso::

      * :mod:`darc.requests` -- :class:`requests.Session` factory functions
      * :mod:`darc.selenium` -- :class:`~selenium.webdriver.chrome.webdriver.WebDriver` factory functions
