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
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for saving bitcoin addresses :data:`~darc.proxy.bitcoin.PATH`.

   .. seealso::

      * :func:`darc.const.get_lock`
