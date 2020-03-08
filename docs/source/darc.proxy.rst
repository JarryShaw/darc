Proxy Utilities
===============

The :mod:`darc.proxy` module provides various proxy support
to the :mod:`darc` project.

.. toctree::

   darc.proxy.bitcoin
   darc.proxy.data
   darc.proxy.ed2k
   darc.proxy.freenet
   darc.proxy.i2p
   darc.proxy.irc
   darc.proxy.magnet
   darc.proxy.mail
   darc.proxy.null
   darc.proxy.tor
   darc.proxy.zeronet

To tell the :mod:`darc` project which proxy settings to be used for the
|Session|_ objects and |Chrome| objects, you can specify such information
in the :data:`darc.proxy.LINK_MAP` mapping dictionarty.

.. data:: darc.proxy.LINK_MAP
   :type: DefaultDict[str, Tuple[types.FunctionType, types.FunctionType]]

   .. code:: python

      LINK_MAP = collections.defaultdict(
          lambda: (darc.requests.null_session, darc.selenium.null_driver),
          dict(
              tor=(darc.requests.tor_session, darc.selenium.tor_driver),
              i2p=(darc.requests.i2p_session, darc.selenium.i2p_driver),
          )
      )

   The mapping dictionary for proxy type to its corresponding |Session|_
   factory function and |Chrome|_ factory function.

   The fallback value is the no proxy |Session|_ object
   (:func:`~darc.requests.null_session`) and |Chrome|_ object
   (:func:`~darc.selenium.null_driver`).

   .. seealso::

      * :mod:`darc.requests` -- |Session|_ factory functions
      * :mod:`darc.selenium` -- |Chrome|_ factory functions

.. |requests| replace:: ``requests``
.. _requests: https://requests.readthedocs.io
.. |selenium| replace:: ``selenium``
.. _selenium: https://www.selenium.dev

.. |Response| replace:: ``requests.Response``
.. _Response: https://requests.readthedocs.io/en/latest/api/index.html#requests.Response
.. |Session| replace:: ``requests.Session``
.. _Session: https://requests.readthedocs.io/en/latest/api/index.html#requests.Session

.. |Chrome| replace:: ``selenium.webdriver.Chrome``
.. _Chrome: https://www.selenium.dev/selenium/docs/api/py/webdriver_chrome/selenium.webdriver.chrome.webdriver.html#selenium.webdriver.chrome.webdriver.WebDriver
