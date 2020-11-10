# Demo for Customised Deployment

In this folder, we have made a sample customisation on `darc`
to demonstrate the deployment of such customisation.

The `Dockerfile` would be the modified environment for the
deployment and `docker-compose.yml` is the bundled service
management integration to Docker Compose.

The customised source code are hosted at the `market` folder,
whose docstring would be good enough to explain itself. Only
to mention that

* `run.py` is the entrypoint with sites customisation hooks
  registered and `darc` CLI bundled
* `market.py` is the abstract base sites customisation class
  for the customised module
* `dummy.py` is just a dummy example for a concret implementation
  of the sites customisation
