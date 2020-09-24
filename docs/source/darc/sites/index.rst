Sites Customisation
===================

.. module:: darc.sites

As websites may have authentication requirements, etc., over
its content, the :mod:`darc.sites` module provides sites
customisation hooks to both :mod:`requests` and :mod:`selenium`
crawling processes.

.. toctree::

   _abc
   default
   bitcoin
   data
   ed2k
   irc
   magnet
   mail
   script
   tel

To start with, you just need to define your sites customisation by
inheriting :class:`~darc.sites._abc.BaseSite` and overload corresponding
:meth:`~darc.sites._abc.BaseSite.crawler` and/or
:meth:`~darc.sites._abc.BaseSite.loader` methods.

To customise behaviours over :mod:`requests`, you sites customisation
class should have a :func:`crawler` method, e.g.
:meth:`DefaultSite.crawler <darc.sites.default.DefaultSite.crawler>`.

The function takes the :class:`requests.Session` object with proxy settings and
a :class:`~darc.link.Link` object representing the link to be
crawled, then returns a :class:`requests.Response` object containing the final
data of the crawling process.

.. autofunction:: darc.sites.crawler_hook

To customise behaviours over :mod:`selenium`, you sites customisation
class should have a :func:`loader` method, e.g.
:meth:`DefaultSite.loader <darc.sites.default.DefaultSite.loader>`.

The function takes the :class:`~selenium.webdriver.chrome.webdriver.WebDriver`
object with proxy settings and a :class:`~darc.link.Link` object representing
the link to be loaded, then returns the :class:`~selenium.webdriver.chrome.webdriver.WebDriver`
object containing the final data of the loading process.

.. autofunction:: darc.sites.loader_hook

To tell the :mod:`darc` project which sites customisation
module it should use for a certain hostname, you can register
such module to the :data:`~darc.sites.SITEMAP` mapping dictionary
through :func:`~darc.sites.register`:

.. autofunction:: darc.sites.register

.. data:: darc.sites.SITEMAP
   :type: DefaultDict[str, Type[darc.sites._abc.BaseSite]]

   .. code-block:: python

      from darc.sites.default import DefaultSite

      SITEMAP = collections.defaultdict(lambda: DefaultSite, {
          # 'www.sample.com': SampleSite,  # local customised class
      })

   The mapping dictionary for hostname to sites customisation
   classes.

   The fallback value is :class:`darc.sites.default.DefaultSite`.

.. autofunction:: darc.sites._get_site

.. seealso::

   Please refer to :doc:`/custom` for more examples and explanations.
