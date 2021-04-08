.. automodule:: darc.proxy.ethereum
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.ethereum.PATH
   :value: '{PATH_MISC}/ethereum.txt'

   Path to the data storage of ethereum addresses.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.ethereum.LOCK
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for saving ethereum addresses :data:`~darc.proxy.ethereum.PATH`.

   .. seealso::

      * :func:`darc.const.get_lock`
