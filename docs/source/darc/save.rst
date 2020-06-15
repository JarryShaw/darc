.. automodule:: darc.save
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.save._SAVE_LOCK
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for saving link hash database ``link.csv``.

   .. seealso::

      * :func:`darc.save.save_link`
      * :func:`darc.const.get_lock`
