FROM python:3.14-bookworm

LABEL org.opencontainers.image.title="darc" \
      org.opencontainers.image.description="Darkweb Crawler Project" \
      org.opencontainers.image.url="https://darc.jarryshaw.me/" \
      org.opencontainers.image.source="https://github.com/JarryShaw/darc" \
      org.opencontainers.image.version="1.0.4" \
      org.opencontainers.image.licenses='BSD 3-Clause "New" or "Revised" License'

STOPSIGNAL SIGINT
HEALTHCHECK --interval=1h --timeout=1m \
    CMD wget -q https://httpbin.org/get -O /dev/null || exit 1

ARG DARC_USER="darc"
ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONIOENCODING="UTF-8" \
    DEBIAN_FRONTEND="noninteractive" \
    DARC_USER="${DARC_USER}"

COPY extra/retry.sh /usr/local/bin/retry
COPY extra/install.py /usr/local/bin/pty-install

RUN set -eux; \
    apt-get update; \
    apt-get install --yes --no-install-recommends \
        build-essential \
        ca-certificates \
        chromium \
        chromium-driver \
        curl \
        default-jre-headless \
        gnupg \
        libmagic1 \
        lsb-release \
        sudo \
        tar \
        tor \
        unzip \
        wget \
        zlib1g-dev; \
    curl --fail --location --silent --show-error \
        https://i2p.net/i2p-archive-keyring.gpg \
        --output /usr/share/keyrings/i2p-archive-keyring.gpg; \
    test "$(gpg --show-keys --with-colons /usr/share/keyrings/i2p-archive-keyring.gpg \
        | awk -F: '$1 == "fpr" { print $10; exit }')" = \
        "7840E7610F28B904753549D767ECE5605BCF1346"; \
    echo "deb [signed-by=/usr/share/keyrings/i2p-archive-keyring.gpg] https://deb.i2p.net/ bookworm main" \
        > /etc/apt/sources.list.d/i2p.list; \
    apt-get update; \
    apt-get install --yes --no-install-recommends i2p i2p-keyring; \
    ln -s /usr/bin/chromium /usr/local/bin/google-chrome; \
    adduser --disabled-password --gecos '' "${DARC_USER}"; \
    adduser "${DARC_USER}" sudo; \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

COPY extra/torrc.focal /etc/tor/torrc
COPY extra/i2p.focal /etc/default/i2p

COPY vendor/ZeroNet-linux-dist-linux64.tar.gz /tmp/
RUN set -eux; \
    tar xzf /tmp/ZeroNet-linux-dist-linux64.tar.gz -C /tmp; \
    mv /tmp/ZeroNet-linux-dist-linux64 /usr/local/src/zeronet
COPY extra/zeronet.focal.conf /usr/local/src/zeronet/zeronet.conf

COPY vendor/new_installer_offline.jar /tmp/
USER darc
RUN set -eux; \
    (pty-install --stdin '/home/darc/freenet\n1' java -jar /tmp/new_installer_offline.jar || true); \
    sudo mv /home/darc/freenet /usr/local/src/freenet
USER root

COPY vendor/noip-duc-linux.tar.gz /tmp/
RUN set -eux; \
    tar xzf /tmp/noip-duc-linux.tar.gz -C /tmp; \
    mv /tmp/noip-2.1.9-1 /usr/local/src/noip; \
    make -C /usr/local/src/noip

COPY requirements.txt /tmp/requirements.txt
RUN set -eux; \
    python -m pip install --upgrade pip setuptools wheel; \
    python -m pip install --cache-dir /app/cache -r /tmp/requirements.txt; \
    python -m pip install ipython

WORKDIR /app
ADD . /app
RUN python -m pip install --no-deps -e .

ENTRYPOINT [ "python", "-m", "darc" ]
CMD [ "--help" ]
