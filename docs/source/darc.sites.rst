Sites Customisation
===================

As websites may have authentication requirements, etc., over
its content, the :mod:`darc.sites` module provides sites
customisation hooks to both |requests|_ and |selenium|_
crawling processes.

.. toctree::

   darc.sites.default

To customise behaviours over |requests|_, you sites customisation
module should have a :func:`crawler` function, e.g.
:func:`~darc.sites.default.crawler`.

The function takes the |Session|_ object with proxy settings and
a :class:`~darc.link.Link` object representing the link to be
crawled, then returns a |Response|_ object containing the final
data of the crawling process.

.. autofunction:: darc.sites.crawler_hook

To customise behaviours over |selenium|_, you sites customisation
module should have a :func:`loader` function, e.g.
:func:`~darc.sites.default.loader`.

The function takes the |Chrome|_ object with proxy settings and
a :class:`~darc.link.Link` object representing the link to be
loaded, then returns the |Chrome|_ object containing the final
data of the loading process.

.. autofunction:: darc.sites.loader_hook

To tell the :mod:`darc` project which sites customisation
module it should use for a certain hostname, you can register
such module to the :data:`~darc.sites.SITEMAP` mapping dictionary.

.. data:: darc.sites.SITEMAP
   :type: DefaultDict[str, str]

   .. code:: python

      SITEMAP = collections.defaultdict(lambda: 'default', {
          # 'www.sample.com': 'sample',  # darc.sites.sample
      })

   The mapping dictionary for hostname to sites customisation
   modules.

   The fallback value is ``default``, c.f. :mod:`darc.sites.default`.

.. autofunction:: darc.sites._get_spec

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
