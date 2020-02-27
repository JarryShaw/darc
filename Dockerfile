# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
#FROM python:3.8-alpine
#FROM python:3.8

# If you prefer miniconda:
#FROM continuumio/miniconda3

FROM ubuntu:bionic

LABEL Name=darc Version=0.0.1
#EXPOSE 9065

ARG DEBIAN_FRONTEND="teletype"
ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONIOENCODING="UTF-8"

COPY extra/install.py /usr/local/bin/install
RUN set -x \
 && apt-get update \
 && apt-get install --yes --no-install-recommends \
        apt-utils \
 && apt-get install --yes --no-install-recommends \
        apt-transport-https \
        apt-utils \
        ca-certificates \
 && apt-get update \
 && apt-get install --yes --no-install-recommends \
        gcc \
        g++ \
        make \
        software-properties-common \
        tar \
        unzip \
        zlib1g-dev \
 && retry install --stdin '6\n70' apt-get install --yes --no-install-recommends \
        tzdata \
 && add-apt-repository ppa:deadsnakes/ppa --yes \
 && add-apt-repository ppa:linuxuprising/java --yes \
 && add-apt-repository ppa:i2p-maintainers/i2p --yes \
 && apt-get update \
 && apt-get install --yes --no-install-recommends \
        python3.8 \
        python3-pip \
        python3-setuptools \
        python3-wheel \
 && retry install --stdin 'yes' apt-get install --yes \
        oracle-java13-installer \
 && ln -sf /usr/bin/python3.8 /usr/local/bin/python3

## Tor
RUN apt-get install --yes --no-install-recommends tor
COPY extra/torrc.bionic /etc/tor/torrc

## I2P
RUN apt-get install --yes --no-install-recommends i2p
COPY extra/i2p.bionic /etc/defaults/i2p

## ZeroNet
COPY vendor/ZeroNet-py3-linux64.tar.gz /tmp
RUN set -x \
 && cd /tmp \
 && tar xvpfz ZeroNet-py3-linux64.tar.gz \
 && mv ZeroNet-linux-dist-linux64 /usr/local/src/zeronet
COPY extra/zeronet.bionic.conf /usr/local/src/zeronet/zeronet.conf

## FreeNet
COPY vendor/new_installer_offline.jar /tmp
RUN set -x \
 && cd /tmp \
 && java -jar new_installer_offline.jar

## NoIP
COPY vendor/noip-duc-linux.tar.gz /tmp
RUN set -x \
 && cd /tmp \
 && tar xvpfz noip-duc-linux.tar.gz \
 && mv noip-2.1.9-1 /usr/local/src/noip
 # make install

# # set up timezone
# RUN echo 'Asia/Shanghai' > /etc/timezone \
#  && rm -f /etc/localtime \
#  && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
#  && dpkg-reconfigure -f noninteractive tzdata

# ADD driver/geckodriver-v0.26.0-linux64.tar.gz /usr/local/bin
# ADD tbb/tor-browser-linux64-8.5.5_en-US.tar.gz /
COPY driver/chromedriver_linux64-79.0.3945.36.zip \
     browser/google-chrome-stable_current_amd64.deb /tmp/
RUN set -x \
 ## ChromeDriver
 && unzip -d /usr/bin /tmp/chromedriver_linux64-79.0.3945.36.zip \
 && which chromedriver \
 ## Google Chrome
 && (dpkg --install /tmp/google-chrome-stable_current_amd64.deb || true) \
 && apt-get install --fix-broken --yes --no-install-recommends \
 && dpkg --install /tmp/google-chrome-stable_current_amd64.deb \
 && which google-chrome

# Using pip:
COPY requirements.txt /tmp
RUN python3 -m pip install -r /tmp/requirements.txt --no-cache-dir
#CMD ["python3", "-m", "darc"]

RUN set -x \
 && rm -rf \
        ## APT repository lists
        /var/lib/apt/lists/* \
        ## Python dependencies
        /tmp/requirements.txt \
        /tmp/pip \
        ## ChromeDriver
        /tmp/chromedriver_linux64-79.0.3945.36.zip \
        ## Google Chrome
        /tmp/google-chrome-stable_current_amd64.deb \
        ## Vendors
        /tmp/new_installer_offline.jar \
        /tmp/noip-duc-linux.tar.gz \
        /tmp/ZeroNet-py3-linux64.tar.gz \
 #&& apt-get remove --auto-remove --yes \
 #       software-properties-common \
 #       unzip \
 && apt-get autoremove -y \
 && apt-get autoclean \
 && apt-get clean

#ENTRYPOINT [ "python3", "darc.py" ]
ENTRYPOINT [ "bash", "run.sh" ]
CMD [ "--help" ]

# Using pipenv:
#RUN python3 -m pip install pipenv
#RUN pipenv install --ignore-pipfile
#CMD ["pipenv", "run", "python3", "-m", "darc"]

# Using miniconda (make sure to replace 'myenv' w/ your environment name):
#RUN conda env create -f environment.yml
#CMD /bin/bash -c "source activate myenv && python3 -m darc"

WORKDIR /app
COPY darc/ /app/darc/
COPY LICENSE \
     MANIFEST.in \
     README.md \
     run.sh \
     setup.cfg \
     setup.py \
     test_darc.py /app/
RUN python3 -m pip install -e .
