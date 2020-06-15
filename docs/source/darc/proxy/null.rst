.. automodule:: darc.proxy.null
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.null.PATH
   :value: '{PATH_MISC}/invalid.txt'

   Path to the data storage of links with invalid scheme.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.null.LOCK
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for saving links with invalid scheme :data:`~darc.proxy.null.PATH`.

   .. seealso::

      * :func:`darc.const.get_lock`
