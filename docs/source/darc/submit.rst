.. automodule:: darc.submit
   :members:
   :undoc-members:
   :show-inheritance:

.. data:: darc.submit.PATH_API
   :value: '{PATH_DB}/api/'

   Path to the API submittsion records, i.e. ``api`` folder under the
   root of data storage.

   .. seealso::

      * :data:`darc.const.PATH_DB`

.. data:: darc.submit.API_RETRY
   :type: int

   Retry times for API submission when failure.

   :default: ``3``
   :environ: :data:`API_RETRY`

.. data:: darc.submit.API_NEW_HOST
   :type: str

   API URL for :func:`~darc.submit.submit_new_host`.

   :default: :data:`None`
   :environ: :data:`API_NEW_HOST`

.. data:: darc.submit.API_REQUESTS
   :type: str

   API URL for :func:`~darc.submit.submit_requests`.

   :default: :data:`None`
   :environ: :data:`API_REQUESTS`

.. data:: darc.submit.API_SELENIUM
   :type: str

   API URL for :func:`~darc.submit.submit_selenium`.

   :default: :data:`None`
   :environ: :data:`API_SELENIUM`

.. note::

   If :data:`~darc.submit.API_NEW_HOST`, :data:`~darc.submit.API_REQUESTS`
   and :data:`~darc.submit.API_SELENIUM` is :data:`None`, the corresponding
   submit function will save the JSON data in the path
   specified by :data:`~darc.submit.PATH_API`.

.. seealso::

   The :mod:`darc` provides a demo on how to implement a :mod:`darc`-compliant
   web backend for the data submission module. See the :doc:`demo </demo>` page
   for more information.
