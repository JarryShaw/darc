# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
#FROM python:alpine
FROM python:3.7

# If you prefer miniconda:
#FROM continuumio/miniconda3

LABEL Name=darc Version=0.0.1
EXPOSE 9065

RUN apt-get update \
 && apt-get install --yes --no-install-recommends \
        apt-transport-https
COPY extra/sources.list /etc/apt/sources.list
RUN apt-get update \
 && apt-get install --yes --no-install-recommends \
        tor
COPY extra/torrc /etc/tor/torrc

#  && service tor restart

WORKDIR /app
ADD . /app

# Using pip:
RUN python3 -m pip install -r requirements.txt --cache-dir /app/cache
#CMD ["python3", "-m", "darc"]

ENTRYPOINT [ "python", "darc.py" ]
CMD [ "--help" ]

# Using pipenv:
#RUN python3 -m pip install pipenv
#RUN pipenv install --ignore-pipfile
#CMD ["pipenv", "run", "python3", "-m", "darc"]

# Using miniconda (make sure to replace 'myenv' w/ your environment name):
#RUN conda env create -f environment.yml
#CMD /bin/bash -c "source activate myenv && python3 -m darc"
