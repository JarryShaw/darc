# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
#FROM python:3.9-alpine
#FROM python:3.9

# If you prefer miniconda:
#FROM continuumio/miniconda3

FROM ubuntu:focal

LABEL org.opencontainers.image.title="darc" \
      org.opencontainers.image.description="Darkweb Crawler Project" \
      org.opencontainers.image.url="https://darc.jarryshaw.me/" \
      org.opencontainers.image.source="https://github.com/JarryShaw/darc" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses='BSD 3-Clause "New" or "Revised" License'
#EXPOSE 9050

STOPSIGNAL SIGINT
HEALTHCHECK --interval=1h --timeout=1m \
    CMD wget https://httpbin.org/get -O /dev/null || exit 1

ARG DARC_USER="darc"
ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONIOENCODING="UTF-8" \
    DEBIAN_FRONTEND="teletype" \
    DARC_USER="${DARC_USER}"
    # DEBIAN_FRONTEND="noninteractive"

# RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
#  && apk add --update --no-cache \
#         chromium \
#         chromium-chromedriver \
#         tor
# COPY extra/torrc.alpine /etc/tor/torrc

COPY extra/retry.sh /usr/local/bin/retry
COPY extra/install.py /usr/local/bin/pty-install
# see https://www.oracle.com/cn/java/technologies/javase-downloads.html for archive downloads
COPY vendor/jdk-11.0.17_linux-x64_bin.tar.gz /var/cache/oracle-jdk11-installer-local/

RUN set -x \
 && retry apt-get update \
 && retry apt-get install --yes \
        apt-utils \
 && retry apt-get install --yes \
        apt-transport-https \
        ca-certificates
COPY extra/sources.focal.list /etc/apt/sources.list
RUN set -x \
 && retry apt-get update \
 && retry apt-get install --yes \
        gcc \
        g++ \
        libmagic1 \
        make \
        software-properties-common \
        tar \
        unzip \
        zlib1g-dev \
 && retry add-apt-repository ppa:deadsnakes/ppa --yes \
 && retry add-apt-repository ppa:linuxuprising/java --yes \
 && retry add-apt-repository ppa:i2p-maintainers/i2p --yes
RUN retry apt-get update \
 && retry apt-get install --yes \
        python3.9-dev \
        python3-pip \
        python3-setuptools \
        python3-wheel \
 && ln -sf /usr/bin/python3.9 /usr/local/bin/python3
RUN retry pty-install --stdin '6\n70' apt-get install --yes --no-install-recommends \
        tzdata \
 && retry pty-install --stdin 'yes' apt-get install --yes \
        oracle-java11-installer-local
# see https://launchpad.net/~linuxuprising/+archive/ubuntu/java/+packages for available versions
RUN retry apt-get install --yes \
        sudo \
 && adduser --disabled-password --gecos '' ${DARC_USER} \
 && adduser ${DARC_USER} sudo \
 && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

## Tor
RUN retry apt-get install --yes tor
COPY extra/torrc.focal /etc/tor/torrc

## I2P
RUN retry apt-get install --yes i2p
COPY extra/i2p.focal /etc/defaults/i2p

## ZeroNet
COPY vendor/ZeroNet-linux-dist-linux64.tar.gz /tmp
RUN set -x \
 && cd /tmp \
 && tar xvpfz ZeroNet-linux-dist-linux64.tar.gz \
 && mv ZeroNet-linux-dist-linux64 /usr/local/src/zeronet
COPY extra/zeronet.focal.conf /usr/local/src/zeronet/zeronet.conf

## FreeNet
USER darc
COPY vendor/new_installer_offline.jar /tmp
RUN set -x \
 && cd /tmp \
 && ( pty-install --stdin '/home/darc/freenet\n1' java -jar new_installer_offline.jar || true ) \
 && sudo mv /home/darc/freenet /usr/local/src/freenet
USER root

## NoIP
COPY vendor/noip-duc-linux.tar.gz /tmp
RUN set -x \
 && cd /tmp \
 && tar xf noip-duc-linux.tar.gz \
 && mv noip-2.1.9-1 /usr/local/src/noip \
 && cd /usr/local/src/noip \
 && make
 # && make install

# # set up timezone
# RUN echo 'Asia/Shanghai' > /etc/timezone \
#  && rm -f /etc/localtime \
#  && ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
#  && dpkg-reconfigure -f noninteractive tzdata

# ADD tbb/tor-browser-linux64-8.5.5_en-US.tar.gz /
# ADD driver/geckodriver-v0.26.0-linux64.tar.gz /usr/local/bin
COPY vendor/chromedriver_linux64.zip \
     vendor/google-chrome-stable_current_amd64.deb /tmp/
RUN set -x \
 ## ChromeDriver
 && unzip -d /usr/bin /tmp/chromedriver_linux64.zip \
 && which chromedriver \
 ## Google Chrome
 && (dpkg --install /tmp/google-chrome-stable_current_amd64.deb || true) \
 && retry apt-get install --fix-broken --yes \
 && dpkg --install /tmp/google-chrome-stable_current_amd64.deb \
 && which google-chrome

# Using pip:
COPY requirements.debug.txt /tmp
RUN set -x \
 && python3 -m pip install -r /tmp/requirements.debug.txt --cache-dir /app/cache \
 && python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
 && python3 -m pip install ipython
#CMD ["python3", "-m", "darc"]

ENTRYPOINT [ "python3", "-m", "darc" ]
#ENTRYPOINT [ "bash", "/app/extra/run.sh" ]
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
RUN python3 -m pip install -e .
