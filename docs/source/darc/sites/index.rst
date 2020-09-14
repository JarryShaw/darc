Sites Customisation
===================

.. module:: darc.sites

As websites may have authentication requirements, etc., over
its content, the :mod:`darc.sites` module provides sites
customisation hooks to both :mod:`requests` and :mod:`selenium`
crawling processes.

.. toctree::

   default
   bitcoin
   data
   ed2k
   irc
   magnet
   mail
   script
   tel

To customise behaviours over :mod:`requests`, you sites customisation
module should have a :func:`crawler` function, e.g.
:func:`~darc.sites.default.crawler`.

The function takes the :class:`requests.Session` object with proxy settings and
a :class:`~darc.link.Link` object representing the link to be
crawled, then returns a :class:`requests.Response` object containing the final
data of the crawling process.

.. autofunction:: darc.sites.crawler_hook

To customise behaviours over :mod:`selenium`, you sites customisation
module should have a :func:`loader` function, e.g.
:func:`~darc.sites.default.loader`.

The function takes the :class:`~selenium.webdriver.chrome.webdriver.WebDriver`
object with proxy settings and a :class:`~darc.link.Link` object representing
the link to be loaded, then returns the :class:`~selenium.webdriver.chrome.webdriver.WebDriver`
object containing the final data of the loading process.

.. autofunction:: darc.sites.loader_hook

To tell the :mod:`darc` project which sites customisation
module it should use for a certain hostname, you can register
such module to the :data:`~darc.sites.SITEMAP` mapping dictionary.

.. data:: darc.sites.SITEMAP
   :type: DefaultDict[str, Union[str, types.ModuleType]]

   .. code-block:: python

      SITEMAP = collections.defaultdict(lambda: 'default', {
          # 'www.sample.com': 'sample',  # local customised module
      })

   The mapping dictionary for hostname to sites customisation
   modules.

   The fallback value is :mod:`darc.sites.default`.

.. autofunction:: darc.sites._get_module
