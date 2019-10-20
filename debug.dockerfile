# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
FROM python:3.7-alpine
#FROM python:3.7

# If you prefer miniconda:
#FROM continuumio/miniconda3

LABEL Name=darc Version=0.0.1
EXPOSE 9065

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
 && apk add --update --no-cache tor
# RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
# && apk add --update --no-cache \
#        openrc \
#        tor \
#    # Tell openrc its running inside a container, till now that has meant LXC
# && sed -i 's/#rc_sys=""/rc_sys="lxc"/g' /etc/rc.conf \
#    # Tell openrc loopback and net are already there, since docker handles the networking
# && echo 'rc_provide="loopback net"' >> /etc/rc.conf \
#    # no need for loggers
# && sed -i 's/^#\(rc_logger="YES"\)$/\1/' /etc/rc.conf \
#    # can't get ttys unless you run the container in privileged mode
# && sed -i '/tty/d' /etc/inittab \
#    # can't set hostname since docker sets it
# && sed -i 's/hostname $opts/# hostname $opts/g' /etc/init.d/hostname \
#    # can't mount tmpfs since not privileged
# && sed -i 's/mount -t tmpfs/# mount -t tmpfs/g' /lib/rc/sh/init.sh \
#    # can't do cgroups
# && sed -i 's/cgroup_add_service /# cgroup_add_service /g' /lib/rc/sh/openrc-run.sh \
# && rc-update add tor default
COPY extra/torrc.alpine /etc/tor/torrc
#RUN apt-get update \
#&& apt-get install --yes --no-install-recommends \
#       apt-transport-https
#COPY extra/sources.list /etc/apt/sources.list
#RUN apt-get update \
#&& apt-get install --yes --no-install-recommends \
#       tor
#COPY extra/torrc.debian /etc/tor/torrc

WORKDIR /app
ADD . /app
ADD archive/tor-browser-linux64-8.5.5_en-US.tar.gz /tbb
COPY driver/geckodriver-v0.26.0-linux64 /usr/local/bin

# Using pip:
RUN python3 -m pip install -r requirements.debug.txt --cache-dir /app/cache \
 && python3 -m pip install ipython
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
