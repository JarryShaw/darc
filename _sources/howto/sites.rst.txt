How to implement a sites customisation?
=======================================

As had been discussed already in the `documentation`_, the implementation
of a sites customisation is dead simple: just inherits the
:class:`darc.sites.BaseSite <darc.sites._abc.BaseSite>` class and overwrites
the corresponding :meth:`~darc.sites._abc.BaseSite.crawler` and
:meth:`~darc.sites._abc.BaseSite.loader` *abstract* **static methods**.

.. _documentation: https://darc.jarryshaw.me/en/latest/custom.html#sites-customisation

See below an example from the documentation.

.. code-block:: python

    from darc.sites import BaseSite, register

As the class below suggests, you may implement and register your sites
customisation for *mysite.com* and *www.mysite.com* using the
:class:`MySite` class, where :attr:`~darc.sites._abc.BaseSite.hostname`
attribute contains the list of hostnames to which the class should be
associated with.

**NB**: Implementation details of the ``crawler`` and ``loader``
methods will be discussed in following sections.

.. code-block:: python

    class MySite(BaseSite):
        """This is a site customisation class for demonstration purpose.
        You may implement a module as well should you prefer."""

        #: List[str]: Hostnames the sites customisation is designed for.
        hostname = ['mysite.com', 'www.mysite.com']

        @staticmethod
        def crawler(timestamp, session, link): ...

        @staticmethod
        def loader(timestamp, driver, link): ...

Should your sites customisation be associated with multiple sites, you can
just add them all to the :attr:`hostname` attribute; when you call
:func:`darc.sites.register` to register your sites customisation, the
function will automatically handle the registry association information.

.. code-block:: python

    # register sites implicitly
    register(MySite)

Nonetheless, in case where you would rather specify the hostnames at
runtime (instead of adding them to the :attr:`hostname` attribute), you may
just leave out the :attr:`hostname` attribute as :data:`None` and specify
your list of hostnames at :func:`darc.sites.register` function call.

.. code-block:: python

    # register sites explicitly
    register(MySite, 'mysite.com', 'www.mysite.com')

Crawler Hook
------------

The ``crawler`` method is based on :class:`requests.Session` objects
and returns a :class:`requests.Response` instance representing the
*crawled* web page.

Type annotations of the method can be described as

.. code-block:: python

    @staticmethod
    def crawler(session: requests.Session, link: darc.link.Link) -> requests.Response: ...

where ``session`` is the :class:`requests.Session` instance with **proxy**
presets and ``link`` is the target link (parsed by
:func:`darc.link.parse_link` to provide more information than mere string).

For example, let's say you would like to inject a cookie named ``SessionID``
and an ``Authentication`` header with some fake identity, then you may write
the ``crawler`` method as below.

.. code-block:: python

        @staticmethod
        def crawler(timestamp, session, link):
            """Crawler hook for my site.

            Args:
                timestamp (datetime.datetime): Timestamp of the worker node reference.
                session (requests.Session): Session object with proxy settings.
                link (darc.link.Link): Link object to be crawled.

            Returns:
                requests.Response: The final response object with crawled data.

            """
            # inject cookies
            session.cookies.set('SessionID', 'fake-session-id-value')

            # insert headers
            session.headers['Authentication'] = 'Basic fake-identity-credential'

            response = session.get(link.url, allow_redirects=True)
            return response

In this case when :mod:`darc` crawling the link, the HTTP(S) request will be
provided with a session cookie and HTTP header, so that it may bypass
potential authorisation checks and land on the target page.

Loader Hook
-----------

The ``loader`` method is based on :class:`selenium.webdriver.Chrome` objects
and returns a the original web driver instance containing the *loaded* web
page.

Type annotations of the method can be described as

.. code-block:: python

    @staticmethod
    def loader(driver: selenium.webdriver.Chrome, link: darc.link.Link) -> selenium.webdriver.Chrome: ...

