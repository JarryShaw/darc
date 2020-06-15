.. automodule:: darc.proxy.freenet
   :members:
   :undoc-members:
   :show-inheritance:

The following constants are configuration through environment variables:

.. data:: darc.proxy.freenet.FREENET_PORT
   :type: int

   Port for Freenet proxy connection.

   :default: ``8888``
   :environ: :data:`FREENET_PORT`

.. data:: darc.proxy.freenet.FREENET_RETRY
   :type: int

   Retry times for Freenet bootstrap when failure.

   :default: ``3``
   :environ: :data:`FREENET_RETRY`

.. data:: darc.proxy.freenet.BS_WAIT
   :type: float

   Time after which the attempt to start Freenet is aborted.

   :default: ``90``
   :environ: :data:`FREENET_WAIT`

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: darc.proxy.freenet.FREENET_PATH
   :type: str

   Path to the Freenet project.

   :default: ``/usr/local/src/freenet``
   :environ: :data:`FREENET_PATH`

.. data:: darc.proxy.freenet.FREENET_ARGS
   :type: List[str]

   Freenet bootstrap arguments for ``run.sh start``.

   If provided, it should be parsed as command
   line arguments (c.f. :func:`shlex.split`).

   :default: ``''``
   :environ: :data:`FREENET_ARGS`

   .. note::

      The command will be run as :data:`~darc.const.DARC_USER`,
      if current user (c.f. :func:`getpass.getuser`) is *root*.

The following constants are defined for internal usage:

.. data:: darc.proxy.freenet._MNG_FREENET
   :type: bool

   If manage Freenet proxy through :mod:`darc`.

   :default: :data:`True`
   :environ: :data:`DARC_FREENET`

.. data:: darc.proxy.freenet._FREENET_BS_FLAG
   :type: bool

   If the Freenet proxy is bootstrapped.

.. data:: darc.proxy.freenet._FREENET_PROC
   :type: subprocess.Popen

   Freenet proxy process running in the background.

.. data:: darc.proxy.freenet._FREENET_ARGS
   :type: List[str]

   Freenet proxy bootstrap arguments.
