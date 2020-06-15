.. automodule:: darc.proxy.tel
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.tel.PATH
   :value: '{PATH_MISC}/tel.txt'

   Path to the data storage of bitcoin addresses.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.tel.LOCK
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for saving telephone numbers :data:`~darc.proxy.tel.PATH`.

   .. seealso::

      * :func:`darc.const.get_lock`
