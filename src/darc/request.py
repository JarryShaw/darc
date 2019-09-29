# -*- coding: utf-8 -*-

import requests

import darc.typings as typing
from darc.const import SOCKS_PORT


# def get_tor_session() -> typing.Session:
#     session = requests.session()
#     session.proxies = {'http':  f'socks5://127.0.0.1:{SOCKS_PORT}',
#                        'https': f'socks5://127.0.0.1:{SOCKS_PORT}'}
#     return session


def get_nromal(link: str) -> typing.Response:
    """Request a normal link."""
    return requests.get(link)


def get_tor(link: str) -> typing.Response:
    """Request a Tor (.onion) link."""
    return requests.get(link, proxies={'http':  f'socks5://127.0.0.1:{SOCKS_PORT}',
                                       'https': f'socks5://127.0.0.1:{SOCKS_PORT}'})
