# -*- coding: utf-8 -*-

import bs4

import darc.typings as typing

def extract_links(text: str) -> typing.List[str]:
    soup = bs4.BeautifulSoup(text, 'html5lib')
