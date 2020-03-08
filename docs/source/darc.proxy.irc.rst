.. automodule:: darc.proxy.irc
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.irc.PATH
   :value: '{PATH_MISC}/irc.txt'

   Path to the data storage of IRC addresses.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.irc.LOCK
   :type: multiprocessing.Lock

   I/O lock for saving IRC addresses :data:`~darc.proxy.irc.PATH`.
