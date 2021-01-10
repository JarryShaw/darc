.. automodule:: darc.proxy.script
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.script.PATH
   :value: '{PATH_MISC}/script.txt'

   Path to the data storage of bitcoin addresses.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.script.LOCK
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for saving JavaScript links :data:`~darc.proxy.script.PATH`.

   .. seealso::

      * :func:`darc.const.get_lock`
