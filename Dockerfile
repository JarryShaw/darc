FROM python:3.7

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
 && pip install --upgrade \
        pip \
        setuptools \
        wheel \
 && pip install \
        requests[socks] \
        beautifulsoup4[html5lib] \
        selenium

WORKDIR /darc
ENTRYPOINT [ "python", "darc.py" ]
CMD [ "--help" ]
COPY darc.py /darc/darc.py
