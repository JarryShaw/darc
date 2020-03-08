.. automodule:: darc.proxy.bitcoin
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.bitcoin.PATH
   :value: '{PATH_MISC}/bitcoin.txt'

   Path to the data storage of bitcoin addresses.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.bitcoin.LOCK
   :type: multiprocessing.Lock

   I/O lock for saving bitcoin addresses :data:`~darc.proxy.bitcoin.PATH`.
