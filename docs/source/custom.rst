Customisations
==============

Currently, :mod:`darc` provides three major customisation points, besides the
various :doc:`environment variables <config>`.

Hooks between Rounds
--------------------

.. seealso::

   See :func:`darc.process.register` for technical information.

As the workers are defined as indefinite loops, we introduced the
*hooks between rounds* to be called at end of each loop. Such hook
functions can process all links that had been crawled and/or loaded
in the past round, or to indicate the end of the indefinite loop, so
that we can stop the workers in an elegant way.

A typical hook function can be defined as following:

.. code-block:: python

    from darc.error import WorkerBreak
    from darc.process import register


    def dummy_hook(node_type, link_pool):
        """A sample hook function that prints the processed links
        in the past round and informs the work to quit.

        Args:
            node_type (Literal['crawler', 'loader']): Type of worker node.
            link_pool (List[darc.link.Link]): List of processed links.

        Returns:
            NoReturn: The hook function will never return, though return
                values will be ignored anyway.

        Raises:
            darc.error.WorkerBreak: Inform the work to quit after this round.

        """
        if node_type == 'crawler':
            verb = 'crawled'
        elif node_type == 'loader':
            verb = 'loaded'
        else:
            raise ValueError('unknown type of worker node: %s' % node_type)

        for link in link_pool:
            print('We just %s the link: %s' % (verb, link.url))
        raise WorkerBreak


    # register the hook function
    register(dummy_hook)

Custom Proxy
------------

.. seealso::

   See :func:`darc.proxy.register` for technical information.

Sometimes, we need proxies to connect to certain targers, such as the Tor
network and I2P proxy. :mod:`darc` decides if it need to use a proxy for
connection based on the :attr:`~darc.link.Link.proxy` value of the target
link.

By default, :mod:`darc` uses *no proxy* for :mod:`requests` sessions
and :mod:`selenium` drivers. However, you may use your own proxies by
registering and/or customising the corresponding factory functions.

A typical factory function pair (e.g., for Socks5 proxy) can be
defined as following:

.. code-block:: python

    import requests
    import requests_futures.sessions
    import selenium.webdriver
    import selenium.webdriver.common.proxy
    from darc.const import DARC_CPU
    from darc.proxy import register
    from darc.requests import default_user_agent
    from darc.selenium import BINARY_LOCATION


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
        session.proxies.update(dict(
            http='socks5h://localhost:9293',
            https='socks5h://localhost:9293',
        ))
        return session


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


    # register proxy
    register('socks5', socks5_session, socks5_driver)

Sites Customisation
-------------------

.. seealso::

   See :func:`darc.sites.register` for technical information.

Since websites may require authentication and/or anti-robot checks,
we need to insert certain cookies, animate some user interactions to
bypass such requirements. :mod:`darc` decides which customisation to
use based on the hostname, i.e. :attr:`~darc.link.Link.host` value of
the target link.

By default, :mod:`darc` uses :mod:`darc.sites.default` as the *no op*
for both :mod:`requests` sessions and :mod:`selenium` drivers. However,
you may use your own sites customisation by registering and/or customising
the corresponding classes, which inherited from :class:`~darc.sites._abc.BaseSite`.

A typical sites customisation class (for better demonstration) can be
defined as following:

.. code-block:: python

    import time

    from darc.const import SE_WAIT
    from darc.sites import BaseSite, register


    class MySite(BaseSite):
        """This is a site customisation class for demonstration purpose.
        You may implement a module as well should you prefer."""

        #: List[str]: Hostnames the sites customisation is designed for.
        hostname = ['mysite.com', 'www.mysite.com']

        @staticmethod
        def crawler(session, link):
            """Crawler hook for my site.

            Args:
                session (requests.Session): Session object with proxy settings.
                link (darc.link.Link): Link object to be crawled.

            Returns:
                requests.Response: The final response object with crawled data.

            """
            # inject cookies
            session.cookies.set('SessionID', 'fake-session-id-value')

            response = session.get(link.url, allow_redirects=True)
            return response

        @staticmethod
        def loader(driver, link):
            """Loader hook for my site.

            Args:
                driver (selenium.webdriver.Chrome): Web driver object with proxy settings.
                link (darc.link.Link): Link object to be loaded.

            Returns:
                selenium.webdriver.Chrome: The web driver object with loaded data.

            """
            # land on login page
            driver.get('https://%s/login' % link.host)

            # animate login attempt
            form = driver.find_element_by_id('login-form')
            form.find_element_by_id('username').send_keys('admin')
            form.find_element_by_id('password').send_keys('p@ssd')
            form.click()

            driver.get(link.url)

            # wait for page to finish loading
            if SE_WAIT is not None:
                time.sleep(SE_WAIT)

            return driver


    # register sites
    register(MySite)

.. important::

   Please note that you may raise :exc:`darc.error.LinkNoReturn` in the ``crawler``
   and/or ``loader`` methods to indicate that such link should be ignored and removed
   from the task queues, e.g. :mod:`darc.sites.data`.
