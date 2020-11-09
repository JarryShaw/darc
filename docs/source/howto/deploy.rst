How to gracefully deploy ``darc``?
==================================

To deploy ``darc``, there would generally be three basic steps:

1. deploy the ``darc`` Docker image;
2. setup the ``healthcheck`` watchdog service;
3. install the ``upload`` cron job (optional)

To Start With
-------------

.. note::

   Imma assume that you're using \*NIX systems, as I don't
   believe a Windows user is gonna see this ;)

Firstly, you will need to clone the repository to your system:

.. code-block::

   git clone https://github.com/JarryShaw/darc.git
   # change your working directory
   cd darc

then set up the folders you need for the log files:

.. code-block::

   mkdir -p logs
   mkdir -p logs/cron

And now, you will need to decide where you would like to store
the data (documents crawled and saved by ``darc``); let's assume
that you have a ``/data`` disk mounted on the system -- since that's
what I have on mine xD -- which would be big enough to use as a
safe seperated storage place from the system so that ``darc`` will
not crash your system by exhausting the storage,

.. code-block::

   mkdir /data/darc
   # and make a shortcut
   ln -s /data/darc data

therefore, you're gonna save your data in ``/data/darc`` folder.

Software Dependency
-------------------

After setting local systems, there're some software dependencies
you shall install:

1. `Docker <https://www.docker.com>`__

``darc`` is exclusively deployed through Docker environment, even
though it can also be deployed directly on a host machine, either
Linux or macOS, and perhaps Windows but I had never tested.

2. Database

``darc`` needs database backend for the task queue management and
other stuffs. It is highly recommended to deploy ``darc`` with
**`Redis <http://redis.io/>`__**; but if you insist, you may use
relationship database (e.g. `MySQL`_, `SQLite`_, `PostgreSQL`_,
etc.) instead.

.. important::

   In this article, I will not discuss about the usage of relationship
   database as they're just too miserable for ``darc`` in terms of
   availability anyway.

.. _MySQL: https://mysql.com/
.. _SQLite: https://www.sqlite.org/
.. _PostgreSQL: https://www.postgresql.org/

As per best practice, *4 GB RAM* would be minimal requirement
for the Redis database. It would be suggested to use directly a
cloud provider hosted Redis database instead of running it on
the same server as ``darc``.

Deploy ``darc`` Docker Image
----------------------------

As discussed in :doc:`../docker`, ``darc`` is exclusively
integrated with Docker workflow.
