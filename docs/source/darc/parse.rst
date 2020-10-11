.. automodule:: darc.parse
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.parse.URL_PAT
   :type: List[re.Pattern]

   Regular expression patterns to match all reasonable URLs.

   Currently, we have two builtin patterns:

   1. HTTP(S) and other *regular* URLs, e.g. WebSocket, IRC, etc.

   .. code:: python

      re.compile(r'(?P<url>((https?|wss?|irc):)?(//)?\w+(\.\w+)+/?\S*)', re.UNICODE),

   2. Bitcoin accounts, data URIs, (ED2K) magnet links, email addresses,
      telephone numbers, JavaScript functions, etc.

   .. code:: python

      re.compile(r'(?P<url>(bitcoin|data|ed2k|magnet|mailto|script|tel):\w+)', re.ASCII)

   :environ: :envvar:`DARC_URL_PAT`

   .. seealso::

      The patterns are used in :func:`darc.parse.extract_links_from_text`.
