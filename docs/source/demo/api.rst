Web Backend Demo
================

This is a demo of API for communication between the
:mod:`darc` crawlers (:mod:`darc.submit`) and web UI.

.. seealso::

   Please refer to :doc:`data schema <schema>` for more
   information about the submission data.

Assuming the web UI is developed using the |Flask|_
microframework.

.. |Flask| replace:: ``Flask``
.. _Flask: https://flask.palletsprojects.com

.. literalinclude:: ../../../demo/api.py
   :language: python
