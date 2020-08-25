.. automodule:: darc.db
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.db.BULK_SIZE
   :type: int

   :default: ``100``
   :environ: :envvar:`DARC_BULK_SIZE`

   *Bulk* size for updating Redis databases.

   .. seealso::

      * :func:`darc.db.save_requests`
      * :func:`darc.db.save_selenium`

.. data:: darc.db.LOCK_TIMEOUT
   :type: Optional[float]

   :default: ``10``
   :environ: :envvar:`DARC_LOCK_TIMEOUT`

   Lock blocking timeout.

   .. note::

      If is an infinit ``inf``, no timeout will be applied.

   .. seealso::

      Get a lock from :func:`darc.db.get_lock`.

.. data:: darc.db.MAX_POOL
   :type: int

   :default: ``1_000``
   :environ: :envvar:`DARC_MAX_POOL`

   Maximum number of links loading from the database.

   .. note::

      If is an infinit ``inf``, no limit will be applied.

.. data:: darc.db.REDIS_LOCK
   :type: bool

   :default: :data:`False`
   :environ: :envvar:`DARC_REDIS_LOCK`

   If use Redis (Lua) lock to ensure process/thread-safely operations.

   .. seealso::

      Toggles the behaviour of :func:`darc.db.get_lock`.

.. data:: darc.db.RETRY_INTERVAL
   :type: int

   :default: ``10``
   :environ: :envvar:`DARC_RETRY`

   Retry interval between each Redis command failure.

   .. note::

      If is an infinit ``inf``, no interval will be applied.

   .. seealso::

      Toggles the behaviour of :func:`darc.db.redis_command`.
