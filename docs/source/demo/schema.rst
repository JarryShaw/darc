Submission Data Schema
======================

To better describe the submitted data, :mod:`darc` provides
several `JSON schema <http://json-schema.org/>`__ generated
from |pydantic|_ models.

.. |pydantic| replace:: :mod:`pydantic`
.. _pydantic: https://pydantic-docs.helpmanual.io/

New Host Submission
-------------------

The data submission from :func:`darc.submit.submit_new_host`.

.. literalinclude:: ../../../demo/schema/new_host.schema.json
   :language: json

Requests Submission
-------------------

The data submission from :func:`darc.submit.submit_requests`.

.. literalinclude:: ../../../demo/schema/requests.schema.json
   :language: json

Selenium Submission
-------------------

The data submission from :func:`darc.submit.submit_selenium`.

.. literalinclude:: ../../../demo/schema/selenium.schema.json
   :language: json

Model Definitions
-----------------

.. literalinclude:: ../../../demo/schema.py
   :language: python
