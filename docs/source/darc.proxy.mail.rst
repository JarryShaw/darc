.. automodule:: darc.proxy.mail
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.proxy.mail.PATH
   :value: '{PATH_MISC}/mail.txt'

   Path to the data storage of email addresses.

   .. seealso::

      * :data:`darc.const.PATH_MISC`

.. data:: darc.proxy.mail.LOCK
   :type: multiprocessing.Lock

   I/O lock for saving email addresses :data:`~darc.proxy.mail.PATH`.
