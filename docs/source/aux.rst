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
