.. automodule:: darc.proxy.magnet
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.magnet.PATH
   :value: '{PATH_MISC}/magnet.txt'

   Path to the data storage of magnet links.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.magnet.LOCK
   :type: multiprocessing.Lock

   I/O lock for saving magnet links :data:`~darc.proxy.magnet.PATH`.
