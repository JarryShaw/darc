
Auxiliary Scripts
=================

Since the :mod:`darc` project can be deployed through :doc:`docker`,
we provided some auxiliary scripts to help with the deployment.

Health Check
------------

:File location: ``extra/healthcheck.py``

.. code:: text

   usage: healthcheck [-h] [-f FILE] [-i INTERVAL]

   health check running container

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

.. code:: text

   usage: upload [-h] [-f FILE] [-p PATH] [-i INTERVAL] -H HOST [-U USER]

   upload API submission files

   optional arguments:
     -h, --help            show this help message and exit
     -f FILE, --file FILE  path to compose file
     -p PATH, --path PATH  path to data storage
     -i INTERVAL, --interval INTERVAL
                           interval (in seconds) to upload
     -H HOST, --host HOST  upstream hostname
     -U USER, --user USER  upstream user credential

This script will automatically upload API submission files, c.f.
:mod:`darc.submit`, using :manpage:`curl(1)`. The ``--user`` option is
supplied for the same option of :manpage:`curl(1)`.

When uploading, the script will *pause* the running containers and it will
*unpause* them upon completion.

Remove Repeated Lines
---------------------

:File location: ``extra/uniq.py``

This script works the same as :manpage:`uniq(1)`, except it filters one input
line at a time without putting pressure onto memory utilisation.
