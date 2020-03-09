``darc`` - Darkweb Crawler Project
==================================

``darc`` is designed as a swiss-knife for darkweb crawling.
It integrates ``requests`` to collect HTTP request and response
information, such as cookies, header fields, etc. It also bundles
``selenium`` to provide a fully rendered web page and screenshot
of such view.

The general process of ``darc`` can be described as following:

0. ``darc.process.process`: obtain URLs from the ``requests```
   link database (c.f. ``darc.db.load_requests``), and feed
   such URLs to ``darc.crawl.crawler`` with *multiprocessing*
   support.

1. ``darc.crawl.crawler``: parse the URL using
   ``darc.link.parse_link``, and check if need to crawl the
   URL (c.f. ``darc.const.PROXY_WHITE_LIST`, ``darc.const.PROXY_BLACK_LIST```
   , ``darc.const.LINK_WHITE_LIST` and ``darc.const.LINK_BLACK_LIST```);
   if true, then crawl the URL with ``requests``.

   If the URL is from a brand new host, ``darc`` will first try
   to fetch and save ``robots.txt`` and sitemaps of the host
   (c.f. ``darc.save.save_robots` and ``darc.save.save_sitemap```),
   and extract then save the links from sitemaps (c.f. ``darc.parse.read_sitemap``)
   into link database for future crawling (c.f. ``darc.db.save_requests``).
   Also, if the submission API is provided, ``darc.submit.submit_new_host``
   will be called and submit the documents just fetched.

   If ``robots.txt`` presented, and ``darc.const.FORCE`` is
   ``False``, ``darc`` will check if allowed to crawl the URL.

   **NOTE:**

      The root path (e.g. ``/`` in https://www.example.com/) will always
      be crawled ignoring ``robots.txt``.

   At this point, ``darc`` will call the customised hook function
   from ``darc.sites`` to crawl and get the final response object.
   ``darc`` will save the session cookies and header information,
   using ``darc.save.save_headers``.

   If the content type of response document is not ignored (c.f.
   ``darc.const.MIME_WHITE_LIST` and ``darc.const.MIME_BLACK_LIST```),
   ``darc` will save the document using ``darc.save.save_html``` or
   ``darc.save.save_file`` accordingly. And if the submission API
   is provided, ``darc.submit.submit_requests`` will be called and
   submit the document just fetched.

   If the response document is HTML, ``darc.parse.extract_links``
   will be called then to extract all possible links from the HTML
   document and save such links into the database
   (c.f. ``darc.db.save_requests``).

   And if the response status code is between ``400`` and ``600``,
   the URL will be saved back to the link database
   (c.f. ``darc.db.save_requests``). If **NOT**, the URL will
   be saved into ``selenium`` link database to proceed next steps
   (c.f. ``darc.db.save_selenium``).

2. ``darc.process.process``: after the obtained URLs have all been
   crawled, ``darc` will obtain URLs from the ``selenium``` link database
   (c.f. ``darc.db.load_selenium``), and feed such URLs to
   ``darc.crawl.loader``.

   **NOTE:**

      If ``darc.const.FLAG_MP` is ``True```, the function will be
      called with *multiprocessing* support; if ``darc.const.FLAG_TH``
      if ``True``, the function will be called with *multithreading*
      support; if none, the function will be called in single-threading.

3. ``darc.crawl.loader``: parse the URL using
   ``darc.link.parse_link`` and start loading the URL using
   ``selenium`` with Google Chrome.

   At this point, ``darc`` will call the customised hook function
   from ``darc.sites`` to load and return the original
   ``selenium.webdriver.Chrome`` object.

   If successful, the rendered source HTML document will be saved
   using ``darc.save.save_html``, and a full-page screenshot
   will be taken and saved.

   If the submission API is provided, ``darc.submit.submit_selenium``
   will be called and submit the document just loaded.

   Later, ``darc.parse.extract_links`` will be called then to
   extract all possible links from the HTML document and save such
   links into the ``requests`` database (c.f. ``darc.db.save_requests``).

------------
Installation
------------

**NOTE:**

   ``darc`` supports Python all versions above and includes **3.6**.
   Currently, it only supports and is tested on Linux (*Ubuntu 18.04*)
   and macOS (*Catalina*).

   When installing in Python versions below **3.8**, ``darc`` will
   use |walrus|_ to compile itself for backport compatibility.

   .. |walrus| replace:: ``walrus``
   .. _walrus: https://github.com/pybpc/walrus

.. code:: shell

   pip install python-darc

Please make sure you have Google Chrome and corresponding version of Chrome
Driver installed on your system.

However, the ``darc`` project is shipped with Docker and Compose support.
Please see the project root for relevant files and more information.

-----
Usage
-----

The ``darc`` project provides a simple CLI::

   usage: darc [-h] [-f FILE] ...

   darkweb swiss knife crawler

   positional arguments:
     link                  links to craw

   optional arguments:
     -h, --help            show this help message and exit
     -f FILE, --file FILE  read links from file

It can also be called through module entrypoint::

   python -m darc ...

**NOTE:**

   The link files can contain **comment** lines, which should start with ``#``.
   Empty lines and comment lines will be ignored when loading.
