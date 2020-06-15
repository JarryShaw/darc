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
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for saving IRC addresses :data:`~darc.proxy.irc.PATH`.

   .. seealso::

      * :func:`darc.const.get_lock`
