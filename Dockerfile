# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
#FROM python:3.7-alpine
#FROM python:3.7

# If you prefer miniconda:
#FROM continuumio/miniconda3

FROM ubuntu:bionic

LABEL Name=darc Version=0.0.1
EXPOSE 9065

ENV LANG "C.UTF-8" \
    LC_ALL "C.UTF-8" \
    PYTHONIOENCODING "UTF-8"

RUN apt-get update \
 && apt-get install --yes --no-install-recommends \
        apt-transport-https \
        apt-utils \
        ca-certificates
COPY extra/sources.bionic.list /etc/apt/sources.list
RUN apt-get update \
 && apt-get install --yes --no-install-recommends \
        software-properties-common \
 && add-apt-repository ppa:deadsnakes/ppa --yes \
 && apt update \
 && apt-get install --yes --no-install-recommends \
        python3.7 \
        python3-pip \
        tor \
 && ln -sf /usr/bin/python3.7 /usr/bin/python3
COPY extra/torrc.bionic /etc/tor/torrc
RUN rm -rf \
        ## apt repository lists
        /var/lib/apt/lists/* \
        ## Python dependencies
        /tmp/pip \
 && apt-get remove --auto-remove --yes \
        apt-transport-https \
        apt-utils \
        ca-certificates \
        software-properties-common \
 && apt-get autoremove -y \
 && apt-get autoclean \
 && apt-get clean

WORKDIR /app

ADD driver/geckodriver-v0.26.0-linux64.tar.gz /usr/local/bin
ADD tbb/tor-browser-linux64-8.5.5_en-US.tar.gz /
COPY darc.py \
     LICENSE \
     MANIFEST.in \
     README.md \
     setup.cfg \
     setup.py \
     test_darc.py /app/

# Using pip:
RUN python3 -m pip install -r requirements.txt --no-cache-dir
#CMD ["python3", "-m", "darc"]

ENTRYPOINT [ "python3", "darc.py" ]
CMD [ "--help" ]

# Using pipenv:
#RUN python3 -m pip install pipenv
#RUN pipenv install --ignore-pipfile
#CMD ["pipenv", "run", "python3", "-m", "darc"]

# Using miniconda (make sure to replace 'myenv' w/ your environment name):
#RUN conda env create -f environment.yml
#CMD /bin/bash -c "source activate myenv && python3 -m darc"
