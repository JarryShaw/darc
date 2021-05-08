Auxiliary Scripts
=================

Since the :mod:`darc` project can be deployed through :doc:`docker`,
we provided some auxiliary scripts to help with the deployment.

Health Check
------------

:File location:
   * Entry point: ``extra/healthcheck.py``
   * System V service: ``extra/healthcheck.service``

.. code-block:: text

   usage: healthcheck [-h] [-f FILE] [-i INTERVAL] ...

   health check running container

   positional arguments:
     services              name of services

   optional arguments:
     -h, --help            show this help message and exit
     -f FILE, --file FILE  path to compose file
     -i INTERVAL, --interval INTERVAL
                           interval (in seconds) of health check

This script will watch the running status of containers managed by Docker
Compose. If the containers are stopped or of *unhealthy* status, it will
bring the containers back alive.

Also, as the internal program may halt unexpectedly whilst the container
remains *healthy*, the script will watch if the program is still active
through its output messages. If inactive, the script will restart the
containers.

Upload API Submission Files
---------------------------

:File location:
   * Entry point: ``extra/upload.py``
   * Helper script: ``extra/upload.sh``
   * Cron sample: ``extra/upload.cron``

.. code-block:: text

   usage: upload [-h] [-p PATH] -H HOST [-U USER]

   upload API submission files

   optional arguments:
     -h, --help            show this help message and exit
     -p PATH, --path PATH  path to data storage
     -H HOST, --host HOST  upstream hostname
     -U USER, --user USER  upstream user credential

This script will automatically upload API submission files, c.f.
:mod:`darc.submit`, using :manpage:`curl(1)`. The ``--user`` option is
supplied for the same option of :manpage:`curl(1)`.

.. important::

   As the :func:`darc.submit.save_submit` is categorising saved API
   submission files by its actual date, the script is also uploading
   such files by the saved dates. Therefore, as the :manpage:`cron(8)`
   sample suggests, the script should better be run everyday *slightly
   after* **12:00 AM** (*0:00* in 24-hour format).

Remove Repeated Lines
---------------------

:File location: ``extra/uniq.py``

This script works the same as :manpage:`uniq(1)`, except it filters one input
line at a time without putting pressure onto memory utilisation.

Redis Clinic
------------

:File location:
   * Entry point: ``extra/clinic.py``
   * Helper script: ``extra/clinic.lua``
   * Cron sample: ``extra/clinic.cron``

.. code-block:: text

   usage: clinic [-h] -r REDIS [-f FILE] [-t TIMEOUT] ...

   memory clinic for Redis

   positional arguments:
     services              name of services

   optional arguments:
     -h, --help            show this help message and exit
     -r REDIS, --redis REDIS
                           URI to the Redis server
     -f FILE, --file FILE  path to compose file
     -t TIMEOUT, --timeout TIMEOUT
                           shutdown timeout in seconds

Since Redis may take more and more memory as the growth of crawled
data and task queues, this script will truncate the Redis task queues
(``queue_requests`` & ``queue_selenium``), as well as the corresponding
:mod:`pickle` caches of :class:`darc.link.Link`.

.. note::

   We used Lua scrpit to slightly accelerate the whole procedure, as
   it may bring burden to the host server if running through Redis
   client.

.. warning::

   Due to restriction on the Alibaba Cloud (Aliyun) customised version
   of Redis, i.e. AsparaDB for Redis, this Lua script is not allowed be
   to executed. It is recommended to manually cleanup the database
   before we find out an alternative solution.
