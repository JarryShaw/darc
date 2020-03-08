.. automodule:: darc.proxy.zeronet
   :members:
   :undoc-members:
   :show-inheritance:

The following constants are configuration through environment variables:

.. data:: darc.proxy.zeronet.ZERONET_PORT
   :type: int

   Port for ZeroNet proxy connection.

   :default: ``43110``
   :environ: :data:`ZERONET_PORT`

.. data:: darc.proxy.zeronet.ZERONET_RETRY
   :type: int

   Retry times for ZeroNet bootstrap when failure.

   :default: ``3``
   :environ: :data:`ZERONET_RETRY`

.. data:: darc.proxy.zeronet.BS_WAIT
   :type: float

   Time after which the attempt to start ZeroNet is aborted.

   :default: ``90``
   :environ: :data:`ZERONET_WAIT`

   .. note::

      If not provided, there will be **NO** timeouts.

.. data:: darc.proxy.zeronet.ZERONET_PATH
   :type: str

   Path to the ZeroNet project.

   :default: ``/usr/local/src/zeronet``
   :environ: :data:`ZERONET_PATH`

.. data:: darc.proxy.zeronet.ZERONET_ARGS
   :type: List[str]

   ZeroNet bootstrap arguments for ``run.sh start``.

   If provided, it should be parsed as command
   line arguments (c.f. |split|_).

   :default: ``''``
   :environ: :data:`ZERONET_ARGS`

   .. note::

      The command will be run as :data:`~darc.const.DARC_USER`,
      if current user (c.f. |getuser|_) is *root*.

.. |split| replace:: ``shlex.split``
.. _split: https://docs.python.org/3/library/shlex.html#shlex.split

.. |getuser| replace:: :func:`getpass.getuser`
.. _getuser: https://docs.python.org/3/library/getpass.html#getpass.getuser

The following constants are defined for internal usage:

.. data:: darc.proxy.zeronet._ZERONET_BS_FLAG
   :type: bool

   If the ZeroNet proxy is bootstrapped.

.. data:: darc.proxy.zeronet._ZERONET_PROC
   :type: subprocess.Popen

   ZeroNet proxy process running in the background.

.. data:: darc.proxy.zeronet._ZERONET_ARGS
   :type: List[str]

   ZeroNet proxy bootstrap arguments.
