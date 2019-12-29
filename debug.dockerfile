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
#EXPOSE 9050

ENV LANG-"C.UTF-8" \
    LC_ALL-"C.UTF-8" \
    PYTHONIOENCODING-"UTF-8"

# RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
#  && apk add --update --no-cache \
#         chromium \
#         chromium-chromedriver \
#         tor
# COPY extra/torrc.alpine /etc/tor/torrc
RUN set -x \
 && apt-get update \
 && apt-get install --yes \
        apt-transport-https \
        apt-utils \
        ca-certificates
COPY extra/sources.bionic.list /etc/apt/sources.list
RUN set -x \
 && apt-get update \
 && apt-get install --yes \
        unzip \
        software-properties-common \
 && add-apt-repository ppa:deadsnakes/ppa --yes \
 && apt-get update \
 && apt-get install --yes \
        python3.7 \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        tor \
 && ln -sf /usr/bin/python3.7 /usr/bin/python3
COPY extra/torrc.bionic /etc/tor/torrc

# ADD tbb/tor-browser-linux64-8.5.5_en-US.tar.gz /
# ADD driver/geckodriver-v0.26.0-linux64.tar.gz /usr/local/bin
COPY driver/chromedriver_linux64-79.0.3945.36.zip \
     browser/google-chrome-stable_current_amd64.deb /tmp/
RUN set -x \
 ## ChromeDriver
 && unzip -d /usr/bin /tmp/chromedriver_linux64-79.0.3945.36.zip \
 && which chromedriver \
 ## Google Chrome
 && (dpkg --install /tmp/google-chrome-stable_current_amd64.deb || true) \
 && apt-get install --fix-broken --yes \
 && dpkg --install /tmp/google-chrome-stable_current_amd64.deb \
 && which google-chrome

# Using pip:
COPY requirements.debug.txt /tmp
RUN set -x \
 && python3 -m pip install -r /tmp/requirements.debug.txt --cache-dir /app/cache \
 && python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
 && python3 -m pip install ipython
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

WORKDIR /app
ADD . /app
