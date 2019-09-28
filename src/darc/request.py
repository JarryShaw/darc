# -*- coding: utf-8 -*-

import requests

import darc.typings as typing
from darc.const import SOCKS_PORT


# def get_tor_session() -> typing.Session:
#     session = requests.session()
#     session.proxies = {'http':  f'socks5://127.0.0.1:{SOCKS_PORT}',
#                        'https': f'socks5://127.0.0.1:{SOCKS_PORT}'}
#     return session


def request(link: str) -> typing.Response:
    """Request a link."""
    return requests.get(link, proxies={'http':  f'socks5://127.0.0.1:{SOCKS_PORT}',
                                       'https': f'socks5://127.0.0.1:{SOCKS_PORT}'})
