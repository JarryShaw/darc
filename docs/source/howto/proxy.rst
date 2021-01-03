How to implement a custom proxy middleware?
===========================================

As had been discussed already in the `documentation`_, the implementation
of a custom proxy is merely two *factory* functions: one yields a
:class:`requests.Session` and/or
:class:`requests_futures.sessions.FuturesSession` instance, one yields a
:class:`selenium.webdriver.Chrome` instance; both with proxy presets.

.. _documentation: https://darc.jarryshaw.me/en/latest/custom.html#custom-proxy

See below an example from the documentation.

.. code-block:: python

    from darc.proxy import register

Session Factory
---------------

The session factory returns a :class:`requests.Session` and/or
:class:`requests_futures.sessions.FuturesSession` instance with presets,
e.g. proxies, user agent, etc.

Type annocation of the function can be described as

.. code-block:: python

    def get_session(futures=False) -> requests.Session: ...

    @typing.overload
    def get_session(futures=True) -> requests_futures.sessions.FuturesSession: ...

For example, let's say you're implementing a Socks5 proxy for `localhost:9293`,
with other presets same as the default factory function, c.f.
:func:`darc.requests.null_session`.

.. code-block:: python

    import requests
    import requests_futures.sessions

    from darc.const import DARC_CPU
    from darc.requests import default_user_agent


    def socks5_session(futures=False):
        """Socks5 proxy session.

        Args:
            futures: If returns a :class:`requests_futures.FuturesSession`.

        Returns:
            Union[requests.Session, requests_futures.FuturesSession]:
            The session object with Socks5 proxy settings.

        """
        if futures:
            session = requests_futures.sessions.FuturesSession(max_workers=DARC_CPU)
        else:
            session = requests.Session()

        session.headers['User-Agent'] = default_user_agent(proxy='Socks5')
        session.proxies.update({
            'http': 'socks5h://localhost:9293',
            'https': 'socks5h://localhost:9293',
        })
        return session

In this case when :mod:`darc` needs to use a Socks5 session for its *crawler*
worker nodes, it will call the ``socks5_session`` function to obtain a preset
session instance.

Driver Factory
--------------

The driver factory returns a :class:`selenium.webdriver.Chrome` instance with
presets, e.g. proxies, options/switches, etc.

Type annocation of the function can be described as

.. code-block:: python

    def get_driver() -> selenium.webdriver.Chrome: ...

For example, let's say you're implementing a Socks5 proxy for `localhost:9293`,
with other presets same as the default factory function, c.f.
:func:`darc.selenium.null_driver`.

.. code-block:: python

    import selenium.webdriver
    import selenium.webdriver.common.proxy

    from darc.selenium import BINARY_LOCATION


    def socks5_driver():
        """Socks5 proxy driver.

        Returns:
            selenium.webdriver.Chrome: The web driver object with Socks5 proxy settings.

        """
        options = selenium.webdriver.ChromeOptions()
        options.binary_location = BINARY_LOCATION
        options.add_argument('--proxy-server=socks5://localhost:9293')
        options.add_argument('--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE localhost"')

        proxy = selenium.webdriver.Proxy()
        proxy.proxyType = selenium.webdriver.common.proxy.ProxyType.MANUAL
        proxy.http_proxy = 'socks5://localhost:9293'
        proxy.ssl_proxy = 'socks5://localhost:9293'

        capabilities = selenium.webdriver.DesiredCapabilities.CHROME.copy()
        proxy.add_to_capabilities(capabilities)

        driver = selenium.webdriver.Chrome(options=options,
                                           desired_capabilities=capabilities)
        return driver

In this case when :mod:`darc` needs to use a Socks5 driver for its *loader*
worker nodes, it will call the ``socks5_driver`` function to obtain a preset
driver instance.

What should I do to register the proxy?
---------------------------------------

All proxies are managed in the :mod:`darc.proxy` module and you can register
your own proxy through :func:`darc.proxy.register`:

.. code-block:: python

    # register proxy
    register('socks5', socks5_session, socks5_driver)

As the codes above suggest, the :func:`darc.proxy.register` takes three
positional arguments: proxy type, session and driver factory functions.

.. seealso::

    :download:`socks5.py <../../../demo/docs/socks5.py>`
