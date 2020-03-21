.. automodule:: darc.db
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.db.QR_LOCK
   :type: multiprocessing.Lock

   I/O lock for the |requests|_ database ``_queue_requests.txt``.

   .. seealso::

      * :func:`darc.db.save_requests`

.. data:: darc.db.QS_LOCK
   :type: Union[multiprocessing.Lock, threading.Lock, contextlib.nullcontext]

   I/O lock for the |selenium|_ database ``_queue_selenium.txt``.

   If :data:`~darc.const.FLAG_MP` is ``True``, it will be an instance of ``multiprocessing.Lock``.
   If :data:`~darc.const.FLAG_TH` is ``True``, it will be an instance of ``threading.Lock``.
   If none above, it will be an instance of ``contextlib.nullcontext``.

   .. seealso::

      * :func:`darc.db.save_selenium`
      * :data:`darc.const.FLAG_MP`
      * :data:`darc.const.FLAG_TH`

.. data:: darc.db.MAX_POOL
   :type: int

   :default: ``1_000``
   :environ: :envvar:`DARC_MAX_POOL`

   Maximum number of links loading from the database.

   .. note::

      If is an infinit ``inf``, no limit will be applied.

.. |requests| replace:: ``requests``
.. _requests: https://requests.readthedocs.io
.. |selenium| replace:: ``selenium``
.. _selenium: https://www.selenium.dev
