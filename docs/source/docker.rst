Docker Integration
==================

The :mod:`darc` project is integrated with Docker and
Compose. Though not published to Docker Hub, you can
still build by yourself.

The Docker image is based on `Ubuntu Bionic`_ (18.04 LTS),
setting up all Python dependencies for the :mod:`darc`
project, installing `Google Chrome`_ (version
79.0.3945.36) and corresponding `ChromeDriver`_, as well as
installing and configuring Tor_, I2P_, ZeroNet_, FreeNet_,
NoIP_ proxies.

.. _Ubuntu Bionic: http://releases.ubuntu.com/18.04.4
.. _Google Chrome: https://www.google.com/chrome
.. _ChromeDriver: https://chromedriver.chromium.org
.. _Tor: https://www.torproject.org
.. _I2P: https://geti2p.net
.. _ZeroNet: https://zeronet.io
.. _Freenet: https://freenetproject.org
.. _NoIP: https://www.noip.com

.. note::

   `NoIP`_ is currently not fully integrated in the
   :mod:`darc` due to misunderstanding in the configuration
   process. Contributions are welcome.

When building the image, there is an *optional* argument
for setting up a *non-root* user, c.f. environment variable
:data:`DARC_USER` and module constant :data:`~darc.const.DARC_USER`.
By default, the username is ``darc``.

.. raw:: html

   <details>
     <summary>Content of <code class="docutils literal notranslate"><span class="pre">Dockerfile</span></code></summary>

.. literalinclude:: ../../Dockerfile
   :language: dockerfile

.. note::

   * ``retry`` is a shell script for retrying the commands until
     success

   .. raw:: html

      <details>
      <summary>Content of <code class="docutils literal notranslate"><span class="pre">retry</span></code></summary>

   .. literalinclude:: ../../extra/retry.sh
      :language: shell

   .. raw:: html

      </details>

   * ``pty-install`` is a Python script simulating user
     input for APT package installation with ``DEBIAN_FRONTEND``
     set as ``Teletype``.

   .. raw:: html

      <details>
      <summary>Content of <code class="docutils literal notranslate"><span class="pre">pty-install</span></code></summary>

   .. literalinclude:: ../../extra/install.py
      :language: shell

   .. raw:: html

      </details>

.. raw:: html

   </details>

As always, you can also use Docker Compose to manage the :mod:`darc`
image. Environment variables can be set as described in the
`configuration <index.html#configuration>`_ section.

.. raw:: html

   <details>
     <summary>Content of <code class="docutils literal notranslate"><span class="pre">docker-compose.yml</span></code></summary>

.. literalinclude:: ../../docker-compose.yml
   :language: yaml

.. raw:: html

   </details>

.. note::

   Should you wish to run :mod:`darc` in reboot mode, i.e. set
   :envvar:`DARC_REBOOT` and/or :data:`~darc.const.REBOOT`
   as ``True``, you may wish to change the entrypoint to

   .. code:: shell

      bash /app/run.sh

   where ``run.sh`` is a shell script wraps around :mod:`darc`
   especially for reboot mode.

   .. raw:: html

      <details>
      <summary>Content of <code class="docutils literal notranslate"><span class="pre">run.sh</span></code></summary>

   .. literalinclude:: ../../extra/run.sh
      :language: shell

   .. raw:: html

      </details>

   In such scenario, you can customise your ``run.sh`` to, for
   instance, archive then upload current data crawled by :mod:`darc`
   to somewhere else and save up some disk space.

   Or you may wish to look into the ``_queue_requests.txt`` and
   ``_queue_selenium.txt`` databases (c.f. :mod:`darc.db`), and make
   some minor adjustments to, perhaps, narrow down the crawling targets.