where ``driver`` is the :class:`selenium.webdriver.Chrome` instance with
**proxy** presets and ``link`` is the target link (parsed by
:func:`darc.link.parse_link` to provide more information than mere string).

For example, let's say you would like to animate user login and go to the
target page after successful attempt, then you may write the ``loader``
method as below.

.. code-block:: python

        @staticmethod
        def loader(timestamp, driver, link):
            """Loader hook for my site.

            Args:
                timestamp: Timestamp of the worker node reference.
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

            # check if the attempt succeeded
            if driver.title == 'Please login!':
                raise ValueError('failed to login %s' % link.host)

            # go to the target page
            driver.get(link.url)

            # wait for page to finish loading
            from darc.const import SE_WAIT  # should've been put with the top-level import statements
            if SE_WAIT is not None:
                time.sleep(SE_WAIT)

            return driver

In this case when :mod:`darc` loading the link, the web driver will first
perform user login, so that it may bypass potential authorisation checks
and land on the target page.

In case to drop the link from task queue...
-------------------------------------------

In some scenarios, you may want to remove the target link from the task
queue, then there're basically two ways:

1. do like a wildling, remove it directly from the database

As there're three task queues used in :mod:`darc`, each represents task
queues for the *crawler* (:mod:`requests` database) and *loader*
(:mod:`selenium` database) worker nodes and a track record for known
hostnames (hostname database), you will need to call corresponding functions
to remove the target link from the database desired.

Possible functions are as below:

* :func:`darc.db.drop_hostname`
* :func:`darc.db.drop_requests`
* :func:`darc.db.drop_selenium`

all take one positional argument ``link``, i.e. the :class:`darc.link.Link`
object to be removed.

Say you would like to remove ``https://www.mysite.com`` from the
:mod:`requests` database, then you may just run

.. code-block:: python

    from darc.db import drop_requests
    from darc.link import parse_link

    link = parse_link('https://www.mysite.com')
    drop_requests(link)

2.  or make it in an elegant way

When implementing the sites customisation, you may wish to drop certain
links at runtime, then you may simply raise :exc:`darc.error.LinkNoReturn`
in the corresponding ``crawler`` and/or ``loader`` methods.

For instance, you would like to proceed with ``mysite.com`` but **NOT**
``www.mysite.com`` in the sites customisation, then you may implement your
class as

.. code-block:: python

    from darc.error import LinkNoReturn

    class MySite(BaseSite):

        ...

        @staticmethod
        def crawler(timestamp, session, link):
            if link.host == 'www.mysite.com':
                raise LinkNoReturn(link)

            ...

        @staticmethod
        def loader(timestamp, driver, link):
            if link.host == 'www.mysite.com':
                raise LinkNoReturn(link)

            ...

Then what should I do to include my sites customisation?
--------------------------------------------------------

Simple as well!

Just *install* your codes to where you're running :mod:`darc`, e.g. the
Docker container, remote server, etc.; then change the startup by injecting
your codes before the entrypoint.

Say the structure of the working directory is as below:

.. code-block:: text

    .
    |-- .venv/
    |   |-- lib/python3.8/site-packages
    |   |   |-- darc/
    |   |   |   |-- ...
    |   |   |-- ...
    |   |-- ...
    |-- mysite.py
    |-- ...

where ``.venv`` is the folder of virtual environment with :mod:`darc`
installed and ``mysite.py`` is the file with your sites customisation.

Then you just need to change your ``mysite.py`` with some additional lines
as below:

.. code-block:: python

    # mysite.py

    import sys

    from darc.__main__ import main
    from darc.sites import BaseSite, register


    class MySite(BaseSite):

        ...


    # register sites
    register(MySite)

    if __name__ == '__main__':
        sys.exit(main())

And now, you can start :mod:`darc` through ``python mysite.py [...]`` instead
of ``python -m darc [...]`` with your sites customisation registered to the
system.

.. seealso::

    :download:`mysite.py <../../../demo/docs/mysite.py>`
