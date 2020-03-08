.. automodule:: darc.proxy.ed2k
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.ed2k.PATH
   :value: '{PATH_MISC}/ed2k.txt'

   Path to the data storage of bED2K magnet links.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.ed2k.LOCK
   :type: multiprocessing.Lock

   I/O lock for saving ED2K magnet links :data:`~darc.proxy.ed2k.PATH`.
