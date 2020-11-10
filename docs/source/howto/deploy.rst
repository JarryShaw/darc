How to gracefully deploy ``darc``?
==================================

.. important::

   It is **NOT** necessary to work at the ``darc`` repository
   folder directly. You can just use ``darc`` with your
   customised code somewhere as you wish.

   However, for simplicity, all relative paths referred in this
   article is relative to the project root of the ``darc``
   repository.

To deploy ``darc``, there would generally be three basic steps:

1. deploy the ``darc`` Docker image;
2. setup the ``healthcheck`` watchdog service;
3. install the ``upload`` cron job (optional)

To Start With
-------------

Per best practice, the system must have as least **2 GB RAM**
and **2 CPU cores** to handle the ``loader`` worker properly.
And the capacity of the RAM will heavily impact the performance
of the :mod:`selenium` integration as Google Chrome is the
renowned memory monster.

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
`Redis <http://redis.io/>`__; but if you insist, you may use
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
integrated with Docker workflow. So basically, just pull
the image from Docker Hub or GitHub Container Registry:

.. code-block:: shell

   # Docker Hub
   docker pull jsnbzh/darc:latest
   # GitHub Container Registry
   docker pull ghcr.io/jarryshaw/darc:latest

In cases where you would like to use a *debug* image, which
changes the ``apt`` sources to China hosted and IPython and
other auxiliaries installed, you call also pull such image
instead:

.. code-block:: shell

   # Docker Hub
   docker pull jsnbzh/darc:debug
   # GitHub Container Registry
   docker pull ghcr.io/jarryshaw/darc-debug:latest

Then you will need to customise the ``docker-compose.yml``
based on your needs. Default values and descriptive help
messages can be found in the file.

The rest of it is easy as just calling ``docker-compose``
command to manage the deployed containers, thus I shall
not discuss further.

Deploy with Customisations
++++++++++++++++++++++++++

.. important::

   I've made a sample customisation at |demo-deploy|_ folder,
   please check it out before moving forwards.

   .. |demo-deploy| replace:: ``demo/deploy/``
   .. _demo-deploy: https://github.com/jarryshaw/darc/tree/master/demo/deploy

As in the sample customisation, you can simply use the ``Dockerfile``
there as your Docker environment declration. And the entrypoint file
``market/run.py`` has the sites customisations registered and the
CLI bundled.

Setup ``healthcheck`` Daemon Service
------------------------------------

Since ``darc`` can be quite a burden to its host system,
I introduced this healthcheck service as discussed in
:doc:`../aux`.

For a normal **System V** based service system, you can
simply install the ``darc-healthcheck`` service to
``/etc/systemd/system/``:

.. code-block:: shell

   ln -s extra/healthcheck.service /etc/systemd/system/darc-healthcheck.service

then enable it to run at startup:

.. code-block:: shell

   sudo systemctl enable darc-healthcheck.service

And from now on, you can simply manage the ``darc-healthcheck``
service through ``systemctl`` or ``service`` command
as you prefer.

Install ``upload`` Cron Job
---------------------------

In certain cases, you might wish to upload the API submission
JSON files to your FTP server which has much more space than
the deploy server, then you can utilise the ``upload`` cron
job as mentioned in :doc:`../aux`.

Simply type the following command:

.. code-block:: shell

   crontab -e

and add the cron job into the file opened:

.. code--block:: shell

   10 0 * * * ( cd /path/to/darc/ && /path/to/python3 /path/to/darc/extra/upload.py --host ftp://hostname --user username:password ) >> /path/to/darc/logs/cron/darc-upload.log 2>&1

just remember to change the paths, hostname and credential
respectively; and at last, to activate the new cron job:

.. code-block:: shell

   sudo systemctl restart cron.service

Now, ``darc`` API submission JSON files will be uploaded
to the target FTP server everyday at *0:10 am*.

Bonus Tip
---------

There is a ``Makefile`` at the project root. You can play
and try to exploit it. A very useful command is that

.. code-block:: shell

   make reload

when you wish to pull the remote repository and restart
``darc`` gracefully.
