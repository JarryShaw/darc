Data Models Demo
================

This is a demo of data models for database storage of
the submitted data from the :mod:`darc` crawlers.

Assuming the database is using |peewee|_ as ORM and
`MySQL`_ as backend.

.. |peewee| replace:: ``peewee``
.. _peewee: https://docs.peewee-orm.com/
.. _MySQL: https://mysql.com/

.. important::

   For more updated, battlefield-tested version of the
   data models, please refer to :mod:`darc.model.web`.

.. literalinclude:: ../../../demo/model.py
   :language: python
